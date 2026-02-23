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
from datetime import datetime, timezone, date
import asyncio
import resend

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Resend setup
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

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

class LoginResponse(BaseModel):
    email: str
    name: str
    role: str
    employee_id: str

class EmployeeCreate(BaseModel):
    name: str
    email: EmailStr
    joining_date: str  # YYYY-MM-DD format
    role: str  # "hr" or "employee"
    carry_forward_el: float = 0.0

class Employee(BaseModel):
    model_config = ConfigDict(extra="ignore")
    employee_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    joining_date: str
    role: str
    carry_forward_el: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

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

class CalendarEvent(BaseModel):
    date: str
    employee_name: str
    leave_type: str
    leave_id: Optional[str] = None
    is_holiday: bool = False
    holiday_name: Optional[str] = None

# ==================== HELPER FUNCTIONS ====================

def calculate_eligible_leaves(joining_date_str: str, year: int, carry_forward_el: float = 0.0):
    """Calculate eligible leaves based on joining date"""
    joining_date = datetime.strptime(joining_date_str, "%Y-%m-%d").date()
    
    # If joined in current year
    if joining_date.year == year:
        months_worked = 13 - joining_date.month  # Including joining month
    elif joining_date.year < year:
        months_worked = 12
    else:
        months_worked = 0
    
    el_eligible = round(1.5 * months_worked, 1)
    cl_eligible = round(0.5 * months_worked, 1)
    wfh_eligible = 1 * months_worked
    
    # Add carry forward to EL
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
        # Monday=0, Sunday=6
        if current.weekday() < 5:  # Monday to Friday
            days += 1
        current = date.fromordinal(current.toordinal() + 1)
    
    return days

async def calculate_leave_balance(employee_id: str, year: int = None):
    """Calculate current leave balance for an employee"""
    if year is None:
        year = datetime.now(timezone.utc).year
    
    # Get employee
    employee = await db.employees.find_one({"employee_id": employee_id}, {"_id": 0})
    if not employee:
        return None
    
    # Calculate eligible leaves
    eligible = calculate_eligible_leaves(
        employee["joining_date"], 
        year, 
        employee.get("carry_forward_el", 0.0)
    )
    
    # Get all approved leaves for this year
    leaves = await db.leaves.find({
        "employee_id": employee_id,
        "status": "approved"
    }, {"_id": 0}).to_list(1000)
    
    # Filter leaves for current year
    year_leaves = [l for l in leaves if l["start_date"].startswith(str(year))]
    
    # Calculate used leaves
    ooo_used = sum(l["days"] for l in year_leaves if l["leave_type"] == "ooo")
    wfh_used = sum(l["days"] for l in year_leaves if l["leave_type"] == "wfh")
    
    # For OOO, deduct from CL first, then EL
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

async def send_email_notification(employee_name: str, leave_type: str, start_date: str, end_date: str, days: float):
    """Send email notification to HR"""
    if not RESEND_API_KEY:
        logger.warning("Resend API key not configured, skipping email notification")
        return
    
    # Get all HR emails
    hr_employees = await db.employees.find({"role": "hr"}, {"_id": 0}).to_list(100)
    hr_emails = [emp["email"] for emp in hr_employees]
    
    if not hr_emails:
        logger.warning("No HR emails found")
        return
    
    leave_type_display = "Out of Office" if leave_type == "ooo" else "Work From Home"
    
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
    
    try:
        for hr_email in hr_emails:
            params = {
                "from": SENDER_EMAIL,
                "to": [hr_email],
                "subject": f"New Leave Request: {employee_name} - {leave_type_display}",
                "html": html_content
            }
            await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Email notification sent to {len(hr_emails)} HR members")
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")

# ==================== API ROUTES ====================

@api_router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login with email"""
    employee = await db.employees.find_one({"email": request.email}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found. Please contact HR.")
    
    return LoginResponse(
        email=employee["email"],
        name=employee["name"],
        role=employee["role"],
        employee_id=employee["employee_id"]
    )

@api_router.post("/employees", response_model=Employee)
async def create_employee(employee: EmployeeCreate):
    """Create a new employee (HR only)"""
    # Check if email already exists
    existing = await db.employees.find_one({"email": employee.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Employee with this email already exists")
    
    employee_obj = Employee(**employee.model_dump())
    doc = employee_obj.model_dump()
    
    await db.employees.insert_one(doc)
    return employee_obj

@api_router.get("/employees", response_model=List[Employee])
async def get_employees():
    """Get all employees"""
    employees = await db.employees.find({}, {"_id": 0}).to_list(1000)
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

@api_router.post("/leaves", response_model=Leave)
async def apply_leave(leave_request: LeaveRequest):
    """Apply for leave"""
    # Get employee
    employee = await db.employees.find_one({"employee_id": leave_request.employee_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Calculate days
    days = count_weekdays(leave_request.start_date, leave_request.end_date)
    
    if days <= 0:
        raise HTTPException(status_code=400, detail="Invalid date range")
    
    # Check balance
    year = datetime.strptime(leave_request.start_date, "%Y-%m-%d").year
    balance = await calculate_leave_balance(leave_request.employee_id, year)
    
    if leave_request.leave_type == "wfh":
        if balance["wfh"]["available"] < days:
            raise HTTPException(status_code=400, detail=f"Insufficient WFH balance. Available: {balance['wfh']['available']} days")
    else:  # ooo
        total_available = balance["casual_leave"]["available"] + balance["earned_leave"]["available"]
        if total_available < days:
            raise HTTPException(status_code=400, detail=f"Insufficient leave balance. Available: {total_available} days")
    
    # Create leave
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
    await send_email_notification(
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
    """Delete/cancel a leave (HR only)"""
    result = await db.leaves.delete_one({"leave_id": leave_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Leave not found")
    return {"message": "Leave deleted successfully"}

@api_router.post("/holidays", response_model=Holiday)
async def create_holiday(holiday: HolidayCreate):
    """Add a holiday (HR only)"""
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
    """Delete a holiday (HR only)"""
    result = await db.holidays.delete_one({"holiday_id": holiday_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Holiday not found")
    return {"message": "Holiday deleted successfully"}

@api_router.get("/calendar")
async def get_calendar(year: int, month: int):
    """Get calendar events for a specific month"""
    # Get leaves for the month
    leaves = await db.leaves.find({
        "status": "approved",
        "start_date": {"$regex": f"^{year}-{month:02d}"}
    }, {"_id": 0}).to_list(1000)
    
    # Get holidays for the year
    holidays = await db.holidays.find({"year": year}, {"_id": 0}).to_list(1000)
    
    events = []
    
    # Add leave events
    for leave in leaves:
        start = datetime.strptime(leave["start_date"], "%Y-%m-%d").date()
        end = datetime.strptime(leave["end_date"], "%Y-%m-%d").date()
        
        current = start
        while current <= end:
            if current.weekday() < 5:  # Only weekdays
                events.append({
                    "date": current.strftime("%Y-%m-%d"),
                    "employee_name": leave["employee_name"],
                    "leave_type": leave["leave_type"],
                    "leave_id": leave["leave_id"],
                    "is_holiday": False
                })
            current = date.fromordinal(current.toordinal() + 1)
    
    # Add holiday events
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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()