import re

import requests


DEFAULT_AI_REPORT_BASE_URL = (
    "https://raw.githubusercontent.com/"
    "dastan96/Flask-Login-Tester/ai-reports/public/ai"
)
DEFAULT_TIMEOUT_SECONDS = 3
REQUEST_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Flask-Login-Tester",
}
SUPPORTED_REPORT_VERSION = "1.0"
REPORT_PATH_PATTERN = re.compile(r"^reports/pr-([1-9]\d*)\.json$")
RISK_LEVELS = {"low", "medium", "high"}

ERROR_MESSAGES = {
    "feed_unavailable": "AI reports are not available yet.",
    "upstream_http_error": "AI reports are temporarily unavailable.",
    "invalid_json": "AI report data is not in a supported format.",
    "invalid_index": "The AI report index is not in a supported format.",
    "invalid_report": "The AI report is not in a supported format.",
    "report_not_found": "The requested AI report was not found.",
}


class AIReportFeedError(Exception):
    def __init__(self, code):
        super().__init__(ERROR_MESSAGES[code])
        self.code = code
        self.public_message = ERROR_MESSAGES[code]


def _is_positive_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_string(value):
    return isinstance(value, str) and bool(value)


def _trusted_url(base_url, path):
    return f"{base_url.rstrip('/')}/{path}"


def _request_json(url, *, timeout, not_found_code):
    try:
        response = requests.get(
            url,
            headers=REQUEST_HEADERS,
            timeout=timeout,
        )
    except requests.RequestException as error:
        raise AIReportFeedError("feed_unavailable") from error

    if response.status_code == 404:
        raise AIReportFeedError(not_found_code)
    if response.status_code != 200:
        raise AIReportFeedError("upstream_http_error")

    try:
        return response.json()
    except ValueError as error:
        raise AIReportFeedError("invalid_json") from error


def _valid_index_entry(entry):
    if not isinstance(entry, dict):
        return False

    required_fields = {
        "pr_number",
        "title",
        "risk_level",
        "generated_at",
        "model",
        "prompt_version",
        "report_path",
    }
    if not required_fields.issubset(entry):
        return False

    pr_number = entry["pr_number"]
    if not _is_positive_int(pr_number):
        return False
    if not all(
        _is_string(entry[field])
        for field in ("title", "generated_at", "model", "prompt_version", "report_path")
    ):
        return False
    if entry["risk_level"] not in RISK_LEVELS:
        return False

    match = REPORT_PATH_PATTERN.fullmatch(entry["report_path"])
    return bool(match) and int(match.group(1)) == pr_number and entry["report_path"] == (
        f"reports/pr-{pr_number}.json"
    )


def _validate_index(data):
    if not isinstance(data, dict):
        return False
    if data.get("report_version") != SUPPORTED_REPORT_VERSION:
        return False
    reports = data.get("reports")
    if not isinstance(reports, list) or not all(_valid_index_entry(report) for report in reports):
        return False
    pr_numbers = [report["pr_number"] for report in reports]
    return len(pr_numbers) == len(set(pr_numbers))


def _valid_change_summary(summary):
    if not isinstance(summary, dict):
        return False
    required_fields = {"files_changed", "additions", "deletions", "total_changes"}
    if not required_fields.issubset(summary):
        return False
    return all(
        isinstance(summary[field], int)
        and not isinstance(summary[field], bool)
        and summary[field] >= 0
        for field in required_fields
    )


def _valid_changed_files(changed_files, summary):
    if not isinstance(changed_files, list):
        return False

    required_fields = {"filename", "status", "additions", "deletions", "total_changes"}
    for changed_file in changed_files:
        if not isinstance(changed_file, dict) or set(changed_file) != required_fields:
            return False
        if not _is_string(changed_file["filename"]) or not _is_string(changed_file["status"]):
            return False
        if not all(
            isinstance(changed_file[field], int)
            and not isinstance(changed_file[field], bool)
            and changed_file[field] >= 0
            for field in ("additions", "deletions", "total_changes")
        ):
            return False
        if changed_file["total_changes"] != (
            changed_file["additions"] + changed_file["deletions"]
        ):
            return False

    return (
        summary["files_changed"] == len(changed_files)
        and summary["additions"] == sum(item["additions"] for item in changed_files)
        and summary["deletions"] == sum(item["deletions"] for item in changed_files)
        and summary["total_changes"] == sum(item["total_changes"] for item in changed_files)
    )


def _validate_report(data, pr_number):
    if not isinstance(data, dict):
        return False
    required_fields = {
        "report_version",
        "prompt_version",
        "generated_at",
        "model",
        "source",
        "change_summary",
        "analysis",
    }
    if not required_fields.issubset(data):
        return False
    if data["report_version"] != SUPPORTED_REPORT_VERSION:
        return False
    if not all(_is_string(data[field]) for field in ("prompt_version", "generated_at", "model")):
        return False

    source = data["source"]
    if not isinstance(source, dict) or source.get("pr_number") != pr_number:
        return False
    source_fields = {"pr_title", "github_url", "merged_at", "commit_sha"}
    if not source_fields.issubset(source):
        return False
    if not all(_is_string(source[field]) for field in ("pr_title", "github_url", "commit_sha")):
        return False
    if source["merged_at"] is not None and not _is_string(source["merged_at"]):
        return False

    summary = data["change_summary"]
    if not _valid_change_summary(summary):
        return False
    if "changed_files" in data and not _valid_changed_files(data["changed_files"], summary):
        return False

    analysis = data["analysis"]
    if not isinstance(analysis, dict) or analysis.get("risk_level") not in RISK_LEVELS:
        return False
    return True


def fetch_report_index(base_url=DEFAULT_AI_REPORT_BASE_URL, timeout=DEFAULT_TIMEOUT_SECONDS):
    data = _request_json(
        _trusted_url(base_url, "index.json"),
        timeout=timeout,
        not_found_code="feed_unavailable",
    )
    if not _validate_index(data):
        raise AIReportFeedError("invalid_index")
    return data


def fetch_ai_report(
    pr_number,
    base_url=DEFAULT_AI_REPORT_BASE_URL,
    timeout=DEFAULT_TIMEOUT_SECONDS,
):
    if not _is_positive_int(pr_number):
        raise ValueError("pr_number must be a positive integer")

    data = _request_json(
        _trusted_url(base_url, f"reports/pr-{pr_number}.json"),
        timeout=timeout,
        not_found_code="report_not_found",
    )
    if not _validate_report(data, pr_number):
        raise AIReportFeedError("invalid_report")
    return data
