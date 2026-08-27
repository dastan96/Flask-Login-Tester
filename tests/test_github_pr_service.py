import pytest
import requests

from services import github_pr_service
from services.github_pr_service import GitHubPRServiceError


class MockResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)

    def json(self):
        return self.payload


def pull_request_payload(**overrides):
    payload = {
        "number": 42,
        "title": "Add login API coverage",
        "body": "Adds positive and negative login scenarios.",
        "state": "closed",
        "merged_at": "2026-08-20T14:30:00Z",
        "head": {"ref": "feature/login-api-tests", "sha": "head123"},
        "base": {"ref": "main"},
        "merge_commit_sha": "merge456",
        "html_url": "https://github.com/dastan96/Flask-Login-Tester/pull/42",
    }
    payload.update(overrides)
    return payload


def mock_get(monkeypatch, responses):
    calls = []
    queued_responses = iter(responses)

    def fake_get(url, *, headers, params, timeout):
        calls.append(
            {
                "url": url,
                "headers": headers,
                "params": params,
                "timeout": timeout,
            }
        )
        response = next(queued_responses)
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(github_pr_service.requests, "get", fake_get)
    return calls


def test_list_recent_pull_requests_normalizes_data_and_prefers_merged(monkeypatch):
    closed_pr = pull_request_payload(
        number=41,
        title="Closed without merge",
        merged_at=None,
        html_url="https://github.com/dastan96/Flask-Login-Tester/pull/41",
    )
    merged_pr = pull_request_payload()
    calls = mock_get(monkeypatch, [MockResponse([closed_pr, merged_pr])])

    result = github_pr_service.list_recent_pull_requests(limit=1)

    assert result == [
        {
            "number": 42,
            "title": "Add login API coverage",
            "state": "closed",
            "merged_at": "2026-08-20T14:30:00Z",
            "source_branch": "feature/login-api-tests",
            "target_branch": "main",
            "github_url": "https://github.com/dastan96/Flask-Login-Tester/pull/42",
        },
    ]
    assert calls[0]["params"] == {
        "state": "closed",
        "sort": "updated",
        "direction": "desc",
        "per_page": 30,
    }
    assert calls[0]["headers"] == github_pr_service.GITHUB_HEADERS
    assert calls[0]["timeout"] == github_pr_service.DEFAULT_TIMEOUT_SECONDS


def test_get_pull_request_normalizes_analysis_fields(monkeypatch):
    mock_get(monkeypatch, [MockResponse(pull_request_payload())])

    result = github_pr_service.get_pull_request(42)

    assert result == {
        "number": 42,
        "title": "Add login API coverage",
        "description": "Adds positive and negative login scenarios.",
        "state": "closed",
        "merged_at": "2026-08-20T14:30:00Z",
        "source_branch": "feature/login-api-tests",
        "target_branch": "main",
        "commit_sha": "merge456",
        "github_url": "https://github.com/dastan96/Flask-Login-Tester/pull/42",
    }


def test_get_pull_request_files_normalizes_and_preserves_patch(monkeypatch):
    patch = "@@ -1,2 +1,3 @@\n existing\n+new assertion"
    payload = [
        {
            "filename": "tests/test_login.py",
            "status": "modified",
            "additions": 8,
            "deletions": 2,
            "changes": 10,
            "patch": patch,
        }
    ]
    calls = mock_get(monkeypatch, [MockResponse(payload)])

    result = github_pr_service.get_pull_request_files(42)

    assert result == [
        {
            "filename": "tests/test_login.py",
            "status": "modified",
            "additions": 8,
            "deletions": 2,
            "total_changes": 10,
            "patch": patch,
        }
    ]
    assert calls[0]["params"] == {"per_page": 100, "page": 1}


def test_get_pull_request_files_fetches_all_pages(monkeypatch):
    first_page = [
        {
            "filename": f"tests/generated/test_{index}.py",
            "status": "added",
            "additions": 1,
            "deletions": 0,
            "changes": 1,
            "patch": f"@@ -0,0 +1 @@\n+case {index}",
        }
        for index in range(100)
    ]
    second_page_patch = "@@ -1 +1 @@\n-old value\n+new value"
    second_page = [
        {
            "filename": "services/final_file.py",
            "status": "modified",
            "additions": 1,
            "deletions": 1,
            "changes": 2,
            "patch": second_page_patch,
        }
    ]
    calls = mock_get(
        monkeypatch,
        [MockResponse(first_page), MockResponse(second_page)],
    )

    result = github_pr_service.get_pull_request_files(42)

    assert len(result) == 101
    assert [item["filename"] for item in result[:100]] == [
        f"tests/generated/test_{index}.py" for index in range(100)
    ]
    assert result[-1] == {
        "filename": "services/final_file.py",
        "status": "modified",
        "additions": 1,
        "deletions": 1,
        "total_changes": 2,
        "patch": second_page_patch,
    }
    assert [call["params"] for call in calls] == [
        {"per_page": 100, "page": 1},
        {"per_page": 100, "page": 2},
    ]


def test_github_http_error_raises_service_error(monkeypatch):
    mock_get(monkeypatch, [MockResponse({}, status_code=403)])

    with pytest.raises(GitHubPRServiceError) as error:
        github_pr_service.get_pull_request(42)

    assert error.value.code == "github_http_error"
    assert error.value.status_code == 403


def test_request_failure_raises_service_error(monkeypatch):
    mock_get(monkeypatch, [requests.ConnectionError("network unavailable")])

    with pytest.raises(GitHubPRServiceError) as error:
        github_pr_service.list_recent_pull_requests()

    assert error.value.code == "request_failed"
    assert error.value.status_code is None


def test_malformed_response_raises_service_error(monkeypatch):
    mock_get(monkeypatch, [MockResponse({"unexpected": "object"})])

    with pytest.raises(GitHubPRServiceError) as error:
        github_pr_service.list_recent_pull_requests()

    assert error.value.code == "invalid_response"
