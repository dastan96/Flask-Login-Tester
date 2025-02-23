import pytest
import requests

BASE_URL = "http://127.0.0.1:5001"

# Positive Test: Valid Login
def test_api_01_01_login_valid_credentials(): 
    endpoint = f"{BASE_URL}/login"
    payload = {"username": "automation_user1", "password": "secret_pass123"}
    response = requests.post(endpoint, json=payload)
    # When sending JSON, the login route returns JSON rather than a redirect.
    assert response.status_code == 200
    data = response.json()
    assert data.get("message") == "Login successful"
    assert data.get("username") == "automation_user1"

# Positive Test: Welcome Page
def test_api_01_02_welcome_page():
    endpoint = f"{BASE_URL}/welcome"
    params = {"api": "true"}
    response = requests.get(endpoint, params=params)
    assert response.status_code == 200

    result_data = response.json()

    # Ensure the response has both summary and test_cases keys
    assert "summary" in result_data, "Missing key 'summary' in response"
    assert "test_cases" in result_data, "Missing key 'test_cases' in response"

    # Check that each test case has the expected keys
    required_keys = ["test_id", "test_name", "status", "duration", "last_run"]
    for test in result_data["test_cases"]:
        for key in required_keys:
            assert key in test, f"Missing key '{key}' in test case: {test}"

    # Optionally, check the summary values
    assert isinstance(result_data["summary"].get("backend_passed"), int)
    assert isinstance(result_data["summary"].get("backend_failed"), int)


# Negative Test: Invalid Credentials
def test_api_01_03_login_invalid_credentials():
    endpoint = f"{BASE_URL}/login"
    payload = {"username": "testuser", "password": "wrongpassword"}
    response = requests.post(endpoint, json=payload)
    assert response.status_code == 401
    data = response.json()
    assert data.get("error") == "Invalid credentials. Try again."

# Negative Test: Missing Username
def test_api_01_04_login_missing_username():
    endpoint = f"{BASE_URL}/login"
    payload = {"username": "", "password": "password123"}
    response = requests.post(endpoint, json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data.get("error") == "Username is a required field."

# Negative Test: Missing Password
def test_api_01_05_login_missing_password(): 
    endpoint = f"{BASE_URL}/login"
    payload = {"username": "testuser", "password": ""}
    response = requests.post(endpoint, json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data.get("error") == "Password is a required field."
