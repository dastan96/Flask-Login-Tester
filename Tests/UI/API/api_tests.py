import requests

BASE_URL = "http://127.0.0.1:5001"  # The base URL of your Flask app

def test_login_success():
    endpoint = f"{BASE_URL}/login"
    payload = {
        "username": "testuser",  # Make sure this user exists in `users` dictionary in `app.py`
        "password": "password123"
    }
    response = requests.post(endpoint, json=payload)
    print(f"Login Response: {response.status_code}, {response.json()}")
    assert response.status_code == 200
    assert response.json()["message"] == "Login successful"

if __name__ == "__main__":
    # Call the test function
    test_login_success()



 
