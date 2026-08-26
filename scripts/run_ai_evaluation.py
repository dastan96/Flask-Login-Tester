#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from services import ai_analysis_evaluation_service, openai_analysis_service
from services.ai_analysis_evaluation_service import AIAnalysisEvaluationCaseError
from services.openai_analysis_service import OpenAIAnalysisServiceError


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Evaluate AI-assisted QA analysis against controlled cases."
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List controlled evaluation cases without calling OpenAI (default).",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Explicitly call OpenAI for the selected controlled evaluation cases.",
    )
    parser.add_argument(
        "--case",
        dest="case_id",
        help="Select one evaluation case by ID.",
    )
    return parser.parse_args(argv)


def _select_cases(case_id):
    if case_id:
        return [ai_analysis_evaluation_service.load_evaluation_case(case_id)]
    return ai_analysis_evaluation_service.load_evaluation_cases()


def _print_case_list(cases, output):
    print("AI QA Evaluation Cases", file=output)
    for case in cases:
        print(f"{case['case_id']}: {case['description']}", file=output)
    print("\nLive analysis was not run.", file=output)


def _print_result(result, output):
    print(f"\n{result['case_id']}", file=output)
    for check in result["checks"]:
        status = "PASS" if check["passed"] else "FAIL"
        print(f"  {status}  {check['name']} - {check['details']}", file=output)
    print(
        f"  Result: {result['passed_checks']}/{result['total_checks']}",
        file=output,
    )


def main(argv=None, *, stdout=None, stderr=None):
    output = stdout or sys.stdout
    error_output = stderr or sys.stderr
    args = parse_args(argv)

    if args.list and args.live:
        print("Choose either --list or --live, not both.", file=error_output)
        return 2

    try:
        cases = _select_cases(args.case_id)
    except AIAnalysisEvaluationCaseError as error:
        print(str(error), file=error_output)
        return 2

    if not args.live:
        _print_case_list(cases, output)
        return 0

    if not os.environ.get("OPENAI_API_KEY", "").strip():
        print(
            "OPENAI_API_KEY is required for explicit live evaluation.",
            file=error_output,
        )
        return 2

    model = openai_analysis_service.resolve_model()
    print("AI QA Evaluation", file=output)
    print(f"Model: {model}", file=output)
    results = []

    for case in cases:
        try:
            analysis = openai_analysis_service.analyze_context(
                case["analysis_context"],
                model=model,
            )
        except OpenAIAnalysisServiceError as error:
            print(
                f"Live analysis failed for {case['case_id']}: {error}",
                file=error_output,
            )
            return 2

        result = ai_analysis_evaluation_service.evaluate_analysis(case, analysis)
        results.append(result)
        _print_result(result, output)

    passed_checks = sum(result["passed_checks"] for result in results)
    total_checks = sum(result["total_checks"] for result in results)
    print(f"\nOverall: {passed_checks}/{total_checks} checks passed", file=output)
    return 0 if all(result["passed"] for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
