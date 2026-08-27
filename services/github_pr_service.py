from collections.abc import Mapping

import requests


GITHUB_API_URL = "https://api.github.com"
REPOSITORY = "dastan96/Flask-Login-Tester"
DEFAULT_TIMEOUT_SECONDS = 5
GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "Flask-Login-Tester",
}


class GitHubPRServiceError(Exception):
    def __init__(self, message, *, code, status_code=None):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


def _invalid_response():
    return GitHubPRServiceError(
        "GitHub API returned an invalid response.",
        code="invalid_response",
    )


def _request_json(path, *, params=None):
    try:
        response = requests.get(
            f"{GITHUB_API_URL}{path}",
            headers=GITHUB_HEADERS,
            params=params,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.HTTPError as error:
        status_code = error.response.status_code if error.response is not None else None
        raise GitHubPRServiceError(
            "GitHub API request failed.",
            code="github_http_error",
            status_code=status_code,
        ) from error
    except requests.RequestException as error:
        raise GitHubPRServiceError(
            "Unable to reach the GitHub API.",
            code="request_failed",
        ) from error

    try:
        return response.json()
    except (TypeError, ValueError) as error:
        raise _invalid_response() from error


def _required(item, key, expected_type):
    if key not in item or not isinstance(item[key], expected_type):
        raise _invalid_response()
    return item[key]


def _optional_string(item, key):
    value = item.get(key)
    if value is not None and not isinstance(value, str):
        raise _invalid_response()
    return value


def _branch(item, key):
    branch = _required(item, key, Mapping)
    return _required(branch, "ref", str)


def _normalize_pull_request(item, *, include_details=False):
    if not isinstance(item, Mapping):
        raise _invalid_response()

    normalized = {
        "number": _required(item, "number", int),
        "title": _required(item, "title", str),
        "state": _required(item, "state", str),
        "merged_at": _optional_string(item, "merged_at"),
        "source_branch": _branch(item, "head"),
        "target_branch": _branch(item, "base"),
        "github_url": _required(item, "html_url", str),
    }

    if include_details:
        head = _required(item, "head", Mapping)
        merge_commit_sha = _optional_string(item, "merge_commit_sha")
        normalized.update(
            {
                "description": _optional_string(item, "body"),
                "commit_sha": merge_commit_sha or _required(head, "sha", str),
            }
        )

    return normalized


def _normalize_file(item):
    if not isinstance(item, Mapping):
        raise _invalid_response()

    return {
        "filename": _required(item, "filename", str),
        "status": _required(item, "status", str),
        "additions": _required(item, "additions", int),
        "deletions": _required(item, "deletions", int),
        "total_changes": _required(item, "changes", int),
        "patch": _optional_string(item, "patch"),
    }


def list_recent_pull_requests(limit=5):
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer between 1 and 100")

    candidate_count = min(max(limit * 3, 30), 100)
    data = _request_json(
        f"/repos/{REPOSITORY}/pulls",
        params={
            "state": "closed",
            "sort": "updated",
            "direction": "desc",
            "per_page": candidate_count,
        },
    )
    if not isinstance(data, list):
        raise _invalid_response()

    pull_requests = [_normalize_pull_request(item) for item in data]
    return sorted(pull_requests, key=lambda item: item["merged_at"] is None)[:limit]


def get_pull_request(pr_number):
    if not isinstance(pr_number, int) or isinstance(pr_number, bool) or pr_number <= 0:
        raise ValueError("pr_number must be a positive integer")

    data = _request_json(f"/repos/{REPOSITORY}/pulls/{pr_number}")
    return _normalize_pull_request(data, include_details=True)


def get_pull_request_files(pr_number):
    if not isinstance(pr_number, int) or isinstance(pr_number, bool) or pr_number <= 0:
        raise ValueError("pr_number must be a positive integer")

    files = []
    page = 1
    while True:
        data = _request_json(
            f"/repos/{REPOSITORY}/pulls/{pr_number}/files",
            params={"per_page": 100, "page": page},
        )
        if not isinstance(data, list):
            raise _invalid_response()

        files.extend(_normalize_file(item) for item in data)
        if len(data) < 100:
            return files
        page += 1
