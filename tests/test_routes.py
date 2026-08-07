def assert_dashboard_response(response):
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "QA Engineering Lab" in body
    assert 'href="/">Dashboard</a>' in body
    assert 'href="/login">Login Demo</a>' in body
    assert 'href="/test-plan">Test Plan</a>' in body
    assert 'href="/about">About</a>' in body
    assert "Logout" not in body
    assert "MyDemo" not in body
    assert "My Demo" not in body
    assert "Latest CI Test Results" in body
    assert "Test Results" in body
    assert 'id="dashboardLoading"' in body
    assert 'id="dashboardUnavailable"' in body
    assert 'id="dashboardContent"' in body
    assert 'id="suiteSummaries"' in body
    assert 'id="testResultsBody"' in body
    assert "/api/test-results/latest" not in body


def assert_public_nav(body):
    assert 'href="/">Dashboard</a>' in body
    assert 'href="/login">Login Demo</a>' in body
    assert 'href="/test-plan">Test Plan</a>' in body
    assert 'href="/about">About</a>' in body
    assert "Logout" not in body


def test_get_root_renders_dashboard(client):
    response = client.get("/")

    assert_dashboard_response(response)


def test_get_welcome_redirects_to_canonical_dashboard(client):
    response = client.get("/welcome")

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_get_welcome_redirect_displays_dashboard(client):
    response = client.get("/welcome", follow_redirects=True)

    assert_dashboard_response(response)


def test_get_welcome_api_true_preserves_json_response(client):
    response = client.get("/welcome?api=true")
    data = response.get_json()

    assert response.status_code == 200
    assert response.is_json
    assert set(data.keys()) == {"summary", "test_cases"}
    assert set(data["summary"].keys()) == {"backend_passed", "backend_failed", "pending"}
    assert data["summary"]["pending"] == 2
    assert isinstance(data["summary"]["backend_passed"], int)
    assert isinstance(data["summary"]["backend_failed"], int)
    assert isinstance(data["test_cases"], list)
    for test_case in data["test_cases"]:
        assert set(test_case.keys()) == {
            "test_id",
            "test_name",
            "status",
            "duration",
            "last_run",
        }


def test_get_login_includes_public_navigation(client):
    response = client.get("/login")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "QA Engineering Lab" in body
    assert "Test positive and negative authentication scenarios using the demo credentials below." in body
    assert_public_nav(body)


def test_valid_browser_login_renders_success_on_login(client):
    response = client.post(
        "/login",
        data={"username": "automation_user1", "password": "secret_pass123"},
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.request.path == "/login"
    assert "Location" not in response.headers
    assert "QA Engineering Lab" in body
    assert 'role="status"' in body
    assert 'aria-live="polite"' in body
    assert "Login successful" in body


def test_invalid_browser_login_renders_accessible_error(client):
    response = client.post(
        "/login",
        data={"username": "automation_user1", "password": "wrong-password"},
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.request.path == "/login"
    assert 'role="alert"' in body
    assert "Invalid credentials. Try again." in body


def test_missing_username_renders_accessible_error(client):
    response = client.post(
        "/login",
        data={"username": "", "password": "secret_pass123"},
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.request.path == "/login"
    assert 'role="alert"' in body
    assert "Username is a required field." in body


def test_missing_password_renders_accessible_error(client):
    response = client.post(
        "/login",
        data={"username": "automation_user1", "password": ""},
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.request.path == "/login"
    assert 'role="alert"' in body
    assert "Password is a required field." in body
