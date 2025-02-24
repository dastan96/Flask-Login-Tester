import subprocess
import json
import datetime
import os
from util.utils import save_individual_test_result

def extract_numeric_id(nodeid):
    """
    Extracts the numeric portion from a nodeid.
    For example, given:
      "tests/api/api_tests.py::test_api_01_01_login_valid_credentials"
    it returns: "01.01"
    """
    test_name = nodeid.split("::")[-1]  # e.g. "test_api_01_01_login_valid_credentials"
    parts = test_name.split("_")
    if len(parts) >= 4 and parts[0] == "test" and parts[1] == "api":
        return f"{parts[2]}.{parts[3]}"
    return "Unknown"

def process_test_name(nodeid):
    """
    Processes the raw function name by removing the numeric portion.
    For example, given:
      "tests/api/api_tests.py::test_api_01_01_login_valid_credentials"
    it returns: "test_api_login_valid_credentials"
    """
    test_name = nodeid.split("::")[-1]  # "test_api_01_01_login_valid_credentials"
    if test_name.startswith("test_api_"):
        parts = test_name.split("_")
        if len(parts) >= 5:
            # Remove the numeric parts (parts[2] and parts[3]) and rebuild the name.
            friendly_name = "test_api_" + "_".join(parts[4:])
            return friendly_name
    return test_name

def generate_run_id():
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

def run_all_tests():
    # Remove old report for a fresh run.
    if os.path.exists("report.json"):
        os.remove("report.json")
    
    try:
        result = subprocess.run(
            ["pytest", "tests/api/api_tests.py", "--json-report", "--json-report-file=report.json"],
            capture_output=True, text=True, check=False
        )
    except Exception as e:
        print("Error running tests:", e)
        return

    try:
        with open("report.json") as f:
            report = json.load(f)
    except Exception as e:
        print("Error reading JSON report:", e)
        return

    tests = report.get("tests", [])
    print("Number of tests found:", len(tests))
    
    # Generate a unique run_id for this test run.
    run_id = generate_run_id()
    
    for test in tests:
        nodeid = test["nodeid"]
        test_id = extract_numeric_id(nodeid)
        friendly_name = process_test_name(nodeid)
        status = "Passed" if test.get("outcome") == "passed" else "Failed"
        print("Saving test:", f"'{test_id}'", "| Friendly Name:", friendly_name, "| Status:", status)
        # Pass run_id along with the other parameters.
        save_individual_test_result(
            test_id=test_id,         # e.g. "01.01"
            test_name=friendly_name, # e.g. "test_api_login_valid_credentials"
            status=status,
            duration="0.00s",
            run_id=run_id            # New parameter to group this run
        )

    print("All test results saved successfully.")

if __name__ == "__main__":
    run_all_tests()
