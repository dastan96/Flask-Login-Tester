import pytest
import requests

BASE_URL = "http://127.0.0.1:5001"

# Positive Test: Valid Login
def test_login_success():
    endpoint = f"{BASE_URL}/login"
    payload = {"username": "automation_user1", "password": "secret_pass123"}
    response = requests.post(endpoint, json=payload)
    # When sending JSON, the login route returns JSON rather than a redirect.
    assert response.status_code == 200
    data = response.json()
    assert data.get("message") == "Login successful"
    assert data.get("username") == "automation_user1"

# Positive Test: Welcome Page
def test_welcome_page():
    endpoint = f"{BASE_URL}/welcome"
    params = {"api": "true"}
    response = requests.get(endpoint, params=params)
    # Ensure that the welcome API returns 200
    assert response.status_code == 200

    result_data = response.json()

    # Ensure the response contains all expected keys.
    required_keys = [
        "status",
        "ui_passed",
        "backend_passed",
        "ui_failed",
        "backend_failed",
        "duration",
        "last_run"
    ]
    for key in required_keys:
        assert key in result_data, f"Missing key in response: {key}"

    # Accept either "Passed", "Failed", or "Not Run"
    assert result_data["status"] in ["Passed", "Not Run", "Failed"]


# Negative Test: Invalid Credentials
def test_login_invalid_credentials():
    endpoint = f"{BASE_URL}/login"
    payload = {"username": "testuser", "password": "wrongpassword"}
    response = requests.post(endpoint, json=payload)
    assert response.status_code == 401
    data = response.json()
    assert data.get("error") == "Invalid credentials. Try again."

# Negative Test: Missing Username
def test_login_missing_username():
    endpoint = f"{BASE_URL}/login"
    payload = {"username": "", "password": "password123"}
    response = requests.post(endpoint, json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data.get("error") == "Username is a required field."

# Negative Test: Missing Password
def test_login_missing_password():
    endpoint = f"{BASE_URL}/login"
    payload = {"username": "testuser", "password": ""}
    response = requests.post(endpoint, json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data.get("error") == "Password is a required field."
