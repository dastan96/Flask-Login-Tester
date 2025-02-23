document.addEventListener("DOMContentLoaded", function () {
    let folders = document.querySelectorAll(".folder");

    folders.forEach(folder => {
        folder.addEventListener("click", function () {
            let targetId = this.getAttribute("data-target");
            let target = document.getElementById(targetId);
            let arrow = this.querySelector(".arrow");

            if (target) {
                if (target.style.display === "none" || target.style.display === "") {
                    target.style.display = "block";
                    arrow.innerHTML = "▼"; // Opened
                } else {
                    target.style.display = "none";
                    arrow.innerHTML = "▶"; // Collapsed
                }
            }
        });
    });

    // Open test case details in a modal
    document.querySelectorAll(".test-case").forEach(testCase => {
        testCase.addEventListener("click", function () {
            let testId = this.getAttribute("data-test");
            openTestCase(testId);
        });
    });
});

function openTestCase(testId) {
    const testCases = {
        "T1": {
            objective: "Verify that a user can successfully log in using valid credentials.",
            preconditions: "A user account with valid credentials exists in the system.",
            testData: "URL: {BASE_URL}/login, Payload: { \"username\": \"validUser\", \"password\": \"validPassword\" }",
            steps: [
                "Send a POST request to {BASE_URL}/login with the valid credentials.",
                "Observe the HTTP response status and payload."
            ],
            expectation: "The API returns a 200 OK status. The response body is in JSON format and contains the message 'Login successful' (or appropriate token/data if applicable).",
            postconditions: "The user session is initiated, or an authentication token is returned."
        },
        "T2": {
            objective: "Verify that logging in with incorrect credentials fails.",
            preconditions: "The system must validate credentials correctly.",
            testData: "URL: {BASE_URL}/login, Payload: { \"username\": \"invalidUser\", \"password\": \"wrongPassword\" }",
            steps: [
                "Send a POST request to {BASE_URL}/login with incorrect credentials.",
                "Observe the HTTP response status and error message."
            ],
            expectation: "The API returns a 401 Unauthorized status. The response body contains an error message 'Invalid credentials. Try again.'.",
            postconditions: "The user is not logged in, and no session or authentication token is created."
        },
        "T3": {
            objective: "Verify that the login API returns 200 OK on success.",
            preconditions: "A valid user account must exist.",
            testData: "URL: {BASE_URL}/login, Payload: { \"username\": \"validUser\", \"password\": \"validPassword\" }",
            steps: [
                "Send a POST request to {BASE_URL}/login with valid credentials.",
                "Check the HTTP response status."
            ],
            expectation: "The API returns a 200 OK status, confirming successful authentication.",
            postconditions: "None. The test is focused on API response verification."
        },
        "T4": {
            objective: "Verify that the login API returns an error when the username is missing.",
            preconditions: "The API requires both username and password for authentication.",
            testData: "URL: {BASE_URL}/login, Payload: { \"username\": \"\", \"password\": \"validPassword\" }",
            steps: [
                "Send a POST request to {BASE_URL}/login with an empty username field.",
                "Observe the HTTP response."
            ],
            expectation: "The API returns a 400 Bad Request status, indicating that the username is required.",
            postconditions: "None. The user remains unauthenticated."
        },
        "T5": {
            objective: "Verify that the login API returns an error when the password is missing.",
            preconditions: "The API requires both username and password for authentication.",
            testData: "URL: {BASE_URL}/login, Payload: { \"username\": \"validUser\", \"password\": \"\" }",
            steps: [
                "Send a POST request to {BASE_URL}/login with an empty password field.",
                "Observe the HTTP response."
            ],
            expectation: "The API returns a 400 Bad Request status, indicating that the password is required.",
            postconditions: "None. The user remains unauthenticated."
        }
    };

    if (testCases[testId]) {
        document.getElementById("modalObjective").textContent = testCases[testId].objective;
        document.getElementById("modalPreconditions").textContent = testCases[testId].preconditions;
        document.getElementById("modalTestData").textContent = testCases[testId].testData;
        
        let stepsList = document.getElementById("modalSteps");
        stepsList.innerHTML = ""; // Clear previous steps
        testCases[testId].steps.forEach(step => {
            let li = document.createElement("li");
            li.textContent = step;
            stepsList.appendChild(li);
        });

        document.getElementById("modalExpectation").textContent = testCases[testId].expectation;
        document.getElementById("modalPostconditions").textContent = testCases[testId].postconditions;
        
        // Show the modal
        let modalElement = document.getElementById("testCaseModal");
        let modal = new bootstrap.Modal(modalElement);
        modal.show();
    }
}
