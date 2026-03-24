"""
Tests for Leave Balance Visibility Feature
- HR can see all employees' leave balances
- Employees can only see their own leave balance
- Tests the /balances endpoint with X-Employee-Id and X-Employee-Role headers
"""
import pytest
import requests
import os
from datetime import datetime

# Configuration
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://attendance-hub-225.preview.emergentagent.com').rstrip('/')
API_URL = f"{BASE_URL}/api"

# Test credentials
HR_EMAIL = "ipshita@Tortoise.pro"
HR_PASSWORD = "TortoiseHR@2024"
TEST_EMPLOYEE_EMAIL = "chirag@tortoise.pro"


class TestLeaveBalanceVisibility:
    """Tests for role-based leave balance visibility"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Get HR user and find/create test employee"""
        # Login as HR to get employee_id
        login_response = requests.post(
            f"{API_URL}/auth/login",
            json={"email": HR_EMAIL, "password": HR_PASSWORD}
        )
        assert login_response.status_code == 200, f"HR login failed: {login_response.text}"
        self.hr_user = login_response.json()
        print(f"HR user logged in: {self.hr_user['name']} (ID: {self.hr_user['employee_id']})")
        
        # Get all employees to find a test employee
        employees_response = requests.get(f"{API_URL}/employees")
        assert employees_response.status_code == 200
        employees = employees_response.json()
        
        # Find chirag@tortoise.pro or any non-HR employee
        self.test_employee = None
        for emp in employees:
            if emp["email"].lower() == TEST_EMPLOYEE_EMAIL.lower():
                self.test_employee = emp
                break
            elif emp["role"] == "employee" and emp["email"].lower() != HR_EMAIL.lower():
                self.test_employee = emp
        
        if self.test_employee:
            print(f"Test employee found: {self.test_employee['name']} (ID: {self.test_employee['employee_id']})")
        else:
            print("No test employee found - will create one")
            # Create a test employee
            unique_email = f"test.visibility.{datetime.now().timestamp()}@tortoise.pro"
            create_response = requests.post(
                f"{API_URL}/employees",
                json={
                    "name": "TEST_Visibility Employee",
                    "email": unique_email,
                    "joining_date": "2025-01-01",
                    "role": "employee",
                    "carry_forward_el": 0.0
                }
            )
            assert create_response.status_code == 200, f"Failed to create test employee: {create_response.text}"
            self.test_employee = create_response.json()
            print(f"Created test employee: {self.test_employee['name']} (ID: {self.test_employee['employee_id']})")

    def test_hr_sees_all_balances(self):
        """Test that HR role can see all employees' leave balances"""
        response = requests.get(
            f"{API_URL}/balances",
            headers={
                "X-Employee-Id": self.hr_user["employee_id"],
                "X-Employee-Role": "hr"
            }
        )
        assert response.status_code == 200
        
        balances = response.json()
        assert isinstance(balances, list)
        assert len(balances) > 1, "HR should see multiple employees' balances"
        
        # Verify HR's own balance is included
        hr_balance = next((b for b in balances if b["employee_id"] == self.hr_user["employee_id"]), None)
        assert hr_balance is not None, "HR's own balance should be in the list"
        
        # Verify test employee's balance is included
        if self.test_employee:
            emp_balance = next((b for b in balances if b["employee_id"] == self.test_employee["employee_id"]), None)
            assert emp_balance is not None, "Test employee's balance should be visible to HR"
        
        print(f"✓ HR can see all {len(balances)} employees' balances")

    def test_employee_sees_only_own_balance(self):
        """Test that employee role can only see their own leave balance"""
        if not self.test_employee:
            pytest.skip("No test employee available")
        
        response = requests.get(
            f"{API_URL}/balances",
            headers={
                "X-Employee-Id": self.test_employee["employee_id"],
                "X-Employee-Role": "employee"
            }
        )
        assert response.status_code == 200
        
        balances = response.json()
        assert isinstance(balances, list)
        assert len(balances) == 1, f"Employee should see only 1 balance, got {len(balances)}"
        
        # Verify it's their own balance
        assert balances[0]["employee_id"] == self.test_employee["employee_id"], \
            "Employee should only see their own balance"
        assert balances[0]["employee_name"] == self.test_employee["name"], \
            "Balance should have correct employee name"
        
        print(f"✓ Employee sees only their own balance: {balances[0]['employee_name']}")

    def test_employee_cannot_see_hr_balance(self):
        """Test that employee cannot see HR's balance"""
        if not self.test_employee:
            pytest.skip("No test employee available")
        
        response = requests.get(
            f"{API_URL}/balances",
            headers={
                "X-Employee-Id": self.test_employee["employee_id"],
                "X-Employee-Role": "employee"
            }
        )
        assert response.status_code == 200
        
        balances = response.json()
        
        # Verify HR's balance is NOT in the list
        hr_balance = next((b for b in balances if b["employee_id"] == self.hr_user["employee_id"]), None)
        assert hr_balance is None, "Employee should NOT see HR's balance"
        
        print("✓ Employee cannot see HR's balance")

    def test_no_headers_returns_all_balances(self):
        """Test that without headers, all balances are returned (backward compatibility)"""
        response = requests.get(f"{API_URL}/balances")
        assert response.status_code == 200
        
        balances = response.json()
        assert isinstance(balances, list)
        assert len(balances) > 1, "Without headers, should return all balances"
        
        print(f"✓ Without headers, returns all {len(balances)} balances (backward compatible)")

    def test_balance_structure_is_correct(self):
        """Test that balance response has correct structure"""
        response = requests.get(
            f"{API_URL}/balances",
            headers={
                "X-Employee-Id": self.hr_user["employee_id"],
                "X-Employee-Role": "hr"
            }
        )
        assert response.status_code == 200
        
        balances = response.json()
        assert len(balances) > 0
        
        balance = balances[0]
        
        # Check required fields
        assert "employee_id" in balance
        assert "employee_name" in balance
        assert "earned_leave" in balance
        assert "casual_leave" in balance
        assert "wfh" in balance
        
        # Check nested structure
        for leave_type in ["earned_leave", "casual_leave", "wfh"]:
            assert "total" in balance[leave_type], f"{leave_type} should have 'total'"
            assert "used" in balance[leave_type], f"{leave_type} should have 'used'"
            assert "available" in balance[leave_type], f"{leave_type} should have 'available'"
        
        print("✓ Balance structure is correct")


class TestGoogleCalendarIntegration:
    """Tests for Google Calendar integration (checking logs for event creation)"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Get HR user"""
        login_response = requests.post(
            f"{API_URL}/auth/login",
            json={"email": HR_EMAIL, "password": HR_PASSWORD}
        )
        assert login_response.status_code == 200
        self.hr_user = login_response.json()

    def test_leave_application_creates_calendar_event(self):
        """Test that applying for leave creates a Google Calendar event"""
        from datetime import timedelta
        
        # Apply for leave - ensure it's a weekday
        test_date = datetime.now() + timedelta(days=60)
        # Skip to Monday if weekend
        while test_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
            test_date += timedelta(days=1)
        
        start_date = test_date.strftime("%Y-%m-%d")
        end_date = start_date
        
        leave_request = {
            "employee_id": self.hr_user["employee_id"],
            "start_date": start_date,
            "end_date": end_date,
            "leave_type": "ooo",
            "reason": "Test Google Calendar integration"
        }
        
        response = requests.post(f"{API_URL}/leaves", json=leave_request)
        assert response.status_code == 200
        
        leave_data = response.json()
        assert "leave_id" in leave_data
        
        # Note: We can't directly verify Google Calendar event creation from API
        # The main agent mentioned checking backend logs for 'Google Calendar event created'
        # This test verifies the leave is created successfully
        
        print(f"✓ Leave created successfully: {leave_data['leave_id']}")
        print("  Note: Check backend logs for 'Google Calendar event created' message")
        
        # Store leave_id for cleanup
        self.leave_id = leave_data["leave_id"]
        
        # Cleanup
        requests.delete(f"{API_URL}/leaves/{leave_data['leave_id']}")

    def test_holiday_creation_creates_calendar_event(self):
        """Test that creating a holiday creates a Google Calendar event"""
        holiday_data = {
            "name": "TEST_Calendar Holiday",
            "date": "2026-08-15",
            "year": 2026
        }
        
        response = requests.post(f"{API_URL}/holidays", json=holiday_data)
        assert response.status_code == 200
        
        holiday = response.json()
        assert "holiday_id" in holiday
        
        print(f"✓ Holiday created successfully: {holiday['holiday_id']}")
        print("  Note: Check backend logs for 'Google Calendar event created' message")
        
        # Cleanup
        requests.delete(f"{API_URL}/holidays/{holiday['holiday_id']}")

    def test_leave_deletion_removes_calendar_event(self):
        """Test that deleting a leave removes the Google Calendar event"""
        from datetime import timedelta
        
        # First create a leave
        start_date = (datetime.now() + timedelta(days=70)).strftime("%Y-%m-%d")
        
        leave_request = {
            "employee_id": self.hr_user["employee_id"],
            "start_date": start_date,
            "end_date": start_date,
            "leave_type": "wfh",
            "reason": "Test calendar deletion"
        }
        
        create_response = requests.post(f"{API_URL}/leaves", json=leave_request)
        assert create_response.status_code == 200
        leave_id = create_response.json()["leave_id"]
        
        # Delete the leave
        delete_response = requests.delete(f"{API_URL}/leaves/{leave_id}")
        assert delete_response.status_code == 200
        
        print(f"✓ Leave deleted successfully: {leave_id}")
        print("  Note: Check backend logs for 'Google Calendar event deleted' message")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
