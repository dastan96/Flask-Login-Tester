from app import app, db, TestResults

def save_test_results(results):
    """
    Save the provided test results to the database.
    'results' should be a dict with keys: status, ui_passed, ui_failed,
    backend_passed, backend_failed, duration, last_run.
    """
    with app.app_context():
        new_result = TestResults(
            status=results.get("status", "Not Run"),
            ui_passed=results.get("ui_passed", 0),
            ui_failed=results.get("ui_failed", 0),
            backend_passed=results.get("backend_passed", 0),
            backend_failed=results.get("backend_failed", 0),
            duration=results.get("duration", "N/A"),
            last_run=results.get("last_run", "N/A")
        )
        db.session.add(new_result)
        db.session.commit()
