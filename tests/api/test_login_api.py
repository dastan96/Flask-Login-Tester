SUCCESS_RESPONSE = {
    "message": "Login successful",
    "username": "automation_user1",
}
INVALID_CREDENTIALS_RESPONSE = {"error": "Invalid credentials. Try again."}
USERNAME_REQUIRED_RESPONSE = {"error": "Username is a required field."}
PASSWORD_REQUIRED_RESPONSE = {"error": "Password is a required field."}
INVALID_REQUEST_RESPONSE = {"error": "Invalid request format."}


def assert_json_response(response, status_code, body):
    assert response.status_code == status_code
    assert response.is_json
    assert response.get_json() == body


def test_api_01_01_login_valid_credentials(client):
    response = client.post(
        "/login",
        json={"username": "automation_user1", "password": "secret_pass123"},
    )

    assert_json_response(response, 200, SUCCESS_RESPONSE)


def test_api_01_02_login_unknown_username(client):
    response = client.post(
        "/login",
        json={"username": "unknown_user", "password": "secret_pass123"},
    )

    assert_json_response(response, 401, INVALID_CREDENTIALS_RESPONSE)


def test_api_01_03_login_wrong_password(client):
    response = client.post(
        "/login",
        json={"username": "automation_user1", "password": "wrong-password"},
    )

    assert_json_response(response, 401, INVALID_CREDENTIALS_RESPONSE)


def test_api_01_04_login_missing_username(client):
    response = client.post(
        "/login",
        json={"password": "secret_pass123"},
    )

    assert_json_response(response, 400, USERNAME_REQUIRED_RESPONSE)


def test_api_01_05_login_empty_username(client):
    response = client.post(
        "/login",
        json={"username": "", "password": "secret_pass123"},
    )

    assert_json_response(response, 400, USERNAME_REQUIRED_RESPONSE)


def test_api_01_06_login_null_username(client):
    response = client.post(
        "/login",
        json={"username": None, "password": "secret_pass123"},
    )

    assert_json_response(response, 400, USERNAME_REQUIRED_RESPONSE)


def test_api_01_07_login_missing_password(client):
    response = client.post(
        "/login",
        json={"username": "automation_user1"},
    )

    assert_json_response(response, 400, PASSWORD_REQUIRED_RESPONSE)


def test_api_01_08_login_empty_password(client):
    response = client.post(
        "/login",
        json={"username": "automation_user1", "password": ""},
    )

    assert_json_response(response, 400, PASSWORD_REQUIRED_RESPONSE)


def test_api_01_09_login_null_password(client):
    response = client.post(
        "/login",
        json={"username": "automation_user1", "password": None},
    )

    assert_json_response(response, 400, PASSWORD_REQUIRED_RESPONSE)


def test_api_01_10_login_empty_json_object(client):
    response = client.post("/login", json={})

    assert_json_response(response, 400, INVALID_REQUEST_RESPONSE)
