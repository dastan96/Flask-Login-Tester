# run_all_tests.py
import subprocess
import json
import datetime
from util.utils import save_test_results

def run_all_tests():
    try:
        # Run pytest on the tests/api/api_tests.py file with JSON report options.
        # Note: using check=False so it doesn't raise an exception if tests fail.
        result = subprocess.run(
            ["pytest", "tests/api/api_tests.py", "--json-report", "--json-report-file=reports/report.json"],
            capture_output=True, text=True, check=False
        )
    except Exception as e:
        print("Error running tests:", e)
        return

    # Open and parse the JSON report.
    try:
        with open("report.json") as f:
            report = json.load(f)
    except Exception as e:
        print("Error reading JSON report:", e)
        return

    # For debugging: print out the report keys
    print("Report keys:", list(report.keys()))
    
    # Check if the report has a summary.
    summary = report.get("summary")
    if summary is None:
        print("No summary found in the report. Report content:", report)
        return

    # Prepare the results based on the report.
    results = {
        "status": "Passed" if summary.get("failed", 0) == 0 else "Failed",
        "ui_passed": 0,  # UI tests not implemented yet
        "ui_failed": 0,  # UI tests not implemented yet
        "backend_passed": summary.get("passed", 0),
        "backend_failed": summary.get("failed", 0),
        "duration": report.get("duration", "N/A"),
        "last_run": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_test_results(results)
    print("Test results saved to the database.")
    return results

if __name__ == "__main__":
    run_all_tests()
