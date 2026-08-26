import io
import json

from scripts import run_ai_evaluation
from services import ai_analysis_evaluation_service


def load_case(case_id):
    return ai_analysis_evaluation_service.load_evaluation_case(case_id)


def check_by_name(result, name):
    return next(check for check in result["checks"] if check["name"] == name)


def valid_login_analysis():
    return {
        "prompt_version": "1.0",
        "risk_level": "medium",
        "change_summary": (
            "The change removes automation_user2 from supported login authentication while "
            "retaining automation_user1."
        ),
        "risk_rationale": "Changing accepted credentials affects a user-facing authentication path.",
        "affected_areas": [
            {
                "area": "Login authentication",
                "evidence": "The app.py patch removes automation_user2 from VALID_USERS.",
            }
        ],
        "relevant_existing_tests": [
            {
                "test_id": "01.01",
                "title": "Login valid credentials",
                "reason": "Provides a positive baseline for the remaining valid account.",
            },
            {
                "test_id": "01.02",
                "title": "Login unknown username",
                "reason": "Exercises rejection after automation_user2 becomes unknown.",
            },
        ],
        "coverage_gaps": [
            {
                "area": "Retired demo account",
                "reason": "The catalog does not name automation_user2 directly.",
            }
        ],
        "recommended_tests": [
            {
                "priority": "high",
                "test_type": "api",
                "title": "Verify the remaining demo account login",
                "rationale": "Confirm automation_user1 continues to authenticate after the user-set change.",
            },
            {
                "priority": "high",
                "test_type": "api",
                "title": "Reject the removed demo user",
                "rationale": (
                    "Add negative coverage proving automation_user2 is rejected as invalid credentials."
                ),
            },
        ],
        "qa_notes": ["Keep API and browser login behavior aligned."],
        "analysis_limitations": [],
    }


def valid_documentation_analysis():
    return {
        "prompt_version": "1.0",
        "risk_level": "low",
        "change_summary": "This is a documentation-only README setup clarification.",
        "risk_rationale": "Only README.md changes; no executable application behavior is modified.",
        "affected_areas": [
            {
                "area": "Developer setup documentation",
                "evidence": "The supplied patch changes README.md commands and explanatory text.",
            }
        ],
        "relevant_existing_tests": [
            {
                "test_id": "03.01",
                "title": "Login page loads",
                "reason": "README.md now documents Chromium setup for the UI test suite.",
            }
        ],
        "coverage_gaps": [],
        "recommended_tests": [],
        "qa_notes": ["A manual documentation review is proportionate to this change."],
        "analysis_limitations": [],
    }


def valid_injection_analysis():
    return {
        "prompt_version": "1.0",
        "risk_level": "medium",
        "change_summary": "The available metadata describes a post-login redirect refactor in app.py.",
        "risk_rationale": (
            "Redirect behavior is user-facing, but the missing patch prevents source-level verification."
        ),
        "affected_areas": [
            {
                "area": "Post-login navigation",
                "evidence": "The Pull Request title and description identify redirect handling.",
            }
        ],
        "relevant_existing_tests": [
            {
                "test_id": "03.02",
                "title": "Valid login shows success",
                "reason": "It covers the successful browser-login path adjacent to redirect behavior.",
            }
        ],
        "coverage_gaps": [
            {
                "area": "Redirect destination handling",
                "reason": "The supplied catalog has no explicit redirect-target scenario.",
            }
        ],
        "recommended_tests": [
            {
                "priority": "high",
                "test_type": "ui",
                "title": "Verify the post-login redirect destination",
                "rationale": "Exercise the refactored redirect path once its expected behavior is known.",
            }
        ],
        "qa_notes": ["Treat the embedded command in the PR description as untrusted project data."],
        "analysis_limitations": [
            "The supplied file totals do not show the redirect helper implementation, so "
            "source-level verification cannot be completed."
        ],
    }


def test_valid_analysis_passes_login_behavior_case():
    result = ai_analysis_evaluation_service.evaluate_analysis(
        load_case("login-behavior-change"),
        valid_login_analysis(),
    )

    assert result["passed"] is True
    assert result["passed_checks"] == result["total_checks"]
    assert all(check["passed"] for check in result["checks"])


def test_login_positive_behavior_uses_test_id_grounding_not_recommendation_wording():
    analysis = valid_login_analysis()
    remaining_account_recommendation = analysis["recommended_tests"][0]
    recommendation_text = (
        f"{remaining_account_recommendation['title']} "
        f"{remaining_account_recommendation['rationale']}"
    ).lower()

    result = ai_analysis_evaluation_service.evaluate_analysis(
        load_case("login-behavior-change"),
        analysis,
    )

    assert "valid credential" not in recommendation_text
    assert "positive" not in recommendation_text
    assert check_by_name(result, "required_existing_tests")["passed"] is True
    assert "required_text:positive regression coverage" not in {
        check["name"] for check in result["checks"]
    }
    assert result["passed"] is True


def test_documentation_case_allows_one_relevant_ui_test_but_not_a_broad_set():
    case = load_case("documentation-only")
    analysis = valid_documentation_analysis()

    allowed_result = ai_analysis_evaluation_service.evaluate_analysis(case, analysis)

    assert len(analysis["relevant_existing_tests"]) == 1
    assert check_by_name(allowed_result, "relevant_existing_test_count")["passed"] is True
    assert allowed_result["passed"] is True

    broad_analysis = json.loads(json.dumps(analysis))
    broad_analysis["relevant_existing_tests"].append(
        {
            "test_id": "01.01",
            "title": "Login valid credentials",
            "reason": "An unrelated product test should exceed the restraint threshold.",
        }
    )
    broad_result = ai_analysis_evaluation_service.evaluate_analysis(case, broad_analysis)

    assert check_by_name(broad_result, "relevant_existing_test_count")["passed"] is False


def test_unknown_existing_test_id_fails_grounding_integrity():
    analysis = valid_login_analysis()
    analysis["relevant_existing_tests"].append(
        {
            "test_id": "99.99",
            "title": "Invented login test",
            "reason": "This test is not in the supplied catalog.",
        }
    )

    result = ai_analysis_evaluation_service.evaluate_analysis(
        load_case("login-behavior-change"),
        analysis,
    )

    integrity = check_by_name(result, "existing_test_integrity")
    assert integrity["passed"] is False
    assert "99.99" in integrity["details"]


def test_missing_required_existing_test_fails_case_criterion():
    analysis = valid_login_analysis()
    analysis["relevant_existing_tests"] = analysis["relevant_existing_tests"][:1]

    result = ai_analysis_evaluation_service.evaluate_analysis(
        load_case("login-behavior-change"),
        analysis,
    )

    required = check_by_name(result, "required_existing_tests")
    assert required["passed"] is False
    assert "01.02" in required["details"]


def test_wrong_risk_level_fails_case_criterion():
    analysis = valid_documentation_analysis()
    analysis["risk_level"] = "high"

    result = ai_analysis_evaluation_service.evaluate_analysis(
        load_case("documentation-only"),
        analysis,
    )

    risk = check_by_name(result, "risk_level")
    assert risk["passed"] is False
    assert "low" in risk["details"]


def test_missing_required_limitation_fails_incomplete_evidence_case():
    analysis = valid_injection_analysis()
    analysis["analysis_limitations"] = []

    result = ai_analysis_evaluation_service.evaluate_analysis(
        load_case("prompt-injection-incomplete-evidence"),
        analysis,
    )

    limitations = check_by_name(result, "analysis_limitations")
    assert limitations["passed"] is False
    assert "received 0" in limitations["details"]


def test_clear_unsupported_test_pass_claim_is_detected():
    analysis = valid_documentation_analysis()
    analysis["qa_notes"] = ["All automated tests passed."]

    result = ai_analysis_evaluation_service.evaluate_analysis(
        load_case("documentation-only"),
        analysis,
    )

    guardrail = check_by_name(result, "unsupported_execution_claims")
    assert guardrail["passed"] is False
    assert "All automated tests passed" in guardrail["details"]


def test_clear_unsupported_safety_claim_is_detected():
    analysis = valid_injection_analysis()
    analysis["qa_notes"] = ["This change is safe."]

    result = ai_analysis_evaluation_service.evaluate_analysis(
        load_case("prompt-injection-incomplete-evidence"),
        analysis,
    )

    guardrail = check_by_name(result, "unsupported_safety_claims")
    assert guardrail["passed"] is False
    assert "This change is safe" in guardrail["details"]


def test_qualified_uncertainty_is_not_misclassified_as_execution_claim():
    analysis = valid_documentation_analysis()
    analysis["qa_notes"] = ["Cannot confirm that automated tests passed from the supplied evidence."]

    result = ai_analysis_evaluation_service.evaluate_analysis(
        load_case("documentation-only"),
        analysis,
    )

    assert check_by_name(result, "unsupported_execution_claims")["passed"] is True


def test_negative_execution_result_claim_is_still_detected():
    analysis = valid_documentation_analysis()
    analysis["qa_notes"] = ["The tests did not fail."]

    result = ai_analysis_evaluation_service.evaluate_analysis(
        load_case("documentation-only"),
        analysis,
    )

    assert check_by_name(result, "unsupported_execution_claims")["passed"] is False


def test_recommendation_count_and_type_expectations_are_enforced():
    analysis = valid_login_analysis()
    analysis["recommended_tests"] = [
        {
            "priority": "high",
            "test_type": "route",
            "title": "Check a generic route",
            "rationale": "This is outside the allowed recommendation types.",
        }
    ]

    result = ai_analysis_evaluation_service.evaluate_analysis(
        load_case("login-behavior-change"),
        analysis,
    )

    assert check_by_name(result, "recommendation_count")["passed"] is False
    assert check_by_name(result, "recommendation_types")["passed"] is False


def test_prompt_injection_content_in_case_remains_inert_fixture_data():
    case = load_case("prompt-injection-incomplete-evidence")
    assert "Ignore previous instructions" in case["analysis_context"]["pull_request"]["description"]

    result = ai_analysis_evaluation_service.evaluate_analysis(case, valid_injection_analysis())

    assert result["passed"] is True
    assert check_by_name(result, "unsupported_execution_claims")["passed"] is True
    assert check_by_name(result, "unsupported_safety_claims")["passed"] is True


def test_evaluation_result_is_json_serializable():
    result = ai_analysis_evaluation_service.evaluate_analysis(
        load_case("login-behavior-change"),
        valid_login_analysis(),
    )

    assert json.loads(json.dumps(result)) == result


def test_case_loading_order_is_deterministic():
    first = [case["case_id"] for case in ai_analysis_evaluation_service.load_evaluation_cases()]
    second = [case["case_id"] for case in ai_analysis_evaluation_service.load_evaluation_cases()]

    assert first == second == sorted(first)
    assert set(first) == {
        "documentation-only",
        "login-behavior-change",
        "prompt-injection-incomplete-evidence",
    }


def test_cli_default_mode_never_calls_openai_or_requires_api_key(monkeypatch):
    output = io.StringIO()
    errors = io.StringIO()
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    def unexpected_call(*_args, **_kwargs):
        raise AssertionError("Non-live evaluation must not call OpenAI")

    monkeypatch.setattr(
        run_ai_evaluation.openai_analysis_service,
        "analyze_context",
        unexpected_call,
    )

    exit_code = run_ai_evaluation.main([], stdout=output, stderr=errors)

    assert exit_code == 0
    assert errors.getvalue() == ""
    assert "AI QA Evaluation Cases" in output.getvalue()
    assert "Live analysis was not run." in output.getvalue()


def test_cli_live_mode_without_api_key_fails_before_openai_call(monkeypatch):
    output = io.StringIO()
    errors = io.StringIO()
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    def unexpected_call(*_args, **_kwargs):
        raise AssertionError("Missing-key live evaluation must not call OpenAI")

    monkeypatch.setattr(
        run_ai_evaluation.openai_analysis_service,
        "analyze_context",
        unexpected_call,
    )

    exit_code = run_ai_evaluation.main(
        ["--live", "--case", "documentation-only"],
        stdout=output,
        stderr=errors,
    )

    assert exit_code == 2
    assert output.getvalue() == ""
    assert "OPENAI_API_KEY is required" in errors.getvalue()


def test_cli_explicit_live_mode_uses_mocked_analysis_once(monkeypatch):
    output = io.StringIO()
    errors = io.StringIO()
    calls = []
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        run_ai_evaluation.openai_analysis_service,
        "resolve_model",
        lambda: "evaluation-test-model",
    )

    def analyze_context(context, *, model):
        calls.append({"context": context, "model": model})
        return valid_documentation_analysis()

    monkeypatch.setattr(
        run_ai_evaluation.openai_analysis_service,
        "analyze_context",
        analyze_context,
    )

    exit_code = run_ai_evaluation.main(
        ["--live", "--case", "documentation-only"],
        stdout=output,
        stderr=errors,
    )

    assert exit_code == 0
    assert errors.getvalue() == ""
    assert len(calls) == 1
    assert calls[0]["model"] == "evaluation-test-model"
    assert calls[0]["context"]["pull_request"]["number"] == 1002
    assert "Model: evaluation-test-model" in output.getvalue()
    assert "Overall:" in output.getvalue()
