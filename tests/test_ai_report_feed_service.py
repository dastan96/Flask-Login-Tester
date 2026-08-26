import pytest
import requests

from services import ai_report_feed_service
from services.ai_report_feed_service import AIReportFeedError


BASE_URL = "https://reports.example.test/public/ai"


def valid_index():
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


def valid_report(pr_number=42):
    return {
        "report_version": "1.0",
        "prompt_version": "1.0",
        "generated_at": "2026-08-25T12:00:00Z",
        "model": "gpt-5.6-terra",
        "source": {
            "pr_number": pr_number,
            "pr_title": "Add AI report feed",
            "github_url": f"https://github.com/dastan96/Flask-Login-Tester/pull/{pr_number}",
            "merged_at": "2026-08-25T11:30:00Z",
            "commit_sha": "abc123",
        },
        "change_summary": {
            "files_changed": 2,
            "additions": 30,
            "deletions": 5,
            "total_changes": 35,
        },
        "analysis": {
            "prompt_version": "1.0",
            "risk_level": "medium",
            "change_summary": "Adds a read-only report feed.",
        },
    }


def valid_changed_files():
    return [
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
            "additions": 10,
            "deletions": 2,
            "total_changes": 12,
        },
    ]


class MockResponse:
    def __init__(self, payload=None, status_code=200, json_error=None):
        self.payload = payload
        self.status_code = status_code
        self.json_error = json_error

    def json(self):
        if self.json_error:
            raise self.json_error
        return self.payload


def mock_get(monkeypatch, response=None, exception=None):
    calls = []

    def fake_get(url, *, headers, timeout):
        calls.append({"url": url, "headers": headers, "timeout": timeout})
        if exception:
            raise exception
        return response

    monkeypatch.setattr(ai_report_feed_service.requests, "get", fake_get)
    return calls


def assert_feed_error(error, code):
    assert error.value.code == code
    assert str(error.value) == ai_report_feed_service.ERROR_MESSAGES[code]


def test_fetch_report_index_returns_validated_data_and_uses_trusted_url(monkeypatch):
    payload = valid_index()
    calls = mock_get(monkeypatch, MockResponse(payload))

    result = ai_report_feed_service.fetch_report_index(BASE_URL)

    assert result == payload
    assert calls == [
        {
            "url": f"{BASE_URL}/index.json",
            "headers": ai_report_feed_service.REQUEST_HEADERS,
            "timeout": 3,
        }
    ]


def test_fetch_ai_report_returns_validated_data_and_fixed_pr_url(monkeypatch):
    payload = valid_report()
    calls = mock_get(monkeypatch, MockResponse(payload))

    result = ai_report_feed_service.fetch_ai_report(42, f"{BASE_URL}/")

    assert result == payload
    assert calls[0]["url"] == f"{BASE_URL}/reports/pr-42.json"
    assert calls[0]["timeout"] == ai_report_feed_service.DEFAULT_TIMEOUT_SECONDS


def test_fetch_ai_report_accepts_optional_valid_changed_files(monkeypatch):
    payload = valid_report()
    payload["changed_files"] = valid_changed_files()
    mock_get(monkeypatch, MockResponse(payload))

    assert ai_report_feed_service.fetch_ai_report(42, BASE_URL) == payload


def test_fetch_ai_report_accepts_older_report_without_changed_files(monkeypatch):
    payload = valid_report()
    mock_get(monkeypatch, MockResponse(payload))

    assert "changed_files" not in ai_report_feed_service.fetch_ai_report(42, BASE_URL)


@pytest.mark.parametrize(
    "changed_files",
    [
        {},
        [{"filename": "app.py"}],
        [
            {
                "filename": "app.py",
                "status": "modified",
                "additions": 20,
                "deletions": 3,
                "total_changes": 99,
            }
        ],
        [
            {
                "filename": "app.py",
                "status": "modified",
                "additions": 20,
                "deletions": 3,
                "total_changes": 23,
                "patch": "must not be public metadata",
            },
            {
                "filename": "static/js/ai_assisted_qa.js",
                "status": "modified",
                "additions": 10,
                "deletions": 2,
                "total_changes": 12,
            },
        ],
    ],
)
def test_fetch_ai_report_rejects_invalid_changed_files(monkeypatch, changed_files):
    payload = valid_report()
    payload["changed_files"] = changed_files
    mock_get(monkeypatch, MockResponse(payload))

    with pytest.raises(AIReportFeedError) as error:
        ai_report_feed_service.fetch_ai_report(42, BASE_URL)

    assert_feed_error(error, "invalid_report")


@pytest.mark.parametrize(
    "report_path",
    [
        "../secrets.json",
        "https://evil.example/report.json",
        "/etc/passwd",
        "reports/pr-41.json",
        "reports/pr-042.json",
    ],
)
def test_fetch_report_index_rejects_unsafe_or_mismatched_paths(monkeypatch, report_path):
    payload = valid_index()
    payload["reports"][0]["report_path"] = report_path
    mock_get(monkeypatch, MockResponse(payload))

    with pytest.raises(AIReportFeedError) as error:
        ai_report_feed_service.fetch_report_index(BASE_URL)

    assert_feed_error(error, "invalid_index")


def test_fetch_ai_report_rejects_mismatched_source_pr_number(monkeypatch):
    mock_get(monkeypatch, MockResponse(valid_report(pr_number=41)))

    with pytest.raises(AIReportFeedError) as error:
        ai_report_feed_service.fetch_ai_report(42, BASE_URL)

    assert_feed_error(error, "invalid_report")


def test_invalid_json_produces_controlled_error(monkeypatch):
    mock_get(monkeypatch, MockResponse(json_error=ValueError("invalid JSON")))

    with pytest.raises(AIReportFeedError) as error:
        ai_report_feed_service.fetch_report_index(BASE_URL)

    assert_feed_error(error, "invalid_json")


@pytest.mark.parametrize("payload", [None, [], {}, {"report_version": "1.0", "reports": {}}])
def test_malformed_index_produces_controlled_error(monkeypatch, payload):
    mock_get(monkeypatch, MockResponse(payload))

    with pytest.raises(AIReportFeedError) as error:
        ai_report_feed_service.fetch_report_index(BASE_URL)

    assert_feed_error(error, "invalid_index")


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        {},
        {"report_version": "1.0", "source": {"pr_number": 42}},
    ],
)
def test_malformed_report_envelope_produces_controlled_error(monkeypatch, payload):
    mock_get(monkeypatch, MockResponse(payload))

    with pytest.raises(AIReportFeedError) as error:
        ai_report_feed_service.fetch_ai_report(42, BASE_URL)

    assert_feed_error(error, "invalid_report")


@pytest.mark.parametrize("exception", [requests.Timeout(), requests.ConnectionError()])
def test_network_failure_produces_controlled_error(monkeypatch, exception):
    mock_get(monkeypatch, exception=exception)

    with pytest.raises(AIReportFeedError) as error:
        ai_report_feed_service.fetch_report_index(BASE_URL)

    assert_feed_error(error, "feed_unavailable")


def test_upstream_http_error_produces_controlled_error(monkeypatch):
    mock_get(monkeypatch, MockResponse(status_code=500))

    with pytest.raises(AIReportFeedError) as error:
        ai_report_feed_service.fetch_report_index(BASE_URL)

    assert_feed_error(error, "upstream_http_error")


def test_missing_pr_report_is_distinguished(monkeypatch):
    mock_get(monkeypatch, MockResponse(status_code=404))

    with pytest.raises(AIReportFeedError) as error:
        ai_report_feed_service.fetch_ai_report(42, BASE_URL)

    assert_feed_error(error, "report_not_found")


def test_missing_index_is_treated_as_unavailable_first_run(monkeypatch):
    mock_get(monkeypatch, MockResponse(status_code=404))

    with pytest.raises(AIReportFeedError) as error:
        ai_report_feed_service.fetch_report_index(BASE_URL)

    assert_feed_error(error, "feed_unavailable")


@pytest.mark.parametrize("pr_number", [0, -1, True, "42"])
def test_fetch_ai_report_rejects_invalid_pr_number(pr_number):
    with pytest.raises(ValueError, match="positive integer"):
        ai_report_feed_service.fetch_ai_report(pr_number, BASE_URL)
