from fastapi import FastAPI, APIRouter, HTTPException, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, date, timedelta
import secrets
import string
import bcrypt
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# SendGrid setup
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', '')
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    email: str
    name: str
    role: str
    employee_id: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class EmployeeCreate(BaseModel):
    name: str
    email: EmailStr
    joining_date: str  # YYYY-MM-DD format
    role: str  # "hr" or "employee"
    carry_forward_el: float = 0.0

class EmployeeResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    employee_id: str
    name: str
    email: str
    joining_date: str
    role: str
    carry_forward_el: float = 0.0
    created_at: str

class LeaveBalance(BaseModel):
    employee_id: str
    employee_name: str
    earned_leave: dict
    casual_leave: dict
    wfh: dict

class LeaveRequest(BaseModel):
    employee_id: str
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    leave_type: str  # "ooo" or "wfh"
    reason: Optional[str] = ""

class Leave(BaseModel):
    model_config = ConfigDict(extra="ignore")
    leave_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    employee_name: str
    start_date: str
    end_date: str
    leave_type: str
    reason: str = ""
    days: float
    status: str = "approved"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class HolidayCreate(BaseModel):
    date: str  # YYYY-MM-DD
    name: str
    year: int

class Holiday(BaseModel):
    model_config = ConfigDict(extra="ignore")
    holiday_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: str
    name: str
    year: int

# ==================== PASSWORD UTILITIES ====================

def generate_password(length: int = 12) -> str:
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def generate_reset_token() -> str:
    """Generate a secure reset token"""
    return secrets.token_urlsafe(32)

# ==================== EMAIL UTILITIES ====================

def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send email via SendGrid"""
    if not SENDGRID_API_KEY:
        logger.warning("SendGrid API key not configured, logging email instead")
        logger.info(f"EMAIL TO: {to_email}")
        logger.info(f"SUBJECT: {subject}")
        logger.info(f"CONTENT: {html_content[:200]}...")
        return True
    
    try:
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info(f"Email sent to {to_email}, status: {response.status_code}")
        return response.status_code == 202
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False

def send_welcome_email(to_email: str, name: str, password: str) -> bool:
    """Send welcome email with generated password"""
    subject = "Welcome to TortoiseHR - Your Account Details"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #0f766e; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }}
            .content {{ background-color: #f8fafc; padding: 30px; border-radius: 0 0 8px 8px; }}
            .password-box {{ background-color: #fff; padding: 15px; margin: 20px 0; border: 2px dashed #0f766e; border-radius: 8px; text-align: center; }}
            .password {{ font-size: 24px; font-weight: bold; color: #0f766e; letter-spacing: 2px; }}
            .btn {{ display: inline-block; background-color: #0f766e; color: white; padding: 12px 30px; text-decoration: none; border-radius: 25px; margin-top: 20px; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to TortoiseHR!</h1>
            </div>
            <div class="content">
                <p>Hi <strong>{name}</strong>,</p>
                <p>Your account has been created successfully. Here are your login credentials:</p>
                
                <p><strong>Email:</strong> {to_email}</p>
                
                <div class="password-box">
                    <p style="margin: 0; color: #666;">Your temporary password:</p>
                    <p class="password">{password}</p>
                </div>
                
                <p><strong>Important:</strong> Please change your password after your first login for security.</p>
                
                <center>
                    <a href="{FRONTEND_URL}" class="btn">Login Now</a>
                </center>
                
                <div class="footer">
                    <p>If you didn't request this account, please contact HR immediately.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return send_email(to_email, subject, html_content)

def send_password_reset_email(to_email: str, name: str, reset_token: str) -> bool:
    """Send password reset email with token link"""
    reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"
    subject = "TortoiseHR - Password Reset Request"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #0f766e; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }}
            .content {{ background-color: #f8fafc; padding: 30px; border-radius: 0 0 8px 8px; }}
            .btn {{ display: inline-block; background-color: #0f766e; color: white; padding: 12px 30px; text-decoration: none; border-radius: 25px; margin: 20px 0; }}
            .warning {{ background-color: #fef3c7; padding: 15px; border-radius: 8px; margin-top: 20px; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Password Reset Request</h1>
            </div>
            <div class="content">
                <p>Hi <strong>{name}</strong>,</p>
                <p>We received a request to reset your password. Click the button below to set a new password:</p>
                
                <center>
                    <a href="{reset_link}" class="btn">Reset Password</a>
                </center>
                
                <p>Or copy and paste this link in your browser:</p>
                <p style="word-break: break-all; color: #0f766e;">{reset_link}</p>
                
                <div class="warning">
                    <p style="margin: 0;"><strong>Note:</strong> This link will expire in 1 hour. If you didn't request a password reset, please ignore this email.</p>
                </div>
                
                <div class="footer">
                    <p>This is an automated message from TortoiseHR. Please do not reply.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return send_email(to_email, subject, html_content)

def send_leave_notification_email(hr_emails: List[str], employee_name: str, leave_type: str, start_date: str, end_date: str, days: float) -> bool:
    """Send leave notification to HR"""
    leave_type_display = "Out of Office" if leave_type == "ooo" else "Work From Home"
    subject = f"New Leave Request: {employee_name} - {leave_type_display}"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #0f766e; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
            .content {{ background-color: #f8fafc; padding: 20px; border-radius: 0 0 8px 8px; }}
            .info {{ background-color: white; padding: 15px; margin: 10px 0; border-left: 4px solid #0f766e; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>New Leave Request - TortoiseHR</h2>
            </div>
            <div class="content">
                <p><strong>{employee_name}</strong> has applied for a leave.</p>
                <div class="info">
                    <p><strong>Leave Type:</strong> {leave_type_display}</p>
                    <p><strong>From:</strong> {start_date}</p>
                    <p><strong>To:</strong> {end_date}</p>
                    <p><strong>Duration:</strong> {days} days</p>
                </div>
                <p>The leave has been automatically approved and added to the calendar.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    success = True
    for hr_email in hr_emails:
        if not send_email(hr_email, subject, html_content):
            success = False
    return success

# ==================== HELPER FUNCTIONS ====================

def calculate_eligible_leaves(joining_date_str: str, year: int, carry_forward_el: float = 0.0):
    """Calculate eligible leaves based on joining date"""
    joining_date = datetime.strptime(joining_date_str, "%Y-%m-%d").date()
    
    if joining_date.year == year:
        months_worked = 13 - joining_date.month
    elif joining_date.year < year:
        months_worked = 12
    else:
        months_worked = 0
    
    el_eligible = round(1.5 * months_worked, 1)
    cl_eligible = round(0.5 * months_worked, 1)
    wfh_eligible = 1 * months_worked
    
    el_eligible += carry_forward_el
    
    return {
        "earned_leave": el_eligible,
        "casual_leave": cl_eligible,
        "wfh": wfh_eligible
    }

def count_weekdays(start_date_str: str, end_date_str: str):
    """Count weekdays between two dates (excluding weekends)"""
    start = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    
    days = 0
    current = start
    while current <= end:
        if current.weekday() < 5:
            days += 1
        current = date.fromordinal(current.toordinal() + 1)
    
    return days

async def calculate_leave_balance(employee_id: str, year: int = None):
    """Calculate current leave balance for an employee"""
    if year is None:
        year = datetime.now(timezone.utc).year
    
    employee = await db.employees.find_one({"employee_id": employee_id}, {"_id": 0})
    if not employee:
        return None
    
    eligible = calculate_eligible_leaves(
        employee["joining_date"], 
        year, 
        employee.get("carry_forward_el", 0.0)
    )
    
    leaves = await db.leaves.find({
        "employee_id": employee_id,
        "status": "approved"
    }, {"_id": 0}).to_list(1000)
    
    year_leaves = [l for l in leaves if l["start_date"].startswith(str(year))]
    
    ooo_used = sum(l["days"] for l in year_leaves if l["leave_type"] == "ooo")
    wfh_used = sum(l["days"] for l in year_leaves if l["leave_type"] == "wfh")
    
    cl_used = min(ooo_used, eligible["casual_leave"])
    el_used = max(0, ooo_used - eligible["casual_leave"])
    
    return {
        "employee_id": employee_id,
        "employee_name": employee["name"],
        "earned_leave": {
            "total": eligible["earned_leave"],
            "used": el_used,
            "available": eligible["earned_leave"] - el_used
        },
        "casual_leave": {
            "total": eligible["casual_leave"],
            "used": cl_used,
            "available": eligible["casual_leave"] - cl_used
        },
        "wfh": {
            "total": eligible["wfh"],
            "used": wfh_used,
            "available": eligible["wfh"] - wfh_used
        }
    }

# ==================== AUTH API ROUTES ====================

@api_router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login with email and password"""
    employee = await db.employees.find_one(
        {"email": {"$regex": f"^{request.email}$", "$options": "i"}}, 
        {"_id": 0}
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found. Please contact HR.")
    
    if not employee.get("password_hash"):
        raise HTTPException(status_code=400, detail="Password not set. Please contact HR.")
    
    if not verify_password(request.password, employee["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    return LoginResponse(
        email=employee["email"],
        name=employee["name"],
        role=employee["role"],
        employee_id=employee["employee_id"]
    )

@api_router.post("/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Request password reset email"""
    employee = await db.employees.find_one(
        {"email": {"$regex": f"^{request.email}$", "$options": "i"}}, 
        {"_id": 0}
    )
    
    # Always return success to prevent email enumeration
    if not employee:
        return {"message": "If your email exists in our system, you will receive a password reset link."}
    
    # Generate reset token
    reset_token = generate_reset_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Store reset token
    await db.password_resets.delete_many({"email": employee["email"]})
    await db.password_resets.insert_one({
        "email": employee["email"],
        "token": reset_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Send email
    send_password_reset_email(employee["email"], employee["name"], reset_token)
    
    return {"message": "If your email exists in our system, you will receive a password reset link."}

@api_router.post("/auth/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """Reset password using token"""
    # Find valid token
    reset_record = await db.password_resets.find_one({"token": request.token}, {"_id": 0})
    
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Check expiration
    expires_at = datetime.fromisoformat(reset_record["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        await db.password_resets.delete_one({"token": request.token})
        raise HTTPException(status_code=400, detail="Reset token has expired. Please request a new one.")
    
    # Validate password
    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    # Update password
    password_hash = hash_password(request.new_password)
    await db.employees.update_one(
        {"email": {"$regex": f"^{reset_record['email']}$", "$options": "i"}},
        {"$set": {"password_hash": password_hash}}
    )
    
    # Delete used token
    await db.password_resets.delete_one({"token": request.token})
    
    return {"message": "Password reset successful. You can now login with your new password."}

@api_router.get("/auth/verify-reset-token")
async def verify_reset_token(token: str):
    """Verify if reset token is valid"""
    reset_record = await db.password_resets.find_one({"token": token}, {"_id": 0})
    
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid reset token")
    
    expires_at = datetime.fromisoformat(reset_record["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="Reset token has expired")
    
    return {"valid": True, "email": reset_record["email"]}

# ==================== EMPLOYEE API ROUTES ====================

@api_router.post("/employees", response_model=EmployeeResponse)
async def create_employee(employee: EmployeeCreate):
    """Create a new employee and send welcome email with password"""
    existing = await db.employees.find_one(
        {"email": {"$regex": f"^{employee.email}$", "$options": "i"}}, 
        {"_id": 0}
    )
    if existing:
        raise HTTPException(status_code=400, detail="Employee with this email already exists")
    
    # Generate password
    plain_password = generate_password()
    password_hash = hash_password(plain_password)
    
    # Create employee document
    employee_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    
    employee_doc = {
        "employee_id": employee_id,
        "name": employee.name,
        "email": employee.email,
        "joining_date": employee.joining_date,
        "role": employee.role,
        "carry_forward_el": employee.carry_forward_el,
        "password_hash": password_hash,
        "created_at": created_at
    }
    
    await db.employees.insert_one(employee_doc)
    
    # Send welcome email with password
    send_welcome_email(employee.email, employee.name, plain_password)
    logger.info(f"Created employee {employee.email} and sent welcome email")
    
    return EmployeeResponse(
        employee_id=employee_id,
        name=employee.name,
        email=employee.email,
        joining_date=employee.joining_date,
        role=employee.role,
        carry_forward_el=employee.carry_forward_el,
        created_at=created_at
    )

@api_router.get("/employees", response_model=List[EmployeeResponse])
async def get_employees():
    """Get all employees"""
    employees = await db.employees.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return employees

@api_router.get("/employees/{employee_id}/balance", response_model=LeaveBalance)
async def get_employee_balance(employee_id: str, year: Optional[int] = None):
    """Get leave balance for an employee"""
    if year is None:
        year = datetime.now(timezone.utc).year
    
    balance = await calculate_leave_balance(employee_id, year)
    if not balance:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return balance

@api_router.get("/balances", response_model=List[LeaveBalance])
async def get_all_balances(year: Optional[int] = None):
    """Get leave balances for all employees"""
    if year is None:
        year = datetime.now(timezone.utc).year
    
    employees = await db.employees.find({}, {"_id": 0}).to_list(1000)
    balances = []
    
    for emp in employees:
        balance = await calculate_leave_balance(emp["employee_id"], year)
        if balance:
            balances.append(balance)
    
    return balances

# ==================== LEAVE API ROUTES ====================

@api_router.post("/leaves", response_model=Leave)
async def apply_leave(leave_request: LeaveRequest):
    """Apply for leave"""
    employee = await db.employees.find_one({"employee_id": leave_request.employee_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    days = count_weekdays(leave_request.start_date, leave_request.end_date)
    
    if days <= 0:
        raise HTTPException(status_code=400, detail="Invalid date range")
    
    year = datetime.strptime(leave_request.start_date, "%Y-%m-%d").year
    balance = await calculate_leave_balance(leave_request.employee_id, year)
    
    if leave_request.leave_type == "wfh":
        if balance["wfh"]["available"] < days:
            raise HTTPException(status_code=400, detail=f"Insufficient WFH balance. Available: {balance['wfh']['available']} days")
    else:
        total_available = balance["casual_leave"]["available"] + balance["earned_leave"]["available"]
        if total_available < days:
            raise HTTPException(status_code=400, detail=f"Insufficient leave balance. Available: {total_available} days")
    
    leave = Leave(
        employee_id=leave_request.employee_id,
        employee_name=employee["name"],
        start_date=leave_request.start_date,
        end_date=leave_request.end_date,
        leave_type=leave_request.leave_type,
        reason=leave_request.reason or "",
        days=days
    )
    
    doc = leave.model_dump()
    await db.leaves.insert_one(doc)
    
    # Send email notification to HR
    hr_employees = await db.employees.find({"role": "hr"}, {"_id": 0}).to_list(100)
    hr_emails = [emp["email"] for emp in hr_employees]
    if hr_emails:
        send_leave_notification_email(
            hr_emails,
            employee["name"],
            leave_request.leave_type,
            leave_request.start_date,
            leave_request.end_date,
            days
        )
    
    return leave

@api_router.get("/leaves", response_model=List[Leave])
async def get_leaves(year: Optional[int] = None):
    """Get all leaves"""
    query = {"status": "approved"}
    if year:
        query["start_date"] = {"$regex": f"^{year}"}
    
    leaves = await db.leaves.find(query, {"_id": 0}).to_list(1000)
    return leaves

@api_router.delete("/leaves/{leave_id}")
async def delete_leave(leave_id: str):
    """Delete/cancel a leave"""
    result = await db.leaves.delete_one({"leave_id": leave_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Leave not found")
    return {"message": "Leave deleted successfully"}

# ==================== HOLIDAY API ROUTES ====================

@api_router.post("/holidays", response_model=Holiday)
async def create_holiday(holiday: HolidayCreate):
    """Add a holiday"""
    holiday_obj = Holiday(**holiday.model_dump())
    doc = holiday_obj.model_dump()
    
    await db.holidays.insert_one(doc)
    return holiday_obj

@api_router.get("/holidays", response_model=List[Holiday])
async def get_holidays(year: Optional[int] = None):
    """Get all holidays"""
    query = {}
    if year:
        query["year"] = year
    
    holidays = await db.holidays.find(query, {"_id": 0}).to_list(1000)
    return holidays

@api_router.delete("/holidays/{holiday_id}")
async def delete_holiday(holiday_id: str):
    """Delete a holiday"""
    result = await db.holidays.delete_one({"holiday_id": holiday_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Holiday not found")
    return {"message": "Holiday deleted successfully"}

# ==================== CALENDAR API ROUTES ====================

@api_router.get("/calendar")
async def get_calendar(year: int, month: int):
    """Get calendar events for a specific month"""
    leaves = await db.leaves.find({
        "status": "approved",
        "start_date": {"$regex": f"^{year}-{month:02d}"}
    }, {"_id": 0}).to_list(1000)
    
    holidays = await db.holidays.find({"year": year}, {"_id": 0}).to_list(1000)
    
    events = []
    
    for leave in leaves:
        start = datetime.strptime(leave["start_date"], "%Y-%m-%d").date()
        end = datetime.strptime(leave["end_date"], "%Y-%m-%d").date()
        
        current = start
        while current <= end:
            if current.weekday() < 5:
                events.append({
                    "date": current.strftime("%Y-%m-%d"),
                    "employee_name": leave["employee_name"],
                    "leave_type": leave["leave_type"],
                    "leave_id": leave["leave_id"],
                    "is_holiday": False
                })
            current = date.fromordinal(current.toordinal() + 1)
    
    for holiday in holidays:
        holiday_date = datetime.strptime(holiday["date"], "%Y-%m-%d").date()
        if holiday_date.year == year and holiday_date.month == month:
            events.append({
                "date": holiday["date"],
                "employee_name": "",
                "leave_type": "holiday",
                "is_holiday": True,
                "holiday_name": holiday["name"]
            })
    
    return {"events": events}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def seed_hr_user():
    """Seed the default HR user on startup"""
    hr_email = "ipshita@Tortoise.pro"
    existing = await db.employees.find_one(
        {"email": {"$regex": f"^{hr_email}$", "$options": "i"}}, 
        {"_id": 0}
    )
    
    if not existing:
        # Generate password for HR
        plain_password = "TortoiseHR@2024"  # Default password for HR
        password_hash = hash_password(plain_password)
        
        hr_user = {
            "employee_id": str(uuid.uuid4()),
            "name": "Ipshita",
            "email": hr_email,
            "joining_date": "2024-01-01",
            "role": "hr",
            "carry_forward_el": 0.0,
            "password_hash": password_hash,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.employees.insert_one(hr_user)
        logger.info(f"Seeded default HR user: {hr_email} with password: {plain_password}")
    else:
        # Ensure existing HR user has password
        if not existing.get("password_hash"):
            plain_password = "TortoiseHR@2024"
            password_hash = hash_password(plain_password)
            await db.employees.update_one(
                {"email": {"$regex": f"^{hr_email}$", "$options": "i"}},
                {"$set": {"password_hash": password_hash}}
            )
            logger.info(f"Updated HR user {hr_email} with password")
        else:
            logger.info(f"HR user {hr_email} already exists with password")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
