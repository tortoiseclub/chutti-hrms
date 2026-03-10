"""
Comprehensive Backend API Tests for Attendance Management System
Tests: Authentication, Employees, Leaves, Holidays, Calendar, Leave Balance
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

# Configuration
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://attendance-hub-225.preview.emergentagent.com').rstrip('/')
API_URL = f"{BASE_URL}/api"

# Test data prefixes
TEST_PREFIX = "TEST_"


class TestAuthentication:
    """Authentication endpoint tests (password-based login)"""

    # HR credentials for testing
    HR_EMAIL = "ipshita@Tortoise.pro"
    HR_PASSWORD = "TortoiseHR@2024"

    def test_login_hr_user_success(self):
        """Test HR login with valid email and password"""
        response = requests.post(
            f"{API_URL}/auth/login",
            json={"email": self.HR_EMAIL, "password": self.HR_PASSWORD}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "email" in data
        assert "name" in data
        assert "role" in data
        assert "employee_id" in data
        assert data["role"] == "hr"
        assert data["email"].lower() == "ipshita@tortoise.pro"
        print(f"✓ HR login successful: {data['name']} ({data['role']})")

    def test_login_case_insensitive(self):
        """Test login is case-insensitive for email"""
        response = requests.post(
            f"{API_URL}/auth/login",
            json={"email": "IPSHITA@TORTOISE.PRO", "password": self.HR_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "hr"
        print("✓ Case-insensitive login works")

    def test_login_invalid_email(self):
        """Test login fails with unknown email"""
        response = requests.post(
            f"{API_URL}/auth/login",
            json={"email": "unknown@example.com", "password": "anypassword123"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        print("✓ Invalid email returns 404")

    def test_login_invalid_email_format(self):
        """Test login fails with invalid email format"""
        response = requests.post(
            f"{API_URL}/auth/login",
            json={"email": "not-an-email", "password": "anypassword123"}
        )
        # Should return 422 for validation error
        assert response.status_code == 422
        print("✓ Invalid email format returns validation error")


class TestEmployees:
    """Employee management tests"""

    def test_get_all_employees(self):
        """Test fetching all employees"""
        response = requests.get(f"{API_URL}/employees")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # HR user should exist
        hr_found = any(emp["email"].lower() == "ipshita@tortoise.pro" for emp in data)
        assert hr_found, "HR user ipshita@Tortoise.pro should exist"
        print(f"✓ Retrieved {len(data)} employees")

    def test_create_employee(self):
        """Test creating a new employee"""
        unique_email = f"test.employee.{datetime.now().timestamp()}@tortoise.pro"
        employee_data = {
            "name": f"{TEST_PREFIX}Employee Create Test",
            "email": unique_email,
            "joining_date": "2025-01-01",
            "role": "employee",
            "carry_forward_el": 5.0
        }

        response = requests.post(
            f"{API_URL}/employees",
            json=employee_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == employee_data["name"]
        assert data["email"] == unique_email
        assert data["joining_date"] == "2025-01-01"
        assert data["role"] == "employee"
        assert data["carry_forward_el"] == 5.0
        assert "employee_id" in data
        
        # Verify by GET
        get_response = requests.get(f"{API_URL}/employees")
        employees = get_response.json()
        created_found = any(emp["email"] == unique_email for emp in employees)
        assert created_found, "Created employee should appear in list"
        print(f"✓ Employee created: {data['employee_id']}")
        return data["employee_id"]

    def test_create_duplicate_employee_fails(self):
        """Test creating employee with existing email fails"""
        response = requests.post(
            f"{API_URL}/employees",
            json={
                "name": "Duplicate Test",
                "email": "ipshita@Tortoise.pro",
                "joining_date": "2025-01-01",
                "role": "employee",
                "carry_forward_el": 0.0
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"].lower()
        print("✓ Duplicate email correctly rejected")


class TestLeaveBalance:
    """Leave balance calculation tests"""

    def test_get_hr_leave_balance(self):
        """Test getting leave balance for HR user"""
        # First get HR employee_id
        employees = requests.get(f"{API_URL}/employees").json()
        hr_user = next((emp for emp in employees if emp["email"].lower() == "ipshita@tortoise.pro"), None)
        assert hr_user is not None

        response = requests.get(f"{API_URL}/employees/{hr_user['employee_id']}/balance")
        assert response.status_code == 200
        
        data = response.json()
        assert "employee_id" in data
        assert "employee_name" in data
        assert "earned_leave" in data
        assert "casual_leave" in data
        assert "wfh" in data
        
        # Verify structure
        assert "total" in data["earned_leave"]
        assert "used" in data["earned_leave"]
        assert "available" in data["earned_leave"]
        print(f"✓ Leave balance: EL={data['earned_leave']['available']}, CL={data['casual_leave']['available']}, WFH={data['wfh']['available']}")

    def test_get_all_balances(self):
        """Test getting all employees' leave balances"""
        response = requests.get(f"{API_URL}/balances")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        for balance in data:
            assert "employee_id" in balance
            assert "earned_leave" in balance
            assert "casual_leave" in balance
            assert "wfh" in balance
        print(f"✓ Retrieved balances for {len(data)} employees")

    def test_balance_calculation_for_new_employee(self):
        """Test leave balance calculation for a new employee"""
        # Create employee joining Jan 2025
        unique_email = f"test.balance.{datetime.now().timestamp()}@tortoise.pro"
        employee = {
            "name": f"{TEST_PREFIX}Balance Calc Test",
            "email": unique_email,
            "joining_date": "2025-01-01",  # Jan 2025
            "role": "employee",
            "carry_forward_el": 10.0  # 10 carry forward
        }

        create_response = requests.post(f"{API_URL}/employees", json=employee)
        assert create_response.status_code == 200
        employee_id = create_response.json()["employee_id"]

        # Get balance for 2025
        balance_response = requests.get(f"{API_URL}/employees/{employee_id}/balance?year=2025")
        assert balance_response.status_code == 200
        balance = balance_response.json()

        # Jan 2025 joining: 13 - 1 = 12 months eligible
        # EL: 1.5 * 12 + 10 carry forward = 18 + 10 = 28
        # CL: 0.5 * 12 = 6
        # WFH: 1 * 12 = 12
        assert balance["earned_leave"]["total"] == 28.0, f"Expected EL=28, got {balance['earned_leave']['total']}"
        assert balance["casual_leave"]["total"] == 6.0, f"Expected CL=6, got {balance['casual_leave']['total']}"
        assert balance["wfh"]["total"] == 12, f"Expected WFH=12, got {balance['wfh']['total']}"
        print(f"✓ Balance calculation correct: EL={balance['earned_leave']['total']}, CL={balance['casual_leave']['total']}, WFH={balance['wfh']['total']}")


class TestLeaves:
    """Leave application tests"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test employee for leave tests"""
        # Get HR employee for testing
        employees = requests.get(f"{API_URL}/employees").json()
        self.hr_user = next((emp for emp in employees if emp["email"].lower() == "ipshita@tortoise.pro"), None)
        assert self.hr_user is not None

    def test_apply_ooo_leave(self):
        """Test applying for OOO leave"""
        # Use dates in the future
        start_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")

        leave_request = {
            "employee_id": self.hr_user["employee_id"],
            "start_date": start_date,
            "end_date": end_date,
            "leave_type": "ooo",
            "reason": "Test OOO leave"
        }

        response = requests.post(f"{API_URL}/leaves", json=leave_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["employee_id"] == self.hr_user["employee_id"]
        assert data["leave_type"] == "ooo"
        assert data["status"] == "approved"
        assert "leave_id" in data
        assert "days" in data
        print(f"✓ OOO leave applied: {data['days']} days, leave_id={data['leave_id']}")
        
        # Cleanup - delete the leave
        requests.delete(f"{API_URL}/leaves/{data['leave_id']}")

    def test_apply_wfh_leave(self):
        """Test applying for WFH leave"""
        start_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        end_date = start_date  # Single day

        leave_request = {
            "employee_id": self.hr_user["employee_id"],
            "start_date": start_date,
            "end_date": end_date,
            "leave_type": "wfh",
            "reason": "Test WFH"
        }

        response = requests.post(f"{API_URL}/leaves", json=leave_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["leave_type"] == "wfh"
        assert data["status"] == "approved"
        print(f"✓ WFH leave applied: {data['days']} days")
        
        # Cleanup
        requests.delete(f"{API_URL}/leaves/{data['leave_id']}")

    def test_get_all_leaves(self):
        """Test getting all leaves"""
        response = requests.get(f"{API_URL}/leaves")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Retrieved {len(data)} leaves")

    def test_get_leaves_by_year(self):
        """Test filtering leaves by year"""
        current_year = datetime.now().year
        response = requests.get(f"{API_URL}/leaves?year={current_year}")
        assert response.status_code == 200
        
        data = response.json()
        for leave in data:
            assert leave["start_date"].startswith(str(current_year))
        print(f"✓ Filtered {len(data)} leaves for year {current_year}")

    def test_delete_leave(self):
        """Test deleting a leave"""
        # First create a leave
        start_date = (datetime.now() + timedelta(days=21)).strftime("%Y-%m-%d")
        leave_request = {
            "employee_id": self.hr_user["employee_id"],
            "start_date": start_date,
            "end_date": start_date,
            "leave_type": "wfh",
            "reason": "Test delete"
        }
        
        create_response = requests.post(f"{API_URL}/leaves", json=leave_request)
        assert create_response.status_code == 200
        leave_id = create_response.json()["leave_id"]

        # Delete the leave
        delete_response = requests.delete(f"{API_URL}/leaves/{leave_id}")
        assert delete_response.status_code == 200

        # Verify deletion
        all_leaves = requests.get(f"{API_URL}/leaves").json()
        assert not any(l["leave_id"] == leave_id for l in all_leaves)
        print(f"✓ Leave deleted successfully: {leave_id}")

    def test_delete_nonexistent_leave(self):
        """Test deleting a non-existent leave returns 404"""
        response = requests.delete(f"{API_URL}/leaves/nonexistent-id")
        assert response.status_code == 404
        print("✓ Delete non-existent leave returns 404")

    def test_insufficient_balance_rejection(self):
        """Test leave application is rejected when balance is insufficient"""
        # Create employee with minimal balance (mid-year joining)
        unique_email = f"test.nobalance.{datetime.now().timestamp()}@tortoise.pro"
        employee = {
            "name": f"{TEST_PREFIX}No Balance",
            "email": unique_email,
            "joining_date": "2026-12-01",  # December - minimal balance
            "role": "employee",
            "carry_forward_el": 0.0
        }

        create_response = requests.post(f"{API_URL}/employees", json=employee)
        assert create_response.status_code == 200
        employee_id = create_response.json()["employee_id"]

        # Try to apply for many days of leave
        start_date = "2026-12-10"
        end_date = "2026-12-31"  # Many days

        leave_request = {
            "employee_id": employee_id,
            "start_date": start_date,
            "end_date": end_date,
            "leave_type": "ooo",
            "reason": "Should fail"
        }

        response = requests.post(f"{API_URL}/leaves", json=leave_request)
        assert response.status_code == 400
        assert "insufficient" in response.json()["detail"].lower()
        print("✓ Insufficient balance correctly rejected")


class TestHolidays:
    """Holiday management tests"""

    def test_create_holiday(self):
        """Test creating a new holiday"""
        holiday_data = {
            "name": f"{TEST_PREFIX}Test Holiday",
            "date": "2026-12-25",
            "year": 2026
        }

        response = requests.post(f"{API_URL}/holidays", json=holiday_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == holiday_data["name"]
        assert data["date"] == holiday_data["date"]
        assert data["year"] == 2026
        assert "holiday_id" in data
        print(f"✓ Holiday created: {data['name']} on {data['date']}")
        
        # Cleanup
        requests.delete(f"{API_URL}/holidays/{data['holiday_id']}")

    def test_get_all_holidays(self):
        """Test getting all holidays"""
        response = requests.get(f"{API_URL}/holidays")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Retrieved {len(data)} holidays")

    def test_get_holidays_by_year(self):
        """Test filtering holidays by year"""
        # First create a holiday for 2025
        holiday_data = {
            "name": f"{TEST_PREFIX}Year Filter Test",
            "date": "2025-07-04",
            "year": 2025
        }
        create_response = requests.post(f"{API_URL}/holidays", json=holiday_data)
        assert create_response.status_code == 200
        holiday_id = create_response.json()["holiday_id"]

        # Get holidays for 2025
        response = requests.get(f"{API_URL}/holidays?year=2025")
        assert response.status_code == 200
        
        data = response.json()
        for holiday in data:
            assert holiday["year"] == 2025
        print(f"✓ Filtered {len(data)} holidays for 2025")
        
        # Cleanup
        requests.delete(f"{API_URL}/holidays/{holiday_id}")

    def test_delete_holiday(self):
        """Test deleting a holiday"""
        # First create a holiday
        holiday_data = {
            "name": f"{TEST_PREFIX}Delete Test",
            "date": "2026-01-01",
            "year": 2026
        }
        create_response = requests.post(f"{API_URL}/holidays", json=holiday_data)
        assert create_response.status_code == 200
        holiday_id = create_response.json()["holiday_id"]

        # Delete the holiday
        delete_response = requests.delete(f"{API_URL}/holidays/{holiday_id}")
        assert delete_response.status_code == 200

        # Verify deletion
        all_holidays = requests.get(f"{API_URL}/holidays").json()
        assert not any(h["holiday_id"] == holiday_id for h in all_holidays)
        print(f"✓ Holiday deleted successfully")

    def test_delete_nonexistent_holiday(self):
        """Test deleting non-existent holiday returns 404"""
        response = requests.delete(f"{API_URL}/holidays/nonexistent-id")
        assert response.status_code == 404
        print("✓ Delete non-existent holiday returns 404")


class TestCalendar:
    """Calendar endpoint tests"""

    def test_get_calendar_current_month(self):
        """Test getting calendar for current month"""
        now = datetime.now()
        response = requests.get(
            f"{API_URL}/calendar",
            params={"year": now.year, "month": now.month}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "events" in data
        assert isinstance(data["events"], list)
        print(f"✓ Calendar for {now.year}-{now.month}: {len(data['events'])} events")

    def test_calendar_shows_leave_events(self):
        """Test that calendar shows applied leaves"""
        # Get HR user
        employees = requests.get(f"{API_URL}/employees").json()
        hr_user = next((emp for emp in employees if emp["email"].lower() == "ipshita@tortoise.pro"), None)
        
        # Apply leave for specific date
        now = datetime.now()
        test_date = (now + timedelta(days=30)).replace(day=15)  # 15th of next month
        if test_date.weekday() >= 5:  # Skip weekend
            test_date = test_date + timedelta(days=(7 - test_date.weekday()))
        
        date_str = test_date.strftime("%Y-%m-%d")
        
        leave_request = {
            "employee_id": hr_user["employee_id"],
            "start_date": date_str,
            "end_date": date_str,
            "leave_type": "ooo",
            "reason": "Calendar test"
        }

        create_response = requests.post(f"{API_URL}/leaves", json=leave_request)
        assert create_response.status_code == 200
        leave_id = create_response.json()["leave_id"]

        # Check calendar
        response = requests.get(
            f"{API_URL}/calendar",
            params={"year": test_date.year, "month": test_date.month}
        )
        assert response.status_code == 200
        
        events = response.json()["events"]
        leave_event = next((e for e in events if e.get("leave_id") == leave_id), None)
        assert leave_event is not None, "Leave should appear in calendar"
        assert leave_event["leave_type"] == "ooo"
        print(f"✓ Leave event found in calendar for {date_str}")
        
        # Cleanup
        requests.delete(f"{API_URL}/leaves/{leave_id}")

    def test_calendar_shows_holidays(self):
        """Test that calendar shows holidays"""
        # Create holiday
        now = datetime.now()
        test_date = (now + timedelta(days=60)).replace(day=10)
        date_str = test_date.strftime("%Y-%m-%d")
        
        holiday_data = {
            "name": f"{TEST_PREFIX}Calendar Holiday",
            "date": date_str,
            "year": test_date.year
        }
        create_response = requests.post(f"{API_URL}/holidays", json=holiday_data)
        assert create_response.status_code == 200
        holiday_id = create_response.json()["holiday_id"]

        # Check calendar
        response = requests.get(
            f"{API_URL}/calendar",
            params={"year": test_date.year, "month": test_date.month}
        )
        assert response.status_code == 200
        
        events = response.json()["events"]
        holiday_event = next((e for e in events if e.get("is_holiday") and e.get("holiday_name") == holiday_data["name"]), None)
        assert holiday_event is not None, "Holiday should appear in calendar"
        print(f"✓ Holiday event found in calendar for {date_str}")
        
        # Cleanup
        requests.delete(f"{API_URL}/holidays/{holiday_id}")


class TestLeaveBalanceDeduction:
    """Tests for leave balance deduction logic"""

    def test_ooo_deducts_cl_first_then_el(self):
        """Test that OOO deducts from CL first, then EL"""
        # Create employee with known balance
        unique_email = f"test.deduction.{datetime.now().timestamp()}@tortoise.pro"
        employee = {
            "name": f"{TEST_PREFIX}Deduction Test",
            "email": unique_email,
            "joining_date": "2026-01-01",  # Full year in 2026
            "role": "employee",
            "carry_forward_el": 0.0
        }

        create_response = requests.post(f"{API_URL}/employees", json=employee)
        assert create_response.status_code == 200
        employee_id = create_response.json()["employee_id"]

        # Get initial balance for 2026
        balance_before = requests.get(f"{API_URL}/employees/{employee_id}/balance?year=2026").json()
        initial_cl = balance_before["casual_leave"]["available"]
        initial_el = balance_before["earned_leave"]["available"]
        
        # Apply OOO leave that exceeds CL
        days_to_apply = initial_cl + 2  # 2 days more than CL available
        
        # Find weekdays for the leave
        start_date = datetime(2026, 2, 2)  # February 2026
        while start_date.weekday() >= 5:  # Skip weekend
            start_date += timedelta(days=1)
        
        # Calculate end date for required weekdays
        current = start_date
        weekdays_count = 0
        while weekdays_count < days_to_apply:
            if current.weekday() < 5:
                weekdays_count += 1
            if weekdays_count < days_to_apply:
                current += timedelta(days=1)
        
        leave_request = {
            "employee_id": employee_id,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": current.strftime("%Y-%m-%d"),
            "leave_type": "ooo",
            "reason": "Test CL then EL deduction"
        }

        leave_response = requests.post(f"{API_URL}/leaves", json=leave_request)
        assert leave_response.status_code == 200
        leave_id = leave_response.json()["leave_id"]

        # Get balance after
        balance_after = requests.get(f"{API_URL}/employees/{employee_id}/balance?year=2026").json()
        
        # CL should be 0 (all used)
        assert balance_after["casual_leave"]["used"] == initial_cl, \
            f"CL should be fully used first. Expected {initial_cl}, got {balance_after['casual_leave']['used']}"
        
        # EL should have 2 used (overflow from CL)
        assert balance_after["earned_leave"]["used"] == 2, \
            f"EL should have 2 days used. Expected 2, got {balance_after['earned_leave']['used']}"
        
        print(f"✓ OOO correctly deducts CL first ({initial_cl} days), then EL (2 days)")
        
        # Cleanup
        requests.delete(f"{API_URL}/leaves/{leave_id}")

    def test_wfh_deducts_from_wfh_balance(self):
        """Test that WFH deducts from WFH balance only"""
        # Get HR user
        employees = requests.get(f"{API_URL}/employees").json()
        hr_user = next((emp for emp in employees if emp["email"].lower() == "ipshita@tortoise.pro"), None)

        # Get initial WFH balance
        balance_before = requests.get(f"{API_URL}/employees/{hr_user['employee_id']}/balance").json()
        initial_wfh = balance_before["wfh"]["available"]
        initial_wfh_used = balance_before["wfh"]["used"]

        # Apply 1 day WFH
        test_date = datetime.now() + timedelta(days=45)
        while test_date.weekday() >= 5:
            test_date += timedelta(days=1)
        
        leave_request = {
            "employee_id": hr_user["employee_id"],
            "start_date": test_date.strftime("%Y-%m-%d"),
            "end_date": test_date.strftime("%Y-%m-%d"),
            "leave_type": "wfh",
            "reason": "WFH deduction test"
        }

        response = requests.post(f"{API_URL}/leaves", json=leave_request)
        assert response.status_code == 200
        leave_id = response.json()["leave_id"]

        # Check balance after
        balance_after = requests.get(f"{API_URL}/employees/{hr_user['employee_id']}/balance").json()
        
        assert balance_after["wfh"]["used"] == initial_wfh_used + 1, "WFH used should increase by 1"
        assert balance_after["wfh"]["available"] == initial_wfh - 1, "WFH available should decrease by 1"
        print(f"✓ WFH correctly deducts from WFH balance")
        
        # Cleanup
        requests.delete(f"{API_URL}/leaves/{leave_id}")


# Cleanup function to remove test data
def cleanup_test_data():
    """Remove TEST_ prefixed employees after tests"""
    employees = requests.get(f"{API_URL}/employees").json()
    test_employees = [emp for emp in employees if emp["name"].startswith(TEST_PREFIX)]
    
    # We don't have a delete employee endpoint, so just leave them
    # In production, you'd want an admin cleanup endpoint
    print(f"Note: {len(test_employees)} test employees created (cleanup not implemented)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
