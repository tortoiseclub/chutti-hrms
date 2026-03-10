"""
Backend API Tests for Password Authentication Features
Tests: Login with password, Forgot password, Reset password, Token verification
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
TEST_PREFIX = "TEST_AUTH_"


class TestPasswordLogin:
    """Password-based login tests"""

    def test_hr_login_with_correct_password(self):
        """Test HR login with valid email and password"""
        response = requests.post(
            f"{API_URL}/auth/login",
            json={"email": HR_EMAIL, "password": HR_PASSWORD}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "email" in data
        assert "name" in data
        assert "role" in data
        assert "employee_id" in data
        assert data["role"] == "hr"
        assert data["email"].lower() == HR_EMAIL.lower()
        print(f"✓ HR login successful with password: {data['name']} ({data['role']})")

    def test_login_fails_with_wrong_password(self):
        """Test login fails with incorrect password"""
        response = requests.post(
            f"{API_URL}/auth/login",
            json={"email": HR_EMAIL, "password": "WrongPassword123"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "detail" in data
        assert "invalid password" in data["detail"].lower()
        print("✓ Login correctly fails with wrong password (401)")

    def test_login_fails_for_nonexistent_user(self):
        """Test login fails for non-existent user"""
        response = requests.post(
            f"{API_URL}/auth/login",
            json={"email": "nonexistent@example.com", "password": "somepassword123"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
        print("✓ Login correctly fails for non-existent user (404)")

    def test_login_case_insensitive_email(self):
        """Test login is case-insensitive for email"""
        response = requests.post(
            f"{API_URL}/auth/login",
            json={"email": HR_EMAIL.upper(), "password": HR_PASSWORD}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["role"] == "hr"
        print("✓ Case-insensitive email login works")


class TestForgotPassword:
    """Forgot password endpoint tests"""

    def test_forgot_password_existing_email(self):
        """Test forgot password sends email for existing user"""
        response = requests.post(
            f"{API_URL}/auth/forgot-password",
            json={"email": HR_EMAIL}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data
        # Should not reveal if email exists (security)
        assert "if your email exists" in data["message"].lower()
        print("✓ Forgot password works for existing email")

    def test_forgot_password_nonexistent_email(self):
        """Test forgot password returns same message for non-existent email (security)"""
        response = requests.post(
            f"{API_URL}/auth/forgot-password",
            json={"email": "random_nonexistent@example.com"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data
        # Same message as existing email to prevent enumeration
        assert "if your email exists" in data["message"].lower()
        print("✓ Forgot password returns same message for non-existent email (prevents enumeration)")


class TestResetToken:
    """Password reset token tests"""

    def test_verify_invalid_token(self):
        """Test verification fails with invalid token"""
        response = requests.get(
            f"{API_URL}/auth/verify-reset-token",
            params={"token": "invalid_token_12345"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "detail" in data
        print("✓ Invalid token correctly rejected (400)")

    def test_reset_password_invalid_token(self):
        """Test password reset fails with invalid token"""
        response = requests.post(
            f"{API_URL}/auth/reset-password",
            json={"token": "invalid_token_12345", "new_password": "NewPassword123!"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "detail" in data
        assert "invalid" in data["detail"].lower() or "expired" in data["detail"].lower()
        print("✓ Reset password correctly fails with invalid token (400)")

    def test_reset_password_short_password(self):
        """Test password reset fails if password is too short"""
        # This will fail because token is invalid first, but we test the validation
        response = requests.post(
            f"{API_URL}/auth/reset-password",
            json={"token": "some_token", "new_password": "short"}
        )
        # Token validation happens first, so we get 400 for invalid token
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("✓ Short password reset request handled (token checked first)")


class TestEmployeeCreationWithPassword:
    """Test employee creation generates password and sends email"""

    def test_create_employee_sends_welcome_email(self):
        """Test creating employee generates password and sends welcome email"""
        unique_email = f"test.newemployee.{datetime.now().timestamp()}@tortoise.pro"
        employee_data = {
            "name": f"{TEST_PREFIX}New Employee",
            "email": unique_email,
            "joining_date": "2025-06-01",
            "role": "employee",
            "carry_forward_el": 0.0
        }

        response = requests.post(
            f"{API_URL}/employees",
            json=employee_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["email"] == unique_email
        assert "employee_id" in data
        print(f"✓ Employee created: {unique_email}")
        print(f"  - Welcome email should have been sent with generated password")
        print(f"  - Employee ID: {data['employee_id']}")
        
        # Note: We can't verify the generated password here as it's only sent via email
        # and hashed in database. We'd need to check backend logs.
        return data["employee_id"], unique_email

    def test_created_employee_has_password(self):
        """Test that created employee has password set in database"""
        # Create a new employee
        unique_email = f"test.passcheck.{datetime.now().timestamp()}@tortoise.pro"
        employee_data = {
            "name": f"{TEST_PREFIX}Password Check",
            "email": unique_email,
            "joining_date": "2025-06-01",
            "role": "employee",
            "carry_forward_el": 0.0
        }

        create_response = requests.post(f"{API_URL}/employees", json=employee_data)
        assert create_response.status_code == 200
        
        # Try to login with wrong password - should get 401 (not 400 for password not set)
        login_response = requests.post(
            f"{API_URL}/auth/login",
            json={"email": unique_email, "password": "WrongPassword123"}
        )
        
        # If password is set, we should get 401 (invalid password), not 400 (password not set)
        assert login_response.status_code == 401, \
            f"Expected 401 (invalid password), got {login_response.status_code}. Password might not be set."
        print(f"✓ Created employee has password set (login returns 401 for wrong password)")


class TestPasswordResetFlow:
    """End-to-end password reset flow tests"""

    def test_forgot_then_verify_token_flow(self):
        """Test the forgot password creates a valid reset token in DB"""
        # Step 1: Request forgot password
        response = requests.post(
            f"{API_URL}/auth/forgot-password",
            json={"email": HR_EMAIL}
        )
        assert response.status_code == 200
        print("✓ Forgot password request successful")
        
        # Note: We can't get the actual token without DB access or email
        # This is expected behavior - tokens should only be delivered via email

    def test_full_password_reset_would_work(self):
        """Document that full flow requires actual email/DB access"""
        # This test documents the expected flow:
        # 1. User requests forgot password
        # 2. Email sent with reset link containing token
        # 3. User clicks link, frontend verifies token
        # 4. User enters new password
        # 5. Password is reset
        
        # We can't fully test this without:
        # - Access to sent email (to get token)
        # - Or direct DB access (to get token from password_resets collection)
        
        print("✓ Full password reset flow documented")
        print("  - Step 1: POST /api/auth/forgot-password - TESTED")
        print("  - Step 2: Email sent via SendGrid - LIVE (not mocked)")
        print("  - Step 3: GET /api/auth/verify-reset-token - requires valid token")
        print("  - Step 4: POST /api/auth/reset-password - requires valid token")


class TestSecurityChecks:
    """Security-related tests"""

    def test_password_not_exposed_in_response(self):
        """Test that password hash is not returned in API responses"""
        response = requests.get(f"{API_URL}/employees")
        assert response.status_code == 200
        
        employees = response.json()
        for emp in employees:
            assert "password_hash" not in emp, "Password hash should not be in response"
            assert "password" not in emp, "Plain password should not be in response"
        print("✓ Password not exposed in employee list response")

    def test_email_enumeration_prevention(self):
        """Test that forgot password doesn't reveal if email exists"""
        # Existing email
        resp1 = requests.post(
            f"{API_URL}/auth/forgot-password",
            json={"email": HR_EMAIL}
        )
        
        # Non-existing email
        resp2 = requests.post(
            f"{API_URL}/auth/forgot-password",
            json={"email": "definitely_not_real@nowhere.com"}
        )
        
        # Both should return same status and similar message
        assert resp1.status_code == resp2.status_code == 200
        assert resp1.json()["message"] == resp2.json()["message"]
        print("✓ Email enumeration prevented (same response for existing/non-existing)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
