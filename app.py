from flask import Flask, jsonify, request, render_template, redirect

app = Flask(__name__)

# Mock user data
users = {"testuser": "password123"}  # A dictionary to store username-password pairs

@app.route('/')
def home():
    return "Welcome to the Login App! Go to /login to log in or /register to register."

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()  # Get JSON data from the request
        if not data:
            return jsonify({"error": "Invalid or missing JSON payload"}), 400

        username = data.get('username')
        password = data.get('password')

        # Check for missing fields
        if not username:
            return jsonify({"error": "Username is a required field"}), 400
        if not password:
            return jsonify({"error": "Password is a required field"}), 400

        # Validate credentials
        if username in users and users[username] == password:
            return jsonify({
                "message": "Login successful",
                "username": username
            }), 200
        else:
            return jsonify({"error": "Invalid credentials. Try again."}), 401

    return render_template('login.html')

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()  # Get JSON data from the request
        if not data:
            return jsonify({"error": "Invalid or missing JSON payload"}), 400

        username = data.get('username')
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        # Check for missing fields
        if not username:
            return jsonify({"error": "Username is a required field"}), 400
        if not password:
            return jsonify({"error": "Password is a required field"}), 400
        if not confirm_password:
            return jsonify({"error": "Confirm password is a required field"}), 400

        # Validate inputs
        if password != confirm_password:  # Check if passwords match
            return jsonify({"error": "Passwords do not match. Try again."}), 400

        if username in users:  # Check if the username already exists
            return jsonify({"error": "Username already exists. Choose another."}), 400

        # Add the new user to the dictionary
        users[username] = password
        return jsonify({"message": "User registered successfully"}), 201

    return render_template('register.html')

# Welcome Route
@app.route('/welcome')
def welcome():
    username = request.args.get('user', 'Guest')  # Get username from query parameters
    return jsonify({
        "message": f"Welcome to My Test, {username}!",
        "info": "This is the welcome page."
    }), 200

if __name__ == '__main__':
    # Use the port provided by Render during deployment
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

# Alias Flask app for Gunicorn
application = app