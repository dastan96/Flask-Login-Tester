from pathlib import Path

from services.qa_context_service import build_qa_context


def write_test_file(tests_dir, relative_path, source):
    path = tests_dir / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


def test_discovers_and_normalizes_product_test_categories(tmp_path):
    tests_dir = tmp_path / "tests"
    write_test_file(
        tests_dir,
        Path("api/test_login_api.py"),
        """
def test_api_01_03_login_wrong_password():
    pass
""",
    )
    write_test_file(
        tests_dir,
        Path("test_routes.py"),
        """
def test_get_root_renders_dashboard():
    pass
""",
    )
    write_test_file(
        tests_dir,
        Path("ui/test_login_ui.py"),
        """
def test_ui_04_missing_username_required_validation():
    pass
""",
    )

    context = build_qa_context(tests_dir)

    assert context["tests"] == [
        {
            "test_id": "01.03",
            "title": "Login wrong password",
            "suite": "Login API Tests",
            "test_type": "api",
            "source_file": "tests/api/test_login_api.py",
            "function_name": "test_api_01_03_login_wrong_password",
        },
        {
            "test_id": None,
            "title": "Get root renders dashboard",
            "suite": "Flask Route Tests",
            "test_type": "route",
            "source_file": "tests/test_routes.py",
            "function_name": "test_get_root_renders_dashboard",
        },
        {
            "test_id": "03.04",
            "title": "Missing username required validation",
            "suite": "UI Tests",
            "test_type": "ui",
            "source_file": "tests/ui/test_login_ui.py",
            "function_name": "test_ui_04_missing_username_required_validation",
        },
    ]
    assert context["suites"] == [
        {
            "name": "Login API Tests",
            "test_type": "api",
            "source_files": ["tests/api/test_login_api.py"],
            "test_count": 1,
        },
        {
            "name": "Flask Route Tests",
            "test_type": "route",
            "source_files": ["tests/test_routes.py"],
            "test_count": 1,
        },
        {
            "name": "UI Tests",
            "test_type": "ui",
            "source_files": ["tests/ui/test_login_ui.py"],
            "test_count": 1,
        },
    ]


def test_excludes_infrastructure_service_tests(tmp_path):
    tests_dir = tmp_path / "tests"
    write_test_file(
        tests_dir,
        Path("test_github_pr_service.py"),
        """
def test_get_pull_request_normalizes_analysis_fields():
    pass
""",
    )
    write_test_file(
        tests_dir,
        Path("test_results_feed.py"),
        """
def test_fetch_latest_results_success():
    pass
""",
    )

    assert build_qa_context(tests_dir) == {"suites": [], "tests": []}


def test_nonconforming_product_test_is_safe_and_has_no_id(tmp_path):
    tests_dir = tmp_path / "tests"
    write_test_file(
        tests_dir,
        Path("api/test_login_api.py"),
        """
def test_unexpected_api_behavior():
    pass
""",
    )

    context = build_qa_context(tests_dir)

    assert context["tests"][0]["test_id"] is None
    assert context["tests"][0]["title"] == "Unexpected API behavior"


def test_output_order_is_deterministic(tmp_path):
    tests_dir = tmp_path / "tests"
    write_test_file(
        tests_dir,
        Path("api/test_login_api.py"),
        """
def test_api_01_10_login_empty_json_object():
    pass

def test_api_01_02_login_unknown_username():
    pass
""",
    )

    first = build_qa_context(tests_dir)
    second = build_qa_context(tests_dir)

    assert first == second
    assert [test["test_id"] for test in first["tests"]] == ["01.02", "01.10"]


def test_real_repository_discovers_major_product_suites():
    context = build_qa_context()
    suites = {(suite["name"], suite["test_type"]) for suite in context["suites"]}

    assert {
        ("Login API Tests", "api"),
        ("Flask Route Tests", "route"),
        ("UI Tests", "ui"),
    }.issubset(suites)
    assert any(test["test_id"] == "01.01" for test in context["tests"])
    assert any(test["test_id"] == "03.01" for test in context["tests"])
    assert not any(
        test["source_file"].endswith("test_github_pr_service.py")
        for test in context["tests"]
    )
