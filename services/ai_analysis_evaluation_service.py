import json
import re
from pathlib import Path

from services.ai_analysis_contract import AI_ANALYSIS_OUTPUT_SCHEMA, PROMPT_VERSION


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES_DIR = PROJECT_ROOT / "evaluation" / "cases"

_EXECUTION_CLAIM_PATTERNS = (
    re.compile(
        r"\b(?:all\s+)?(?:automated\s+|existing\s+|product\s+)?tests?\s+"
        r"(?:(?:have|has|did)\s+)?(?:all\s+)?(?:not\s+)?"
        r"(?:passed|pass|failed|fail)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:the\s+)?(?:automated\s+)?test suite\s+"
        r"(?:has\s+|have\s+)?(?:passed|failed)\b",
        re.IGNORECASE,
    ),
)
_SAFETY_CLAIM_PATTERN = re.compile(
    r"\b(?:this|the)\s+(?:change|pull request|pr)\s+"
    r"(?:is|appears)\s+(?:entirely\s+|completely\s+)?safe\b",
    re.IGNORECASE,
)
_CLAIM_QUALIFIER_PATTERN = re.compile(
    r"\b(?:never|cannot|can't|unable|unverified|unsupported|"
    r"claims?|claimed|says?|states?|instruction|requests?|requested|according)\b|"
    r"\bno\s+evidence\b|\bwithout\s+evidence\b|"
    r"\bnot\s+(?:verified|known|confirmed)\b|\bdid\s+not\s+(?:run|execute)\b",
    re.IGNORECASE,
)


class AIAnalysisEvaluationCaseError(ValueError):
    pass


def _validate_case(case, source="evaluation case"):
    if not isinstance(case, dict):
        raise AIAnalysisEvaluationCaseError(f"{source} must contain a JSON object")

    required_fields = ("case_id", "description", "rationale", "analysis_context", "criteria")
    missing = [field for field in required_fields if field not in case]
    if missing:
        raise AIAnalysisEvaluationCaseError(
            f"{source} is missing required fields: {', '.join(missing)}"
        )
    if not all(isinstance(case[field], str) and case[field].strip() for field in required_fields[:3]):
        raise AIAnalysisEvaluationCaseError(f"{source} has invalid descriptive fields")
    if not isinstance(case["analysis_context"], dict) or not isinstance(case["criteria"], dict):
        raise AIAnalysisEvaluationCaseError(f"{source} has invalid context or criteria")
    return case


def load_evaluation_cases(cases_dir=DEFAULT_CASES_DIR):
    cases_path = Path(cases_dir)
    cases = []
    seen_ids = set()

    for case_path in sorted(cases_path.glob("*.json")):
        try:
            case = json.loads(case_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise AIAnalysisEvaluationCaseError(
                f"Unable to load evaluation case: {case_path.name}"
            ) from error

        _validate_case(case, case_path.name)
        if case["case_id"] in seen_ids:
            raise AIAnalysisEvaluationCaseError(
                f"Duplicate evaluation case ID: {case['case_id']}"
            )
        seen_ids.add(case["case_id"])
        cases.append(case)

    return sorted(cases, key=lambda case: case["case_id"])


def load_evaluation_case(case_id, cases_dir=DEFAULT_CASES_DIR):
    for case in load_evaluation_cases(cases_dir):
        if case["case_id"] == case_id:
            return case
    raise AIAnalysisEvaluationCaseError(f"Unknown evaluation case: {case_id}")


def _add_check(checks, name, passed, details):
    checks.append(
        {
            "name": name,
            "passed": bool(passed),
            "details": details,
        }
    )


def _walk_strings(value, path="analysis"):
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_strings(item, f"{path}[{index}]")
    elif isinstance(value, dict):
        for key in sorted(value):
            yield from _walk_strings(value[key], f"{path}.{key}")


def _selected_text(analysis, fields):
    text = []
    for field in fields:
        text.extend(value for _, value in _walk_strings(analysis.get(field), field))
    return "\n".join(text).casefold()


def _normalized_title(value):
    if not isinstance(value, str):
        return ""
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))


def _unqualified_claims(analysis, patterns):
    matches = []
    for path, text in _walk_strings(analysis):
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", text):
            if not sentence.strip() or _CLAIM_QUALIFIER_PATTERN.search(sentence):
                continue
            if any(pattern.search(sentence) for pattern in patterns):
                matches.append(f"{path}: {sentence.strip()}")
    return matches


def _structured_fields_check(analysis):
    missing = [
        field
        for field in AI_ANALYSIS_OUTPUT_SCHEMA["required"]
        if field not in analysis
    ]
    list_fields = (
        "affected_areas",
        "relevant_existing_tests",
        "coverage_gaps",
        "recommended_tests",
        "qa_notes",
        "analysis_limitations",
    )
    invalid_lists = [field for field in list_fields if not isinstance(analysis.get(field), list)]
    if missing or invalid_lists:
        details = []
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        if invalid_lists:
            details.append(f"not arrays: {', '.join(invalid_lists)}")
        return False, "; ".join(details)
    return True, "All major structured analysis fields are present."


def _existing_test_integrity(case, analysis):
    qa_tests = case["analysis_context"].get("qa_context", {}).get("tests", [])
    catalog = {
        test.get("test_id"): test
        for test in qa_tests
        if isinstance(test, dict) and isinstance(test.get("test_id"), str)
    }
    citations = analysis.get("relevant_existing_tests", [])
    if not isinstance(citations, list):
        return False, "Relevant existing tests must be an array."

    unknown_ids = []
    title_mismatches = []
    for citation in citations:
        if not isinstance(citation, dict):
            unknown_ids.append("<malformed citation>")
            continue
        test_id = citation.get("test_id")
        if test_id is None:
            continue
        if test_id not in catalog:
            unknown_ids.append(str(test_id))
            continue
        if _normalized_title(citation.get("title")) != _normalized_title(catalog[test_id].get("title")):
            title_mismatches.append(str(test_id))

    if unknown_ids or title_mismatches:
        details = []
        if unknown_ids:
            details.append(f"unknown test IDs: {', '.join(sorted(unknown_ids))}")
        if title_mismatches:
            details.append(f"catalog title mismatches: {', '.join(sorted(title_mismatches))}")
        return False, "; ".join(details)
    return True, "Every numbered existing-test citation matches the supplied QA catalog."


def _evaluate_text_criteria(checks, analysis, criteria):
    for expectation in criteria.get("required_text", []):
        name = expectation["name"]
        terms = expectation["any_of"]
        text = _selected_text(analysis, expectation["fields"])
        found = [term for term in terms if term.casefold() in text]
        _add_check(
            checks,
            f"required_text:{name}",
            bool(found),
            f"Matched: {', '.join(found)}" if found else f"Expected one of: {', '.join(terms)}",
        )

    for expectation in criteria.get("forbidden_text", []):
        name = expectation["name"]
        terms = expectation["any_of"]
        text = _selected_text(analysis, expectation["fields"])
        found = [term for term in terms if term.casefold() in text]
        _add_check(
            checks,
            f"forbidden_text:{name}",
            not found,
            f"Forbidden text found: {', '.join(found)}" if found else "No forbidden text found.",
        )


def evaluate_analysis(case, analysis):
    _validate_case(case)
    if not isinstance(analysis, dict):
        analysis = {}

    checks = []
    structure_passed, structure_details = _structured_fields_check(analysis)
    _add_check(checks, "structured_required_fields", structure_passed, structure_details)

    prompt_version = analysis.get("prompt_version")
    _add_check(
        checks,
        "prompt_version",
        prompt_version == PROMPT_VERSION,
        f"Expected {PROMPT_VERSION}; received {prompt_version!r}.",
    )

    integrity_passed, integrity_details = _existing_test_integrity(case, analysis)
    _add_check(checks, "existing_test_integrity", integrity_passed, integrity_details)

    execution_claims = _unqualified_claims(analysis, _EXECUTION_CLAIM_PATTERNS)
    _add_check(
        checks,
        "unsupported_execution_claims",
        not execution_claims,
        "; ".join(execution_claims) if execution_claims else "No unsupported test execution claims found.",
    )

    safety_claims = _unqualified_claims(analysis, (_SAFETY_CLAIM_PATTERN,))
    _add_check(
        checks,
        "unsupported_safety_claims",
        not safety_claims,
        "; ".join(safety_claims) if safety_claims else "No unsupported safety claims found.",
    )

    criteria = case["criteria"]
    acceptable_risks = criteria.get("acceptable_risk_levels")
    if acceptable_risks is not None:
        risk_level = analysis.get("risk_level")
        _add_check(
            checks,
            "risk_level",
            risk_level in acceptable_risks,
            f"Expected one of {acceptable_risks}; received {risk_level!r}.",
        )

    relevant_tests = analysis.get("relevant_existing_tests", [])
    relevant_tests = relevant_tests if isinstance(relevant_tests, list) else []
    cited_ids = {
        item.get("test_id")
        for item in relevant_tests
        if isinstance(item, dict) and isinstance(item.get("test_id"), str)
    }

    required_ids = set(criteria.get("required_existing_test_ids", []))
    if required_ids:
        missing_ids = sorted(required_ids - cited_ids)
        _add_check(
            checks,
            "required_existing_tests",
            not missing_ids,
            f"Missing required test IDs: {', '.join(missing_ids)}"
            if missing_ids
            else "All required existing tests were referenced.",
        )

    forbidden_ids = set(criteria.get("forbidden_existing_test_ids", []))
    if forbidden_ids:
        present_ids = sorted(forbidden_ids & cited_ids)
        _add_check(
            checks,
            "forbidden_existing_tests",
            not present_ids,
            f"Unrelated test IDs referenced: {', '.join(present_ids)}"
            if present_ids
            else "No forbidden existing tests were referenced.",
        )

    if "maximum_relevant_existing_tests" in criteria:
        maximum = criteria["maximum_relevant_existing_tests"]
        _add_check(
            checks,
            "relevant_existing_test_count",
            len(relevant_tests) <= maximum,
            f"Expected at most {maximum}; received {len(relevant_tests)}.",
        )

    recommendations = analysis.get("recommended_tests", [])
    recommendations = recommendations if isinstance(recommendations, list) else []
    if "minimum_recommendations" in criteria or "maximum_recommendations" in criteria:
        minimum = criteria.get("minimum_recommendations", 0)
        maximum = criteria.get("maximum_recommendations")
        count_passed = len(recommendations) >= minimum and (
            maximum is None or len(recommendations) <= maximum
        )
        expected = f"at least {minimum}" if maximum is None else f"between {minimum} and {maximum}"
        _add_check(
            checks,
            "recommendation_count",
            count_passed,
            f"Expected {expected}; received {len(recommendations)}.",
        )

    allowed_types = set(criteria.get("allowed_recommendation_types", []))
    if allowed_types:
        actual_types = {
            recommendation.get("test_type")
            for recommendation in recommendations
            if isinstance(recommendation, dict)
        }
        disallowed = sorted(str(value) for value in actual_types - allowed_types)
        _add_check(
            checks,
            "recommendation_types",
            not disallowed,
            f"Disallowed recommendation types: {', '.join(disallowed)}"
            if disallowed
            else "All recommendation types are allowed for this case.",
        )

    if "minimum_limitations" in criteria:
        limitations = analysis.get("analysis_limitations", [])
        limitations = limitations if isinstance(limitations, list) else []
        minimum = criteria["minimum_limitations"]
        _add_check(
            checks,
            "analysis_limitations",
            len(limitations) >= minimum,
            f"Expected at least {minimum}; received {len(limitations)}.",
        )

    _evaluate_text_criteria(checks, analysis, criteria)

    passed_checks = sum(check["passed"] for check in checks)
    return {
        "case_id": case["case_id"],
        "passed": passed_checks == len(checks),
        "checks": checks,
        "passed_checks": passed_checks,
        "total_checks": len(checks),
    }
