from flask import Flask, jsonify, request, render_template, redirect

app = Flask(__name__, static_folder='static')

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
        data = request.form

        username = data.get('username')
        password = data.get('password')

        # Validate credentials
        if not username or not password:
            error_message = "Invalid username or password, please use any of the given usernames and passwords."
            return render_template('login.html', error=error_message)

        if users.get(username) == password:
            return redirect('/welcome')
        else:
            error_message = "Invalid username or password, please use any of the given usernames and passwords."
            return render_template('login.html', error=error_message)

    return render_template('login.html')


# Welcome Route
@app.route('/welcome')
def welcome():
    # Example data (replace with real test results dynamically)
    test_results = {
        "ui_passed": 5,
        "ui_failed": 1,
        "backend_passed": 3,
        "backend_failed": 1,
        "status": "Passed",
        "duration": "0.12s",
        "last_run": "Jan 31, 2025"
    }
    return render_template('welcome.html', results=test_results)


# Logout Route
@app.route('/logout')
def logout():
    return redirect('/login')  # Redirect to the login page


# About Route
@app.route('/about')
def about():
    return "This is a demo dashboard for showcasing test results."


if __name__ == '__main__':
    # Use the port provided by Render during deployment
    import os
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port, debug=True)

# Alias Flask app for Gunicorn
application = app
app.logger.info(f"Static folder: {app.static_folder}")