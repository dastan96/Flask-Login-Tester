from types import SimpleNamespace
from xml.etree import ElementTree

from scripts.normalize_test_results import ROUTE_TEST_IDS, normalize


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
        assert tests[friendly_name]["suite"] == "Web Routes"

    web_routes_suite = next(suite for suite in data["suites"] if suite["id"] == "flask_routes")
    assert web_routes_suite["name"] == "Web Routes"


def test_normalize_excludes_unknown_tests_from_public_feed():
    root = junit_for([
        ("tests.test_new_feature", "test_unknown_future_case"),
    ])

    data = normalize(root, args())

    assert data["total"] == 0
    assert data["tests"] == []
