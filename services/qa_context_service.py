import ast
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TESTS_DIR = PROJECT_ROOT / "tests"
API_TEST_PATTERN = re.compile(r"^test_api_(\d{2})_(\d{2})_(.+)$")
UI_TEST_PATTERN = re.compile(r"^test_ui_(\d{2})_(.+)$")
ACRONYMS = {
    "api": "API",
    "ci": "CI",
    "css": "CSS",
    "html": "HTML",
    "http": "HTTP",
    "json": "JSON",
    "ui": "UI",
    "url": "URL",
}
TEST_TYPE_ORDER = {"api": 0, "route": 1, "ui": 2}


def _readable_title(value):
    words = [ACRONYMS.get(word, word) for word in value.strip("_").split("_") if word]
    if not words:
        return "Unnamed test"
    title = " ".join(words)
    return title[0].upper() + title[1:]


def _api_suite_name(path):
    name = path.stem.removeprefix("test_")
    if name.endswith("_api"):
        name = name[:-4]
    subject = _readable_title(name)
    return f"{subject} API Tests"


def _suite_for_file(relative_path):
    if len(relative_path.parts) > 1 and relative_path.parts[0] == "api":
        return _api_suite_name(relative_path), "api"
    if len(relative_path.parts) > 1 and relative_path.parts[0] == "ui":
        return "UI Tests", "ui"
    if len(relative_path.parts) == 1 and relative_path.stem == "test_routes":
        return "Flask Route Tests", "route"
    return None


def _test_functions(tree):
    functions = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                functions.append(node)
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            functions.extend(
                child
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                and child.name.startswith("test_")
            )
    return functions


def _test_identity(function_name, test_type):
    if test_type == "api":
        match = API_TEST_PATTERN.match(function_name)
        if match:
            return f"{match.group(1)}.{match.group(2)}", _readable_title(match.group(3))

    if test_type == "ui":
        match = UI_TEST_PATTERN.match(function_name)
        if match:
            return f"03.{match.group(1)}", _readable_title(match.group(2))

    name = function_name.removeprefix("test_")
    return None, _readable_title(name)


def build_qa_context(tests_dir=DEFAULT_TESTS_DIR):
    tests_path = Path(tests_dir).resolve()
    discovered = []

    for source_path in sorted(tests_path.rglob("test_*.py")):
        relative_path = source_path.relative_to(tests_path)
        suite = _suite_for_file(relative_path)
        if suite is None:
            continue

        suite_name, test_type = suite
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        source_file = (Path(tests_path.name) / relative_path).as_posix()

        for function in _test_functions(tree):
            test_id, title = _test_identity(function.name, test_type)
            test = {
                "test_id": test_id,
                "title": title,
                "suite": suite_name,
                "test_type": test_type,
                "source_file": source_file,
                "function_name": function.name,
            }
            discovered.append((function.lineno, test))

    discovered.sort(
        key=lambda item: (
            TEST_TYPE_ORDER[item[1]["test_type"]],
            item[1]["suite"],
            item[1]["source_file"],
            item[1]["test_id"] is None,
            item[1]["test_id"] or "",
            item[0],
        )
    )
    tests = [test for _, test in discovered]

    suite_data = {}
    for test in tests:
        key = (test["suite"], test["test_type"])
        summary = suite_data.setdefault(
            key,
            {
                "name": test["suite"],
                "test_type": test["test_type"],
                "source_files": [],
                "test_count": 0,
            },
        )
        if test["source_file"] not in summary["source_files"]:
            summary["source_files"].append(test["source_file"])
        summary["test_count"] += 1

    suites = sorted(
        suite_data.values(),
        key=lambda suite: (TEST_TYPE_ORDER[suite["test_type"]], suite["name"]),
    )
    return {"suites": suites, "tests": tests}
