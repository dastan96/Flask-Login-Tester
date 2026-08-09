from types import SimpleNamespace
from xml.etree import ElementTree

from scripts.normalize_test_results import ROUTE_TEST_IDS, normalize, render_index


def args():
    return SimpleNamespace(
        branch="local",
        commit_sha="local",
        trigger="local",
        workflow_run_url="",
    )


def junit_for(testcases):
    testcases = list(testcases)
    body = "\n".join(
        f'<testcase classname="{classname}" name="{name}" time="0.001" />'
        for classname, name in testcases
    )
    return ElementTree.fromstring(f'<testsuite tests="{len(testcases)}" time="0.001">{body}</testsuite>')


def by_name(data):
    return {test["name"]: test for test in data["tests"]}


def test_normalize_preserves_login_api_ids():
    root = junit_for([
        ("tests.api.test_login_api", "test_api_01_01_login_valid_credentials"),
        ("tests.api.test_login_api", "test_api_01_10_login_empty_json_object"),
    ])

    data = normalize(root, args())

    tests = by_name(data)
    assert tests["login_valid_credentials"]["id"] == "01.01"
    assert tests["login_empty_json_object"]["id"] == "01.10"


def test_normalize_assigns_stable_flask_route_ids():
    root = junit_for(("tests.test_routes", name) for name in ROUTE_TEST_IDS)

    data = normalize(root, args())

    tests = by_name(data)
    for raw_name, expected_id in ROUTE_TEST_IDS.items():
        friendly_name = raw_name[5:]
        assert tests[friendly_name]["id"] == expected_id
        assert tests[friendly_name]["suite"] == "Flask Route Tests"

    web_routes_suite = next(suite for suite in data["suites"] if suite["id"] == "flask_routes")
    assert web_routes_suite["name"] == "Flask Route Tests"
    assert web_routes_suite["total"] == 11


def test_normalize_assigns_continuous_web_route_ids_without_blanks():
    root = junit_for(("tests.test_routes", name) for name in ROUTE_TEST_IDS)

    data = normalize(root, args())

    web_route_ids = [
        test["id"]
        for test in data["tests"]
        if test["suite"] == "Flask Route Tests"
    ]
    assert web_route_ids == [f"02.{number:02d}" for number in range(1, 12)]
    assert None not in web_route_ids
    assert "" not in web_route_ids


def test_normalize_assigns_stable_ui_test_ids_and_suite_totals():
    ui_test_names = [
        "test_ui_01_login_page_loads",
        "test_ui_02_valid_login_shows_success",
        "test_ui_03_invalid_credentials_show_error",
        "test_ui_04_missing_username_required_validation",
        "test_ui_05_missing_password_required_validation",
    ]
    root = junit_for(("tests.ui.test_login_ui", name) for name in ui_test_names)

    data = normalize(root, args())

    tests = by_name(data)
    assert tests["login_page_loads"]["suite"] == "UI Tests"
    assert tests["valid_login_shows_success"]["suite"] == "UI Tests"

    ui_ids = [
        test["id"]
        for test in data["tests"]
        if test["suite"] == "UI Tests"
    ]
    assert ui_ids == [f"03.{number:02d}" for number in range(1, 6)]
    assert None not in ui_ids
    assert "" not in ui_ids

    ui_suite = next(suite for suite in data["suites"] if suite["id"] == "ui_tests")
    assert ui_suite["name"] == "UI Tests"
    assert ui_suite["total"] == 5
    assert ui_suite["passed"] == 5
    assert ui_suite["failed"] == 0
    assert ui_suite["skipped"] == 0


def test_normalize_aggregates_multiple_junit_roots():
    backend_root = junit_for([
        ("tests.api.test_login_api", "test_api_01_01_login_valid_credentials"),
        ("tests.test_routes", "test_get_root_renders_dashboard"),
    ])
    ui_root = junit_for([
        ("tests.ui.test_login_ui", "test_ui_01_login_page_loads"),
        ("tests.ui.test_login_ui", "test_ui_02_valid_login_shows_success"),
    ])

    data = normalize([backend_root, ui_root], args())

    assert data["total"] == 4
    assert data["passed"] == 4
    assert data["failed"] == 0
    assert data["skipped"] == 0
    assert data["status"] == "passed"
    assert [suite["name"] for suite in data["suites"]] == [
        "Login API",
        "UI Tests",
        "Flask Route Tests",
    ]


def test_normalize_public_ids_are_not_blank():
    roots = [
        junit_for([
            ("tests.api.test_login_api", "test_api_01_01_login_valid_credentials"),
            ("tests.api.test_login_api", "test_api_01_10_login_empty_json_object"),
        ]),
        junit_for(("tests.test_routes", name) for name in ROUTE_TEST_IDS),
        junit_for([
            ("tests.ui.test_login_ui", "test_ui_01_login_page_loads"),
            ("tests.ui.test_login_ui", "test_ui_05_missing_password_required_validation"),
        ]),
    ]

    data = normalize(roots, args())

    assert all(test["id"] for test in data["tests"])


def test_normalize_excludes_unmapped_tests_from_public_modules():
    root = junit_for([
        ("tests.test_routes", "test_dashboard_js_accepts_legacy_web_routes_alias"),
    ])

    data = normalize(root, args())

    assert data["total"] == 0
    assert data["tests"] == []
    flask_routes_suite = next(suite for suite in data["suites"] if suite["id"] == "flask_routes")
    assert flask_routes_suite["total"] == 0


def test_render_index_uses_automated_results_heading():
    root = junit_for([
        ("tests.api.test_login_api", "test_api_01_01_login_valid_credentials"),
    ])
    data = normalize(root, args())

    html = render_index(data)

    assert "Latest Automated Test Results" in html
    assert "Backend Test Results" not in html


def test_normalize_excludes_unknown_tests_from_public_feed():
    root = junit_for([
        ("tests.test_new_feature", "test_unknown_future_case"),
    ])

    data = normalize(root, args())

    assert data["total"] == 0
    assert data["tests"] == []
