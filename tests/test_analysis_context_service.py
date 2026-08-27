import json

import pytest

from services import analysis_context_service
from services.github_pr_service import GitHubPRServiceError


def sample_pull_request():
    return {
        "number": 42,
        "title": "Add QA analysis context",
        "description": "Combines deterministic QA data sources.",
        "state": "closed",
        "merged_at": "2026-08-22T16:30:00Z",
        "source_branch": "feature/analysis-context",
        "target_branch": "main",
        "commit_sha": "abc123",
        "github_url": "https://github.com/dastan96/Flask-Login-Tester/pull/42",
    }


def sample_changed_files():
    return [
        {
            "filename": "services/analysis_context_service.py",
            "status": "added",
            "additions": 18,
            "deletions": 0,
            "total_changes": 18,
            "patch": "@@ -0,0 +1,2 @@\n+def build_analysis_context():\n+    pass",
        },
        {
            "filename": "tests/test_analysis_context_service.py",
            "status": "added",
            "additions": 24,
            "deletions": 2,
            "total_changes": 26,
            "patch": "@@ -1 +1,2 @@\n-old\n+new\n+test",
        },
    ]


def sample_qa_context():
    return {
        "suites": [
            {
                "name": "Login API Tests",
                "test_type": "api",
                "source_files": ["tests/api/test_login_api.py"],
                "test_count": 1,
            }
        ],
        "tests": [
            {
                "test_id": "01.01",
                "title": "Login valid credentials",
                "suite": "Login API Tests",
                "test_type": "api",
                "source_file": "tests/api/test_login_api.py",
                "function_name": "test_api_01_01_login_valid_credentials",
            }
        ],
    }


def mock_context_sources(monkeypatch, pull_request, changed_files, qa_context):
    calls = []

    def get_pull_request(pr_number):
        calls.append(("pull_request", pr_number))
        return pull_request

    def get_pull_request_files(pr_number):
        calls.append(("changed_files", pr_number))
        return changed_files

    monkeypatch.setattr(
        analysis_context_service.github_pr_service,
        "get_pull_request",
        get_pull_request,
    )
    monkeypatch.setattr(
        analysis_context_service.github_pr_service,
        "get_pull_request_files",
        get_pull_request_files,
    )
    monkeypatch.setattr(
        analysis_context_service.qa_context_service,
        "build_qa_context",
        lambda: qa_context,
    )
    return calls


def test_build_analysis_context_combines_sources_and_aggregates_changes(monkeypatch):
    pull_request = sample_pull_request()
    changed_files = sample_changed_files()
    qa_context = sample_qa_context()
    calls = mock_context_sources(
        monkeypatch,
        pull_request,
        changed_files,
        qa_context,
    )

    context = analysis_context_service.build_analysis_context(42)

    assert context == {
        "pull_request": pull_request,
        "change_summary": {
            "files_changed": 2,
            "additions": 42,
            "deletions": 2,
            "total_changes": 44,
        },
        "changed_files": changed_files,
        "qa_context": qa_context,
    }
    assert context["changed_files"][0]["patch"] == changed_files[0]["patch"]
    assert calls == [("pull_request", 42), ("changed_files", 42)]
    assert json.loads(json.dumps(context)) == context


def test_empty_changed_files_produce_zero_summary(monkeypatch):
    mock_context_sources(
        monkeypatch,
        sample_pull_request(),
        [],
        sample_qa_context(),
    )

    context = analysis_context_service.build_analysis_context(42)

    assert context["change_summary"] == {
        "files_changed": 0,
        "additions": 0,
        "deletions": 0,
        "total_changes": 0,
    }
    assert context["changed_files"] == []


def test_github_service_error_is_not_swallowed(monkeypatch):
    failure = GitHubPRServiceError(
        "GitHub API request failed.",
        code="github_http_error",
        status_code=403,
    )

    def fail(_pr_number):
        raise failure

    monkeypatch.setattr(
        analysis_context_service.github_pr_service,
        "get_pull_request",
        fail,
    )

    with pytest.raises(GitHubPRServiceError) as error:
        analysis_context_service.build_analysis_context(42)

    assert error.value is failure
    assert error.value.code == "github_http_error"
    assert error.value.status_code == 403


def test_real_qa_context_combines_with_mocked_github_data(monkeypatch):
    pull_request = sample_pull_request()
    changed_files = sample_changed_files()
    monkeypatch.setattr(
        analysis_context_service.github_pr_service,
        "get_pull_request",
        lambda _pr_number: pull_request,
    )
    monkeypatch.setattr(
        analysis_context_service.github_pr_service,
        "get_pull_request_files",
        lambda _pr_number: changed_files,
    )

    context = analysis_context_service.build_analysis_context(42)
    suite_names = {suite["name"] for suite in context["qa_context"]["suites"]}

    assert {"Login API Tests", "Flask Route Tests", "UI Tests"}.issubset(suite_names)
    assert len(context["qa_context"]["tests"]) > 0
    assert context["changed_files"] == changed_files
