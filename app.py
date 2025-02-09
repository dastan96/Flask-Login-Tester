from flask import Flask, jsonify, request, render_template, redirect, url_for
from flask import redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import json
import datetime


app = Flask(__name__)

# Database configuration
if not os.path.exists(app.instance_path):
    os.makedirs(app.instance_path)

db_path = os.path.join(app.instance_path, 'test_results.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
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
    # Get username from query parameters
    username = request.args.get('user', 'Guest')

    # Query the latest test results from the database.
    # This assumes that a higher id means a more recent record.
    latest_result = TestResults.query.order_by(TestResults.id.desc()).first()

    if latest_result:
        test_results = {
            "ui_passed": latest_result.ui_passed,
            "ui_failed": latest_result.ui_failed,
            "backend_passed": latest_result.backend_passed,
            "backend_failed": latest_result.backend_failed,
            "status": latest_result.status,
            "duration": latest_result.duration,
            "last_run": latest_result.last_run
        }
    else:
        # Provide default test results if the database is empty
        test_results = {
            "ui_passed": 0,
            "ui_failed": 0,
            "backend_passed": 0,
            "backend_failed": 0,
            "status": "Not Run",
            "duration": "N/A",
            "last_run": "N/A"
        }

    # **API Request Handling**
    if request.args.get("api") == "true":
        return jsonify(test_results)  # Return data as JSON for API requests

    # **Frontend Handling (Render the page with valid test results)**
    return render_template('welcome.html', results=test_results, username=username)


# About Route
@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

# Alias Flask app for Gunicorn
application = app
app.logger.info(f"Static folder: {app.static_folder}")

class TestResults(db.Model):
    __tablename__ = "test_results_table"  
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=False)
    ui_passed = db.Column(db.Integer, default=0)
    backend_passed = db.Column(db.Integer, default=0)
    ui_failed = db.Column(db.Integer, default=0)
    backend_failed = db.Column(db.Integer, default=0)
    duration = db.Column(db.String(20), nullable=False)
    last_run = db.Column(db.String(20), nullable=False)


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