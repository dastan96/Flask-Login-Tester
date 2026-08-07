#!/usr/bin/env python3
import argparse
import html
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree


SUITE_DEFINITIONS = [
    {
        "id": "login_api",
        "name": "Login API",
        "module": "tests.api.test_login_api",
    },
    {
        "id": "flask_routes",
        "name": "Flask Routes",
        "module": "tests.test_routes",
    },
]

API_TEST_PATTERN = re.compile(r"^test_api_(\d{2})_(\d{2})_(.+)$")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Normalize pytest JUnit XML into a sanitized public results feed."
    )
    parser.add_argument("--junit", required=True, help="Path to pytest JUnit XML.")
    parser.add_argument("--out-dir", required=True, help="Directory for public output.")
    parser.add_argument("--branch", default="", help="Branch name to publish.")
    parser.add_argument("--commit-sha", default="", help="Commit SHA to publish.")
    parser.add_argument("--trigger", default="", help="Workflow trigger/event name.")
    parser.add_argument("--workflow-run-url", default="", help="GitHub Actions run URL.")
    return parser.parse_args()


def utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_junit(path):
    try:
        return ElementTree.parse(path).getroot()
    except (ElementTree.ParseError, OSError) as exc:
        raise SystemExit(f"Unable to read JUnit XML: {exc}") from exc


def as_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def collect_testcases(root):
    return list(root.iter("testcase"))


def total_duration(root, testcases):
    if root.tag == "testsuites":
        duration = as_float(root.attrib.get("time"))
        if duration:
            return duration

    if root.tag == "testsuite":
        duration = as_float(root.attrib.get("time"))
        if duration:
            return duration

    return sum(as_float(case.attrib.get("time")) for case in testcases)


def status_for_case(testcase):
    if testcase.find("skipped") is not None:
        return "skipped"
    if testcase.find("failure") is not None or testcase.find("error") is not None:
        return "failed"
    return "passed"


def suite_for_classname(classname):
    for suite in SUITE_DEFINITIONS:
        if classname == suite["module"] or classname.startswith(suite["module"] + "."):
            return suite
    return {
        "id": "other",
        "name": "Other",
        "module": "",
    }


def friendly_name_and_id(name):
    match = API_TEST_PATTERN.match(name)
    if match:
        return f"{match.group(1)}.{match.group(2)}", match.group(3)

    if name.startswith("test_"):
        return None, name[5:]

    return None, name


def summarize_suite(suite):
    total = suite["total"]
    failed = suite["failed"]
    skipped = suite["skipped"]
    passed = suite["passed"]
    status = "passed" if failed == 0 else "failed"
    return {
        "id": suite["id"],
        "name": suite["name"],
        "status": status,
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "duration": round(suite["duration"], 6),
    }


def normalize(root, args):
    testcases = collect_testcases(root)
    tests = []
    suite_totals = {
        suite["id"]: {
            "id": suite["id"],
            "name": suite["name"],
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "duration": 0.0,
        }
        for suite in SUITE_DEFINITIONS
    }

    for testcase in testcases:
        raw_name = testcase.attrib.get("name", "")
        classname = testcase.attrib.get("classname", "")
        suite = suite_for_classname(classname)
        test_id, friendly_name = friendly_name_and_id(raw_name)
        status = status_for_case(testcase)
        duration = as_float(testcase.attrib.get("time"))

        if suite["id"] not in suite_totals:
            suite_totals[suite["id"]] = {
                "id": suite["id"],
                "name": suite["name"],
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "duration": 0.0,
            }

        suite_summary = suite_totals[suite["id"]]
        suite_summary["total"] += 1
        suite_summary[status] += 1
        suite_summary["duration"] += duration

        tests.append({
            "id": test_id,
            "name": friendly_name,
            "suite": suite["name"],
            "status": status,
            "duration": round(duration, 6),
        })

    total = len(testcases)
    skipped = sum(1 for test in tests if test["status"] == "skipped")
    failed = sum(1 for test in tests if test["status"] == "failed")
    passed = sum(1 for test in tests if test["status"] == "passed")

    suites = [summarize_suite(suite_totals[suite["id"]]) for suite in SUITE_DEFINITIONS]
    for suite_id, suite in sorted(suite_totals.items()):
        if suite_id not in {definition["id"] for definition in SUITE_DEFINITIONS}:
            suites.append(summarize_suite(suite))

    return {
        "schema_version": 1,
        "status": "passed" if failed == 0 else "failed",
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "duration": round(total_duration(root, testcases), 6),
        "completed_at": utc_now_iso(),
        "branch": args.branch,
        "commit_sha": args.commit_sha,
        "trigger": args.trigger,
        "workflow_run_url": args.workflow_run_url,
        "suites": suites,
        "tests": tests,
    }


def clean_out_dir(path):
    path.mkdir(parents=True, exist_ok=True)
    for child in path.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def css_class(status):
    return "ok" if status == "passed" else "bad" if status == "failed" else "skip"


def render_index(data):
    status = html.escape(data["status"].upper())
    short_sha = data["commit_sha"][:7] if data["commit_sha"] else ""
    run_url = data.get("workflow_run_url", "")

    suite_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(suite['name'])}</td>"
        f"<td class=\"{css_class(suite['status'])}\">{html.escape(suite['status'])}</td>"
        f"<td>{suite['total']}</td>"
        f"<td>{suite['passed']}</td>"
        f"<td>{suite['failed']}</td>"
        f"<td>{suite['skipped']}</td>"
        f"<td>{suite['duration']:.3f}s</td>"
        "</tr>"
        for suite in data["suites"]
    )

    test_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(test['id'] or '')}</td>"
        f"<td>{html.escape(test['name'])}</td>"
        f"<td>{html.escape(test['suite'])}</td>"
        f"<td class=\"{css_class(test['status'])}\">{html.escape(test['status'])}</td>"
        f"<td>{test['duration']:.3f}s</td>"
        "</tr>"
        for test in data["tests"]
    )

    action_link = ""
    if run_url:
        escaped_url = html.escape(run_url, quote=True)
        action_link = f'<a href="{escaped_url}">View workflow run</a>'

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Flask Login Tester Results</title>
  <style>
    body {{
      color: #182026;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
      margin: 2rem auto;
      max-width: 1040px;
      padding: 0 1rem;
    }}
    h1, h2 {{ line-height: 1.2; }}
    .summary {{
      border: 1px solid #d8dee4;
      border-radius: 8px;
      display: grid;
      gap: 1rem;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      margin: 1.5rem 0;
      padding: 1rem;
    }}
    .label {{ color: #57606a; font-size: 0.85rem; }}
    .value {{ font-size: 1.2rem; font-weight: 700; }}
    .ok {{ color: #116329; font-weight: 700; }}
    .bad {{ color: #a40e26; font-weight: 700; }}
    .skip {{ color: #8a5a00; font-weight: 700; }}
    table {{ border-collapse: collapse; margin: 1rem 0 2rem; width: 100%; }}
    th, td {{ border-bottom: 1px solid #d8dee4; padding: 0.65rem; text-align: left; }}
    th {{ background: #f6f8fa; }}
  </style>
</head>
<body>
  <h1>Backend Test Results</h1>
  <div class="summary">
    <div><div class="label">Status</div><div class="value {css_class(data['status'])}">{status}</div></div>
    <div><div class="label">Total</div><div class="value">{data['total']}</div></div>
    <div><div class="label">Passed</div><div class="value">{data['passed']}</div></div>
    <div><div class="label">Failed</div><div class="value">{data['failed']}</div></div>
    <div><div class="label">Skipped</div><div class="value">{data['skipped']}</div></div>
    <div><div class="label">Duration</div><div class="value">{data['duration']:.3f}s</div></div>
  </div>
  <p>
    Completed at {html.escape(data['completed_at'])} on
    <strong>{html.escape(data['branch'])}</strong>
    commit <strong>{html.escape(short_sha)}</strong>.
    {action_link}
  </p>

  <h2>Suite Summary</h2>
  <table>
    <thead><tr><th>Suite</th><th>Status</th><th>Total</th><th>Passed</th><th>Failed</th><th>Skipped</th><th>Duration</th></tr></thead>
    <tbody>
{suite_rows}
    </tbody>
  </table>

  <h2>Tests</h2>
  <table>
    <thead><tr><th>ID</th><th>Name</th><th>Suite</th><th>Status</th><th>Duration</th></tr></thead>
    <tbody>
{test_rows}
    </tbody>
  </table>
</body>
</html>
"""


def main():
    args = parse_args()
    root = load_junit(args.junit)
    data = normalize(root, args)

    out_dir = Path(args.out_dir)
    clean_out_dir(out_dir)
    (out_dir / "latest.json").write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "index.html").write_text(render_index(data), encoding="utf-8")

    return 0


if __name__ == "__main__":
    sys.exit(main())
