import json
import re

from playwright.sync_api import Page, expect


VALID_USERNAME = "automation_user1"
VALID_PASSWORD = "secret_pass123"


def open_login_page(page: Page, login_ui_base_url: str):
    page.goto(f"{login_ui_base_url}/login")


def username_field(page: Page):
    return page.get_by_label("Username")


def password_field(page: Page):
    return page.get_by_label("Password")


def login_button(page: Page):
    return page.get_by_role("button", name="Login")


def test_ui_01_login_page_loads(page: Page, login_ui_base_url: str):
    open_login_page(page, login_ui_base_url)

    expect(page.get_by_role("heading", name="QA Lab")).to_be_visible()
    expect(username_field(page)).to_be_visible()
    expect(password_field(page)).to_be_visible()
    expect(login_button(page)).to_be_visible()
    expect(login_button(page)).to_be_enabled()


def test_ui_02_valid_login_shows_success(page: Page, login_ui_base_url: str):
    open_login_page(page, login_ui_base_url)

    username_field(page).fill(VALID_USERNAME)
    password_field(page).fill(VALID_PASSWORD)
    login_button(page).click()

    expect(page).to_have_url(f"{login_ui_base_url}/login")
    expect(page.get_by_role("status")).to_contain_text("Login successful")


def test_ui_03_invalid_credentials_show_error(page: Page, login_ui_base_url: str):
    open_login_page(page, login_ui_base_url)

    username_field(page).fill(VALID_USERNAME)
    password_field(page).fill("wrong_password")
    login_button(page).click()

    expect(page).to_have_url(f"{login_ui_base_url}/login")
    expect(page.get_by_role("alert")).to_contain_text("Invalid credentials. Try again.")


def test_ui_04_missing_username_required_validation(page: Page, login_ui_base_url: str):
    open_login_page(page, login_ui_base_url)

    password_field(page).fill(VALID_PASSWORD)
    login_button(page).click()

    username = username_field(page)
    assert username.evaluate("element => !element.validity.valid")
    assert username.evaluate("element => element.validationMessage") != ""
    expect(page.get_by_role("status")).not_to_be_visible()
    expect(page).to_have_url(f"{login_ui_base_url}/login")


def test_ui_05_missing_password_required_validation(page: Page, login_ui_base_url: str):
    open_login_page(page, login_ui_base_url)

    username_field(page).fill(VALID_USERNAME)
    login_button(page).click()

    password = password_field(page)
    assert password.evaluate("element => !element.validity.valid")
    assert password.evaluate("element => element.validationMessage") != ""
    expect(page.get_by_role("status")).not_to_be_visible()
    expect(page).to_have_url(f"{login_ui_base_url}/login")


def ai_report_index_response():
    return {
        "available": True,
        "source": "github_raw",
        "data": {
            "report_version": "1.0",
            "reports": [
                {
                    "pr_number": 42,
                    "title": "Add persisted AI reports",
                    "risk_level": "medium",
                    "generated_at": "2026-08-25T12:00:00Z",
                    "model": "test-model-2026",
                    "prompt_version": "1.0",
                    "report_path": "reports/pr-42.json",
                },
                {
                    "pr_number": 41,
                    "title": "Older report without file details",
                    "risk_level": "low",
                    "generated_at": "2026-08-24T12:00:00Z",
                    "model": "test-model-2026",
                    "prompt_version": "1.0",
                    "report_path": "reports/pr-41.json",
                }
            ],
        },
        "error": None,
    }


def ai_report_detail_response(pr_number=42, include_changed_files=True):
    response = {
        "available": True,
        "source": "github_raw",
        "data": {
            "report_version": "1.0",
            "prompt_version": "1.0",
            "generated_at": "2026-08-25T12:00:00Z",
            "model": "test-model-2026",
            "source": {
                "pr_number": pr_number,
                "pr_title": (
                    "Add persisted AI reports"
                    if pr_number == 42
                    else "Older report without file details"
                ),
                "github_url": f"https://github.com/dastan96/Flask-Login-Tester/pull/{pr_number}",
                "merged_at": "2026-08-25T11:30:00Z",
                "commit_sha": "abc1234567890def",
            },
            "change_summary": {
                "files_changed": 3,
                "additions": 48,
                "deletions": 7,
                "total_changes": 55,
            },
            "analysis": {
                "prompt_version": "1.0",
                "risk_level": "medium",
                "change_summary": "Adds persisted AI report retrieval and safe rendering.",
                "risk_rationale": "The change adds a new public read-only reporting surface.",
                "affected_areas": [
                    {
                        "area": "AI report presentation",
                        "evidence": "A new persisted report explorer renders structured analysis.",
                    },
                    {
                        "area": "Report navigation",
                        "evidence": "The review uses accessible tabs for detailed analysis.",
                    }
                ],
                "relevant_existing_tests": [
                    {
                        "test_id": "02.01",
                        "title": "Dashboard renders at root route",
                        "reason": "It establishes the public-page rendering pattern.",
                    }
                ],
                "coverage_gaps": [
                    {
                        "area": "Unavailable report state",
                        "reason": "The new asynchronous failure path needs browser coverage.",
                    },
                    {
                        "area": "Long report summaries",
                        "reason": "Expanded summary behavior should remain readable.",
                    }
                ],
                "recommended_tests": [
                    {
                        "priority": "high",
                        "test_type": "ui",
                        "title": "Verify persisted report rendering",
                        "rationale": "Confirms users can review the newest analysis without triggering generation.",
                    }
                ],
                "qa_notes": ["Review recommendations alongside deterministic test results."],
                "analysis_limitations": ["The analysis uses only the supplied Pull Request evidence."],
            },
        },
        "error": None,
    }
    if include_changed_files:
        response["data"]["changed_files"] = [
            {
                "filename": "app.py",
                "status": "modified",
                "additions": 20,
                "deletions": 3,
                "total_changes": 23,
            },
            {
                "filename": "static/js/ai_assisted_qa.js",
                "status": "modified",
                "additions": 18,
                "deletions": 2,
                "total_changes": 20,
            },
            {
                "filename": "templates/ai_assisted_qa.html",
                "status": "modified",
                "additions": 10,
                "deletions": 2,
                "total_changes": 12,
            },
        ]
    return response


def fulfill_json(route, payload, status=200):
    route.fulfill(
        status=status,
        content_type="application/json",
        body=json.dumps(payload),
    )


def test_ui_06_ai_assisted_qa_renders_available_report(page: Page, login_ui_base_url: str):
    page.route(
        re.compile(r".*/api/ai-reports$"),
        lambda route: fulfill_json(route, ai_report_index_response()),
    )
    page.route(
        re.compile(r".*/api/ai-reports/42$"),
        lambda route: fulfill_json(route, ai_report_detail_response()),
    )
    page.route(
        re.compile(r".*/api/ai-reports/41$"),
        lambda route: fulfill_json(
            route,
            ai_report_detail_response(pr_number=41, include_changed_files=False),
        ),
    )

    page.goto(f"{login_ui_base_url}/ai")

    selector = page.get_by_label("Pull Request report")
    expect(selector).to_have_value("42")
    expect(selector).to_contain_text("PR #42 — Add persisted AI reports")
    expect(page.get_by_role("heading", name="Add persisted AI reports")).to_be_visible()
    expect(page.get_by_text("MEDIUM RISK", exact=True)).to_be_visible()
    expect(page.get_by_text("+48", exact=True)).to_be_visible()
    expect(page.get_by_role("tab", name="Overview")).to_have_attribute("aria-selected", "true")
    expect(page.get_by_text("Adds persisted AI report retrieval and safe rendering.", exact=True)).to_be_visible()
    overview = page.get_by_role("tabpanel", name="Overview")
    expect(overview.get_by_role("article")).to_have_count(3)
    expect(overview.get_by_role("heading", name="Unavailable report state")).to_be_visible()
    expect(page.get_by_text("app.py", exact=True)).to_be_visible()
    expect(page.get_by_role("link", name="View Pull Request 42 on GitHub").first).to_be_visible()
    expect(
        page.get_by_role("link", name="View raw AI-assisted QA report for Pull Request 42").first
    ).to_be_visible()

    page.get_by_role("tab", name="Findings").click()
    expect(page.get_by_role("heading", name="Affected Areas")).to_be_visible()
    expect(page.get_by_text("Potential Coverage Gap", exact=True).first).to_be_visible()

    page.get_by_role("tab", name="Test Impact").click()
    expect(page.get_by_text("02.01", exact=True)).to_be_visible()
    expect(page.get_by_role("heading", name="Dashboard renders at root route")).to_be_visible()
    expect(page.get_by_text("It establishes the public-page rendering pattern.", exact=True)).to_be_visible()
    expect(page.get_by_text("HIGH · UI", exact=True)).to_be_visible()
    expect(page.get_by_text("Recommended Test", exact=True)).to_be_visible()
    expect(page.get_by_text("Verify persisted report rendering", exact=True)).to_be_visible()

    page.get_by_role("tab", name="Details").click()
    expect(page.get_by_text("test-model-2026", exact=True)).to_be_visible()

    selector.select_option("41")
    expect(page.get_by_role("heading", name="Older report without file details")).to_be_visible()
    expect(
        page.get_by_text("Per-file change details are not available for this older report.", exact=True)
    ).to_be_visible()
    expect(page.get_by_text("3", exact=True).first).to_be_visible()


def test_ui_07_ai_assisted_qa_handles_unavailable_reports(page: Page, login_ui_base_url: str):
    unavailable = {
        "available": False,
        "source": "github_raw",
        "data": None,
        "error": {
            "code": "feed_unavailable",
            "message": "AI reports are not available yet.",
        },
    }
    page.route(
        re.compile(r".*/api/ai-reports$"),
        lambda route: fulfill_json(route, unavailable, status=503),
    )

    page.goto(f"{login_ui_base_url}/ai")

    expect(page.get_by_text("AI reports are not available yet.", exact=True)).to_be_visible()
    expect(page.get_by_role("heading", name="Loading AI analysis")).not_to_be_visible()
    expect(page.get_by_role("heading", name="Change Summary")).not_to_be_visible()
