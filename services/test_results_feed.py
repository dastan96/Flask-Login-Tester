from dataclasses import dataclass

import requests


DEFAULT_TIMEOUT_SECONDS = 3
WORKFLOW_RUN_URL_PREFIX = "https://github.com/dastan96/Flask-Login-Tester/actions/"
OVERALL_STATUSES = {"passed", "failed"}
TEST_STATUSES = {"passed", "failed", "skipped"}

REQUIRED_TOP_LEVEL_FIELDS = {
    "schema_version",
    "status",
    "total",
    "passed",
    "failed",
    "skipped",
    "duration",
    "completed_at",
    "branch",
    "commit_sha",
    "trigger",
    "workflow_run_url",
    "suites",
    "tests",
}

REQUIRED_SUITE_FIELDS = {
    "name",
    "status",
    "total",
    "passed",
    "failed",
    "skipped",
    "duration",
}

REQUIRED_TEST_FIELDS = {
    "id",
    "name",
    "suite",
    "status",
    "duration",
}

ERROR_MESSAGES = {
    "timeout": "Latest test results are temporarily unavailable.",
    "connection_error": "Latest test results are temporarily unavailable.",
    "upstream_http_error": "Latest test results are temporarily unavailable.",
    "invalid_json": "Latest test results are temporarily unavailable.",
    "unsupported_schema": "Latest test results are not in a supported format.",
    "invalid_payload": "Latest test results are not in a supported format.",
}


@dataclass
class FeedResult:
    available: bool
    data: dict | None = None
    error: dict | None = None


def sanitized_error(code):
    return {
        "code": code,
        "message": ERROR_MESSAGES[code],
    }


def unavailable(code):
    return FeedResult(available=False, error=sanitized_error(code))


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def is_number(value):
    return (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool)


def valid_counts(data):
    counts = [data[field] for field in ("total", "passed", "failed", "skipped")]
    if not all(is_int(count) and count >= 0 for count in counts):
        return False
    return data["total"] == data["passed"] + data["failed"] + data["skipped"]


def valid_workflow_run_url(value):
    return value == "" or value.startswith(WORKFLOW_RUN_URL_PREFIX)


def has_required_fields(data, fields):
    return fields.issubset(data.keys())


def validate_suite(suite):
    if not isinstance(suite, dict):
        return False
    if not has_required_fields(suite, REQUIRED_SUITE_FIELDS):
        return False
    if not valid_counts(suite):
        return False
    if not is_number(suite["duration"]):
        return False
    if not isinstance(suite["name"], str):
        return False
    if suite["status"] not in OVERALL_STATUSES:
        return False
    return True


def validate_test(test):
    if not isinstance(test, dict):
        return False
    if not has_required_fields(test, REQUIRED_TEST_FIELDS):
        return False
    if test["id"] is not None and not isinstance(test["id"], str):
        return False
    if not isinstance(test["name"], str):
        return False
    if not isinstance(test["suite"], str):
        return False
    if test["status"] not in TEST_STATUSES:
        return False
    if not is_number(test["duration"]):
        return False
    return True


def validate_feed_payload(data):
    if not isinstance(data, dict):
        return "invalid_payload"
    if not has_required_fields(data, REQUIRED_TOP_LEVEL_FIELDS):
        return "invalid_payload"
    if data["schema_version"] != 1:
        return "unsupported_schema"
    if not valid_counts(data):
        return "invalid_payload"
    if not is_number(data["duration"]):
        return "invalid_payload"
    for field in ("status", "completed_at", "branch", "commit_sha", "trigger", "workflow_run_url"):
        if not isinstance(data[field], str):
            return "invalid_payload"
    if data["status"] not in OVERALL_STATUSES:
        return "invalid_payload"
    if not valid_workflow_run_url(data["workflow_run_url"]):
        return "invalid_payload"
    if not isinstance(data["suites"], list):
        return "invalid_payload"
    if not isinstance(data["tests"], list):
        return "invalid_payload"
    if not all(validate_suite(suite) for suite in data["suites"]):
        return "invalid_payload"
    if not all(validate_test(test) for test in data["tests"]):
        return "invalid_payload"
    return None


def fetch_latest_results(feed_url, timeout=DEFAULT_TIMEOUT_SECONDS):
    try:
        response = requests.get(feed_url, timeout=timeout)
    except requests.Timeout:
        return unavailable("timeout")
    except requests.ConnectionError:
        return unavailable("connection_error")
    except requests.RequestException:
        return unavailable("connection_error")

    if response.status_code != 200:
        return unavailable("upstream_http_error")

    try:
        data = response.json()
    except ValueError:
        return unavailable("invalid_json")

    error_code = validate_feed_payload(data)
    if error_code:
        return unavailable(error_code)

    return FeedResult(available=True, data=data, error=None)
