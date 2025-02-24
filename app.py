from flask import Flask, jsonify, request, render_template, redirect, url_for
from flask import redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text 
import os
import json
import datetime


app = Flask(__name__)

# Database configuration
if not os.path.exists(app.instance_path):
    os.makedirs(app.instance_path)

db_path = os.path.join(app.instance_path, 'test_results.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
print("Using database path:", os.path.abspath(db_path))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Mock user data
users = {
    "guest_user": "secret_pass123",
    "automation_user1": "secret_pass123",
    "automation_user2": "secret_pass123",
    "error_user": "secret_pass123"
}

# Home Route
@app.route('/')
def home():
    return "Welcome to the Login App! Go to /login to log in."

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form

        if not data:
            return jsonify({"error": "Invalid request format."}), 400

        username = data.get('username')
        password = data.get('password')

        # Validate fields
        if not username:
            if request.is_json:
                return jsonify({"error": "Username is a required field."}), 400
            return render_template('login.html', error="Username is a required field.")
        if not password:
            if request.is_json:
                return jsonify({"error": "Password is a required field."}), 400
            return render_template('login.html', error="Password is a required field.")

        if users.get(username) == password:
            if request.is_json:
                return jsonify({
                    "message": "Login successful",
                    "username": username
                }), 200
            # Redirect to the welcome route with the username as a query parameter
            return redirect(url_for('welcome', user=username))

        if request.is_json:
            return jsonify({"error": "Invalid credentials. Try again."}), 401
        return render_template('login.html', error="Invalid credentials. Try again.")

    return render_template('login.html')


#Logout
@app.route('/logout', methods=['GET'])
def logout():
    return redirect(url_for('login'))

# Welcome Route
@app.route('/welcome', methods=['GET'])
def welcome():
    username = request.args.get('user', 'Guest')

    # If this is an API request, return JSON for the latest 5 test results
    if request.args.get("api") == "true":
        # 1) Query only the 5 most recent records, ordered by last_run descending
        results = (TestResults.query
                   .order_by(TestResults.last_run.desc())
                   .limit(5)
                   .all())

        test_cases = []
        passed = 0
        failed = 0

        # 2) Build the test_cases list and count pass/fail
        for result in results:
            test_cases.append({
                "test_id": result.test_id,
                "test_name": result.test_name,
                "status": result.status,
                "duration": result.duration,
                "last_run": result.last_run
            })
            if result.status == "Passed":
                passed += 1
            else:
                failed += 1

        # 3) Summarize the pass/fail for the chart
        summary = {
            "backend_passed": passed,
            "backend_failed": failed,
            "pending": 2  # For UI tests (if applicable)
        }

        # 4) Return JSON with both the summary and these 5 test cases
        return jsonify({
            "summary": summary,
            "test_cases": test_cases
        })

    # Otherwise, render the welcome.html template with the same 5 results
    else:
        # Only show 5 records on the HTML version as well
        results = (TestResults.query
                   .order_by(TestResults.last_run.desc())
                   .limit(5)
                   .all())

        return render_template('welcome.html', test_cases=results, username=username)
    
#History Data
@app.route("/history", methods=["GET"])
def history():
    # Group test results by run_id and aggregate counts
    results = db.session.execute(text("""
        SELECT run_id,
               COUNT(*) AS total,
               SUM(CASE WHEN status='Passed' THEN 1 ELSE 0 END) AS passed,
               MAX(last_run) AS date
        FROM test_results_table
        GROUP BY run_id
        ORDER BY date DESC
        LIMIT 10
    """)).fetchall()

    runs_data = []
    for row in results:
        runs_data.append({
            "run_id": row[0],
            "total": row[1],
            "passed": row[2],
            "date": row[3]  # this should be in a sortable/displayable format, e.g. "YYYY-MM-DD HH:MM:SS"
        })

    return jsonify({"runs": runs_data})



#Test Plans
@app.route('/test-plan', methods=['GET'])
def test_plan():
    return render_template('test_plan.html')  # 


# About Route
@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

# Alias Flask app for Gunicorn
application = app
app.logger.info(f"Static folder: {app.static_folder}")

class TestResults(db.Model):
    __tablename__ = "test_results_table"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    test_id = db.Column(db.String(20), nullable=False)      # Example: "01.01"
    test_name = db.Column(db.String(100), nullable=False)     # Example: "Login with valid credentials"
    status = db.Column(db.String(20), nullable=False)         # "Passed" or "Failed"
    duration = db.Column(db.String(20), nullable=False)       # Example: "0.11s"
    last_run = db.Column(db.String(50), nullable=False)       # Timestamp of last execution
    run_id = db.Column(db.String(50), nullable=True)          # Model ID



if __name__ == '__main__':
    # Use the port provided by Render during deployment
    port = os.environ.get("PORT", 5001)
    try:
        port = int(port)
        print(f"Port successfully set to: {port}")
    except ValueError:
        print(f"Invalid port value: {port}. Falling back to default port 5001.")
        port = 5001

    # Start the Flask app
    app.run(host='0.0.0.0', port=port, debug=(os.environ.get("DEBUG", "False").lower() == "true"))