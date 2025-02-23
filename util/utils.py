from app import app, db, TestResults
import datetime

def save_individual_test_result(test_id, test_name, status, duration="N/A"):
    with app.app_context():
        new_result = TestResults(
            test_id=test_id,
            test_name=test_name,
            status=status,
            duration=duration,
            last_run=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.session.add(new_result)
        db.session.commit()
