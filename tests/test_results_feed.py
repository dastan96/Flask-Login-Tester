import json
from pathlib import Path

import pytest
import requests

import app as app_module
from services import test_results_feed
from services.test_results_feed import FeedResult, fetch_latest_results


@pytest.fixture
def latest_payload():
    fixture_path = Path(__file__).parent / "fixtures" / "latest_results.json"
    return json.loads(fixture_path.read_text())


class MockResponse:
    def __init__(self, status_code=200, payload=None, json_error=None):
        self.status_code = status_code
        self.payload = payload
        self.json_error = json_error

    def json(self):
        if self.json_error:
            raise self.json_error
        return self.payload


def mock_get(monkeypatch, response=None, exception=None):
    calls = []

    def fake_get(url, timeout):
        calls.append({"url": url, "timeout": timeout})
        if exception:
            raise exception
        return response

    monkeypatch.setattr(test_results_feed.requests, "get", fake_get)
    return calls


def assert_unavailable(result, code):
    assert result.available is False
    assert result.data is None
    assert result.error == {
        "code": code,
        "message": test_results_feed.ERROR_MESSAGES[code],
    }


def test_fetch_latest_results_success(monkeypatch, latest_payload):
    calls = mock_get(monkeypatch, MockResponse(payload=latest_payload))

    result = fetch_latest_results("https://example.test/latest.json")

    assert result.available is True
    assert result.data == latest_payload
    assert result.error is None
    assert calls == [{"url": "https://example.test/latest.json", "timeout": 3}]


def test_fetch_latest_results_timeout(monkeypatch):
    mock_get(monkeypatch, exception=requests.Timeout())

    result = fetch_latest_results("https://example.test/latest.json")

    assert_unavailable(result, "timeout")


def test_fetch_latest_results_connection_error(monkeypatch):
    mock_get(monkeypatch, exception=requests.ConnectionError())

    result = fetch_latest_results("https://example.test/latest.json")

    assert_unavailable(result, "connection_error")


def test_fetch_latest_results_non_200_response(monkeypatch):
    mock_get(monkeypatch, MockResponse(status_code=500, payload={}))

    result = fetch_latest_results("https://example.test/latest.json")

    assert_unavailable(result, "upstream_http_error")


def test_fetch_latest_results_invalid_json(monkeypatch):
    mock_get(monkeypatch, MockResponse(json_error=ValueError("invalid json")))

    result = fetch_latest_results("https://example.test/latest.json")

    assert_unavailable(result, "invalid_json")


def test_fetch_latest_results_unsupported_schema(monkeypatch, latest_payload):
    latest_payload["schema_version"] = 2
    mock_get(monkeypatch, MockResponse(payload=latest_payload))

    result = fetch_latest_results("https://example.test/latest.json")

    assert_unavailable(result, "unsupported_schema")


def test_fetch_latest_results_missing_required_field(monkeypatch, latest_payload):
    latest_payload.pop("total")
    mock_get(monkeypatch, MockResponse(payload=latest_payload))

    result = fetch_latest_results("https://example.test/latest.json")

    assert_unavailable(result, "invalid_payload")


def test_fetch_latest_results_invalid_suites_type(monkeypatch, latest_payload):
    latest_payload["suites"] = {}
    mock_get(monkeypatch, MockResponse(payload=latest_payload))

    result = fetch_latest_results("https://example.test/latest.json")

    assert_unavailable(result, "invalid_payload")


def test_fetch_latest_results_invalid_tests_type(monkeypatch, latest_payload):
    latest_payload["tests"] = {}
    mock_get(monkeypatch, MockResponse(payload=latest_payload))

    result = fetch_latest_results("https://example.test/latest.json")

    assert_unavailable(result, "invalid_payload")


def test_fetch_latest_results_unsafe_workflow_url(monkeypatch, latest_payload):
    latest_payload["workflow_run_url"] = "https://evil.example/actions/runs/123"
    mock_get(monkeypatch, MockResponse(payload=latest_payload))

    result = fetch_latest_results("https://example.test/latest.json")

    assert_unavailable(result, "invalid_payload")


def test_fetch_latest_results_negative_count(monkeypatch, latest_payload):
    latest_payload["failed"] = -1
    latest_payload["total"] = latest_payload["passed"] + latest_payload["failed"] + latest_payload["skipped"]
    mock_get(monkeypatch, MockResponse(payload=latest_payload))

    result = fetch_latest_results("https://example.test/latest.json")

    assert_unavailable(result, "invalid_payload")


def test_fetch_latest_results_inconsistent_top_level_total(monkeypatch, latest_payload):
    latest_payload["total"] = 99
    mock_get(monkeypatch, MockResponse(payload=latest_payload))

    result = fetch_latest_results("https://example.test/latest.json")

    assert_unavailable(result, "invalid_payload")


def test_fetch_latest_results_inconsistent_suite_total(monkeypatch, latest_payload):
    latest_payload["suites"][0]["total"] = 99
    mock_get(monkeypatch, MockResponse(payload=latest_payload))

    result = fetch_latest_results("https://example.test/latest.json")

    assert_unavailable(result, "invalid_payload")


def test_fetch_latest_results_invalid_overall_status(monkeypatch, latest_payload):
    latest_payload["status"] = "unknown"
    mock_get(monkeypatch, MockResponse(payload=latest_payload))

    result = fetch_latest_results("https://example.test/latest.json")

    assert_unavailable(result, "invalid_payload")


def test_fetch_latest_results_invalid_test_status(monkeypatch, latest_payload):
    latest_payload["tests"][0]["status"] = "unknown"
    mock_get(monkeypatch, MockResponse(payload=latest_payload))

    result = fetch_latest_results("https://example.test/latest.json")

    assert_unavailable(result, "invalid_payload")


def test_latest_results_endpoint_success(client, monkeypatch, latest_payload):
    monkeypatch.setattr(
        app_module,
        "fetch_latest_results",
        lambda feed_url: FeedResult(available=True, data=latest_payload, error=None),
    )

    response = client.get("/api/test-results/latest")
    data = response.get_json()

    assert response.status_code == 200
    assert data["available"] is True
    assert data["source"] == "github_pages"
    assert data["results_page_url"] == "https://dastan96.github.io/Flask-Login-Tester/"
    assert data["data"] == latest_payload
    assert data["error"] is None


def test_latest_results_endpoint_unavailable(client, monkeypatch):
    error = test_results_feed.sanitized_error("timeout")
    monkeypatch.setattr(
        app_module,
        "fetch_latest_results",
        lambda feed_url: FeedResult(available=False, data=None, error=error),
    )

    response = client.get("/api/test-results/latest")
    data = response.get_json()

    assert response.status_code == 503
    assert data == {
        "available": False,
        "source": "github_pages",
        "results_page_url": "https://dastan96.github.io/Flask-Login-Tester/",
        "data": None,
        "error": error,
    }
