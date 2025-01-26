 # Flask Login Tester

This is a simple Flask web application showcasing user authentication functionalities. The project is designed to demonstrate API testing with Postman while keeping the backend minimal yet effective.

## Features
- **User Registration**: Create a new user by providing a username and password.
- **User Login**: Authenticate using existing credentials.
- **Welcome Page**: Displays a personalized welcome message after successful login.
- **API Testing**: Supports extensive positive and negative test scenarios using Postman.

## Purpose
This project was built to:
1. Showcase my skills in API testing and backend development.
2. Provide a simple and understandable example for API tests.
3. Demonstrate error handling and response validation for real-world scenarios.

## Technologies Used
- **Flask**: Python microframework for building the web application.
- **Postman**: For API testing and automation.
- **Git/GitHub**: Version control and collaboration.
- **Render**: Deployment of the application (optional).

## Setup Instructions

### Prerequisites
- Python 3.7+
- `pip` (Python package manager)
- Git installed on your machine

### Steps to Run Locally
1. Clone the repository:
    ```bash
    git clone https://github.com/dastan96/Flask-Login-Tester.git
    cd Flask-Login-Tester
    ```

2. Create and activate a virtual environment (optional but recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # For Mac/Linux
    venv\Scripts\activate     # For Windows
    ```

3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Run the Flask application:
    ```bash
    python app.py
    ```

5. Open your browser and visit `http://127.0.0.1:5000`.


### API Endpoints
#### 1. `/register` (POST)
- **Description**: Register a new user.
- **Request Body**:
  ```json
  {
      "username": "exampleuser",
      "password": "examplepass",
      "confirm_password": "examplepass"
  }

  ## Postman Collection and Environment
To test the Flask Login API, you can use the provided Postman collection and environment:
1. **Import the Collection**:
   - Go to Postman > Import > Upload the `Flask-Login-API-Tests.postman_collection.json` file.
2. **Import the Environment**:
   - Go to Postman > Manage Environments > Import > Upload the `render-environment.json` file.
3. **Run the Tests**:
   - Select the `Render Deployment` environment.
   - Run individual requests or use the Postman Runner to run all tests in the collection.