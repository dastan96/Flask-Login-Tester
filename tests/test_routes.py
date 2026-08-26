import re
from pathlib import Path

import app as app_module
from services.ai_report_feed_service import AIReportFeedError


def assert_dashboard_response(response):
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "QA Lab" in body
    assert "QA Engineering Lab" not in body
    assert 'href="/">Dashboard</a>' in body
    assert 'href="/login">Login Demo</a>' in body
    assert 'href="/test-plan">Test Library</a>' in body
    assert 'href="/about">Architecture</a>' in body
    assert 'href="/about">About</a>' not in body
    assert "Logout" not in body
    assert "MyDemo" not in body
    assert "My Demo" not in body
    assert "Latest CI Test Results" in body
    assert "Test Cases" in body
    assert 'id="dashboardLoading"' in body
    assert 'id="dashboardUnavailable"' in body
    assert 'id="dashboardContent"' in body
    assert 'id="suiteSummaries"' in body
    assert 'id="testResultsBody"' in body
    assert 'id="testCasesToggle"' in body
    assert 'aria-expanded="false"' in body
    assert 'aria-controls="testResultsBody"' in body
    assert "/api/test-results/latest" not in body


def assert_public_nav(body):
    assert 'href="/">Dashboard</a>' in body
    assert 'href="/login">Login Demo</a>' in body
    assert 'href="/test-plan">Test Library</a>' in body
    assert 'href="/about">Architecture</a>' in body
    assert 'href="/about">About</a>' not in body
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
    assert "QA Lab" in body
    assert "QA Engineering Lab" not in body
    assert "Test positive and negative authentication scenarios using the demo credentials below." in body
    assert_public_nav(body)


def test_get_test_plan_uses_canonical_public_navbar(client):
    response = client.get("/test-plan")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert '<nav class="navbar navbar-expand-lg navbar-dark bg-primary">' in body
    assert '<div class="container">' in body
    assert '<div class="container-fluid">' not in body
    assert_public_nav(body)
    assert "Test Suites" in body
    assert "<h2>Test Plan</h2>" not in body
    assert "Browse the automated test suites and detailed test cases used to validate the application." in body
    assert ">Features<" not in body
    assert "Under Development" not in body
    assert "Test Case Details" not in body
    assert "Expected Result:" in body
    assert "Expectation:" not in body


def test_test_library_defines_public_suite_ids_and_dynamic_modal_title():
    script = Path("static/js/test_plan.js").read_text(encoding="utf-8")

    expected_ids = {
        *(f"01.{number:02d}" for number in range(1, 11)),
        *(f"02.{number:02d}" for number in range(1, 12)),
        *(f"03.{number:02d}" for number in range(1, 6)),
    }
    defined_ids = set(re.findall(r'id: "(\d{2}\.\d{2})"', script))

    assert "01 — Login API Tests" in script
    assert "02 — Flask Route Tests" in script
    assert "03 — UI Tests" in script
    assert defined_ids == expected_ids
    assert "User Interface Tests (Under Development)" not in script
    assert "Test Case Details" not in script
    assert "function renderModalTitle(testCase)" in script
    assert 'id.className = "case-id";' in script
    assert 'title.className = "case-title";' in script
    assert "modalTitle.append(id, title);" in script
    assert "testCase.id} — ${testCase.title}" not in script


def test_get_about_reflects_current_reporting_architecture(client):
    response = client.get("/about")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert_public_nav(body)
    for expected in [
        "QA LAB ARCHITECTURE",
        "Quality Engineering in Practice",
        "Quality Engineering Capabilities",
        "TESTING STRATEGY",
        "Login API Tests",
        "pytest · Flask test client",
        "Flask Route Tests",
        "UI Tests",
        "Playwright · Chromium",
        "Backend pytest job",
        "Playwright UI job",
        "aggregate-results",
        "latest.json",
        "GitHub Pages",
        "Flask results endpoint",
        "QA Lab dashboard",
        "Hosted on Render",
        "Pull requests validate backend, browser, and aggregation jobs; production reporting is published only from main.",
        "WHY THIS ARCHITECTURE?",
        "Separate test execution",
        "One reporting source of truth",
        "Sanitized public reporting",
        "View GitHub Repository",
    ]:
        assert expected in body

    for stale_content in [
        'href="/about">About</a>',
        "What This Demonstrates",
        "Technology Stack",
        "View Test Plan",
        "Legacy Note",
        "Public Links",
        "SQLite Database Storage",
        "report.json",
        "run_all_tests.py",
        "api_tests.py",
        "project_diagram.jpeg",
    ]:
        assert stale_content not in body


def test_dashboard_js_accepts_legacy_web_routes_alias():
    script = open("static/js/dashboard.js", encoding="utf-8").read()

    assert "Flask Route Tests" in script
    assert "Web Routes" in script
    assert "Show More v" not in script
    assert "Show Less ^" not in script


def test_valid_browser_login_renders_success_on_login(client):
    response = client.post(
        "/login",
        data={"username": "automation_user1", "password": "secret_pass123"},
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.request.path == "/login"
    assert "Location" not in response.headers
    assert "QA Lab" in body
    assert "QA Engineering Lab" not in body
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


def ai_report_index_payload():
    return {
        "report_version": "1.0",
        "reports": [
            {
                "pr_number": 42,
                "title": "Add AI report feed",
                "risk_level": "medium",
                "generated_at": "2026-08-25T12:00:00Z",
                "model": "gpt-5.6-terra",
                "prompt_version": "1.0",
                "report_path": "reports/pr-42.json",
            }
        ],
    }


def ai_report_payload():
    return {
        "report_version": "1.0",
        "prompt_version": "1.0",
        "generated_at": "2026-08-25T12:00:00Z",
        "model": "gpt-5.6-terra",
        "source": {"pr_number": 42, "pr_title": "Add AI report feed"},
        "change_summary": {"files_changed": 2, "additions": 30, "deletions": 5, "total_changes": 35},
        "analysis": {"risk_level": "medium"},
    }


def test_get_ai_report_index_returns_feed_result_without_openai_key(client, monkeypatch):
    payload = ai_report_index_payload()
    calls = []
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    def fetch(base_url):
        calls.append(base_url)
        return payload

    monkeypatch.setattr(app_module, "fetch_report_index", fetch)

    response = client.get("/api/ai-reports")

    assert response.status_code == 200
    assert response.get_json() == {
        "available": True,
        "source": "github_raw",
        "data": payload,
        "error": None,
    }
    assert calls == [app_module.app.config["AI_REPORT_FEED_BASE_URL"]]


def test_get_selected_ai_report_returns_feed_result(client, monkeypatch):
    payload = ai_report_payload()
    calls = []

    def fetch(pr_number, base_url):
        calls.append((pr_number, base_url))
        return payload

    monkeypatch.setattr(app_module, "fetch_ai_report", fetch)

    response = client.get("/api/ai-reports/42")

    assert response.status_code == 200
    assert response.get_json()["data"] == payload
    assert calls == [(42, app_module.app.config["AI_REPORT_FEED_BASE_URL"])]


def test_get_ai_report_index_returns_safe_unavailable_response(client, monkeypatch):
    def fail(_base_url):
        raise AIReportFeedError("feed_unavailable")

    monkeypatch.setattr(app_module, "fetch_report_index", fail)

    response = client.get("/api/ai-reports")

    assert response.status_code == 503
    assert response.get_json() == {
        "available": False,
        "source": "github_raw",
        "data": None,
        "error": {
            "code": "feed_unavailable",
            "message": "AI reports are not available yet.",
        },
    }


def test_get_missing_ai_report_returns_safe_not_found_response(client, monkeypatch):
    def fail(_pr_number, _base_url):
        raise AIReportFeedError("report_not_found")

    monkeypatch.setattr(app_module, "fetch_ai_report", fail)

    response = client.get("/api/ai-reports/42")

    assert response.status_code == 404
    assert response.get_json()["error"] == {
        "code": "report_not_found",
        "message": "The requested AI report was not found.",
    }


def test_get_malformed_ai_report_returns_safe_upstream_response(client, monkeypatch):
    def fail(_pr_number, _base_url):
        raise AIReportFeedError("invalid_report")

    monkeypatch.setattr(app_module, "fetch_ai_report", fail)

    response = client.get("/api/ai-reports/42")

    assert response.status_code == 502
    assert response.get_json()["error"] == {
        "code": "invalid_report",
        "message": "The AI report is not in a supported format.",
    }
