#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from services.ai_report_service import generate_ai_report


def parse_args():
    parser = argparse.ArgumentParser(description="Generate an AI-assisted QA report for a Pull Request.")
    parser.add_argument("--pr", type=int, required=True, help="Pull Request number to analyze.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate the report even when it already exists.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    result = generate_ai_report(args.pr, force=args.force)

    status = "generated" if result.generated else "skipped (already exists)"
    print(f"PR #{result.pr_number}: {status}")
    print(f"Report: {result.report_path}")
    if result.generated:
        print(f"Model: {result.model}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
