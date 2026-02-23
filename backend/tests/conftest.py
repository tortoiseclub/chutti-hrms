import pytest
import requests
import os

# Use environment variable or fallback for testing
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://attendance-hub-225.preview.emergentagent.com').rstrip('/')
API_URL = f"{BASE_URL}/api"

@pytest.fixture(scope="session")
def api_url():
    """Return the base API URL"""
    return API_URL

@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="session")
def hr_user():
    """HR user credentials"""
    return {
        "email": "ipshita@Tortoise.pro",
        "name": "Ipshita"
    }

@pytest.fixture(scope="session")
def test_employee_data():
    """Test employee data for creation"""
    return {
        "name": "Test Employee",
        "email": "test.employee@tortoise.pro",
        "joining_date": "2025-01-01",
        "role": "employee",
        "carry_forward_el": 0.0
    }
