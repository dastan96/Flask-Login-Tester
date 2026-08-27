const TEST_LIBRARY = [
    {
        id: "01",
        title: "01 — Login API Tests",
        description: "Validates authentication behavior, invalid credentials, and required-field handling for the login API.",
        cases: [
            {
                id: "01.01",
                title: "Valid credentials return successful authentication response",
                objective: "Verify that valid automation credentials return the expected successful JSON response.",
                preconditions: "The Flask application is running and automation_user1 is configured.",
                testData: "POST /login JSON: username=automation_user1, password=secret_pass123",
                steps: [
                    "Send a JSON POST request to /login with valid automation_user1 credentials.",
                    "Assert that the response is JSON.",
                    "Assert the exact status code and response body."
                ],
                expectedResult: "HTTP 200 with {\"message\":\"Login successful\",\"username\":\"automation_user1\"}.",
                postconditions: "None verified by this test."
            },
            {
                id: "01.02",
                title: "Unknown username is rejected",
                objective: "Verify that a username not present in the demo user store cannot authenticate.",
                preconditions: "The Flask application is running and the request body is JSON.",
                testData: "POST /login JSON: username=unknown_user, password=secret_pass123",
                steps: [
                    "Send a JSON POST request to /login with an unknown username.",
                    "Assert that the response is JSON.",
                    "Assert the exact error response."
                ],
                expectedResult: "HTTP 401 with {\"error\":\"Invalid credentials. Try again.\"}.",
                postconditions: "None verified by this test."
            },
            {
                id: "01.03",
                title: "Wrong password is rejected",
                objective: "Verify that a known username with an incorrect password cannot authenticate.",
                preconditions: "The Flask application is running and automation_user1 is configured.",
                testData: "POST /login JSON: username=automation_user1, password=wrong-password",
                steps: [
                    "Send a JSON POST request to /login with a valid username and wrong password.",
                    "Assert that the response is JSON.",
                    "Assert the generic invalid-credentials response."
                ],
                expectedResult: "HTTP 401 with {\"error\":\"Invalid credentials. Try again.\"}.",
                postconditions: "None verified by this test."
            },
            {
                id: "01.04",
                title: "Missing username key returns username-required error",
                objective: "Verify that the API rejects a login request when the username key is omitted.",
                preconditions: "The Flask application is running and the request body is JSON.",
                testData: "POST /login JSON: password=secret_pass123",
                steps: [
                    "Send a JSON POST request to /login without the username key.",
                    "Assert that the response is JSON.",
                    "Assert the exact username-required response."
                ],
                expectedResult: "HTTP 400 with {\"error\":\"Username is a required field.\"}.",
                postconditions: "None verified by this test."
            },
            {
                id: "01.05",
                title: "Empty username returns username-required error",
                objective: "Verify that an empty username string is treated as missing input.",
                preconditions: "The Flask application is running and the request body is JSON.",
                testData: "POST /login JSON: username=\"\", password=secret_pass123",
                steps: [
                    "Send a JSON POST request to /login with an empty username.",
                    "Assert that the response is JSON.",
                    "Assert the exact username-required response."
                ],
                expectedResult: "HTTP 400 with {\"error\":\"Username is a required field.\"}.",
                postconditions: "None verified by this test."
            },
            {
                id: "01.06",
                title: "Null username returns username-required error",
                objective: "Verify that a null username value is rejected.",
                preconditions: "The Flask application is running and the request body is JSON.",
                testData: "POST /login JSON: username=null, password=secret_pass123",
                steps: [
                    "Send a JSON POST request to /login with username set to null.",
                    "Assert that the response is JSON.",
                    "Assert the exact username-required response."
                ],
                expectedResult: "HTTP 400 with {\"error\":\"Username is a required field.\"}.",
                postconditions: "None verified by this test."
            },
            {
                id: "01.07",
                title: "Missing password key returns password-required error",
                objective: "Verify that the API rejects a login request when the password key is omitted.",
                preconditions: "The Flask application is running and the request body is JSON.",
                testData: "POST /login JSON: username=automation_user1",
                steps: [
                    "Send a JSON POST request to /login without the password key.",
                    "Assert that the response is JSON.",
                    "Assert the exact password-required response."
                ],
                expectedResult: "HTTP 400 with {\"error\":\"Password is a required field.\"}.",
                postconditions: "None verified by this test."
            },
            {
                id: "01.08",
                title: "Empty password returns password-required error",
                objective: "Verify that an empty password string is treated as missing input.",
                preconditions: "The Flask application is running and the request body is JSON.",
                testData: "POST /login JSON: username=automation_user1, password=\"\"",
                steps: [
                    "Send a JSON POST request to /login with an empty password.",
                    "Assert that the response is JSON.",
                    "Assert the exact password-required response."
                ],
                expectedResult: "HTTP 400 with {\"error\":\"Password is a required field.\"}.",
                postconditions: "None verified by this test."
            },
            {
                id: "01.09",
                title: "Null password returns password-required error",
                objective: "Verify that a null password value is rejected.",
                preconditions: "The Flask application is running and the request body is JSON.",
                testData: "POST /login JSON: username=automation_user1, password=null",
                steps: [
                    "Send a JSON POST request to /login with password set to null.",
                    "Assert that the response is JSON.",
                    "Assert the exact password-required response."
                ],
                expectedResult: "HTTP 400 with {\"error\":\"Password is a required field.\"}.",
                postconditions: "None verified by this test."
            },
            {
                id: "01.10",
                title: "Empty JSON object returns invalid-request error",
                objective: "Verify that an empty JSON object is rejected before field-level validation.",
                preconditions: "The Flask application is running and the request body is JSON.",
                testData: "POST /login JSON: {}",
                steps: [
                    "Send a JSON POST request to /login with an empty object.",
                    "Assert that the response is JSON.",
                    "Assert the exact invalid-request-format response."
                ],
                expectedResult: "HTTP 400 with {\"error\":\"Invalid request format.\"}.",
                postconditions: "None verified by this test."
            }
        ]
    },
    {
        id: "02",
        title: "02 — Flask Route Tests",
        description: "Validates page routing, redirects, navigation, rendered content, and browser-form responses.",
        cases: [
            {
                id: "02.01",
                title: "Dashboard renders at root route",
                objective: "Verify that the root route renders the public QA dashboard.",
                preconditions: "The Flask application can render the dashboard template.",
                testData: "GET /",
                steps: [
                    "Request the root URL.",
                    "Assert a successful response.",
                    "Assert that dashboard navigation and required dashboard element IDs are present."
                ],
                expectedResult: "HTTP 200 with the QA Lab dashboard content and no legacy branding.",
                postconditions: "None verified by this test."
            },
            {
                id: "02.02",
                title: "Plain /welcome redirects to root",
                objective: "Verify that / is the canonical dashboard URL.",
                preconditions: "The Flask application is running.",
                testData: "GET /welcome",
                steps: [
                    "Request /welcome without query parameters.",
                    "Inspect the status code and Location header."
                ],
                expectedResult: "HTTP 302 with Location set to /.",
                postconditions: "None verified by this test."
            },
            {
                id: "02.03",
                title: "Following /welcome redirect displays dashboard",
                objective: "Verify that clients following the /welcome redirect land on the dashboard.",
                preconditions: "The Flask application is running.",
                testData: "GET /welcome with follow_redirects=True",
                steps: [
                    "Request /welcome while following redirects.",
                    "Assert a successful final response.",
                    "Assert the same dashboard content used by GET /."
                ],
                expectedResult: "HTTP 200 with the QA Lab dashboard content.",
                postconditions: "None verified by this test."
            },
            {
                id: "02.04",
                title: "Legacy JSON response is preserved",
                objective: "Verify that /welcome?api=true returns the expected legacy JSON response shape.",
                preconditions: "The test results database fixture is available to the Flask app.",
                testData: "GET /welcome?api=true",
                steps: [
                    "Request /welcome with api=true.",
                    "Assert that the response is JSON.",
                    "Assert the expected summary and test case keys."
                ],
                expectedResult: "HTTP 200 JSON with summary and test_cases fields. The summary contains backend_passed, backend_failed, and pending; each test case contains test_id, test_name, status, duration, and last_run.",
                postconditions: "None verified by this test."
            },
            {
                id: "02.05",
                title: "Login page includes public navigation",
                objective: "Verify that the Login Demo page uses the shared public navigation labels.",
                preconditions: "The Flask app can render templates.",
                testData: "GET /login",
                steps: [
                    "Request /login.",
                    "Assert a successful response.",
                    "Assert Dashboard, Login Demo, Test Library, and About navigation links are present."
                ],
                expectedResult: "HTTP 200 with public navigation and the current login subtitle.",
                postconditions: "None verified by this test."
            },
            {
                id: "02.06",
                title: "Test Library uses canonical public navbar",
                objective: "Verify that the Test Library page aligns with the shared public navbar structure.",
                preconditions: "The Flask app can render templates.",
                testData: "GET /test-plan",
                steps: [
                    "Request /test-plan.",
                    "Assert the canonical navbar container is used.",
                    "Assert the public navigation links are present."
                ],
                expectedResult: "HTTP 200 with the same navbar container and public links used by the other pages.",
                postconditions: "None verified by this test."
            },
            {
                id: "02.07",
                title: "About page reflects current reporting architecture",
                objective: "Verify that the About page describes the active CI and reporting flow.",
                preconditions: "The Flask app can render templates.",
                testData: "GET /about",
                steps: [
                    "Request /about.",
                    "Assert current reporting terms are present.",
                    "Assert stale legacy architecture terms are absent."
                ],
                expectedResult: "HTTP 200 with current Playwright, JUnit XML, pytest HTML, latest.json, GitHub Pages, and /api/test-results/latest content.",
                postconditions: "None verified by this test."
            },
            {
                id: "02.08",
                title: "Valid browser login renders accessible success feedback",
                objective: "Verify that a successful HTML form login stays on the login page and renders accessible success feedback.",
                preconditions: "The Flask application is running and automation_user1 is configured.",
                testData: "POST /login form: username=automation_user1, password=secret_pass123",
                steps: [
                    "Submit the browser form with valid credentials.",
                    "Assert the response remains on /login.",
                    "Assert that the success feedback includes role=status and aria-live=polite."
                ],
                expectedResult: "HTTP 200 rendering login.html with no Location header and Login successful feedback using role=status and aria-live=polite.",
                postconditions: "None verified by this test."
            },
            {
                id: "02.09",
                title: "Invalid browser login renders accessible error",
                objective: "Verify that invalid HTML form credentials render an accessible error message.",
                preconditions: "The login form posts browser form data to /login.",
                testData: "POST /login form: username=automation_user1, password=wrong-password",
                steps: [
                    "Submit the browser form with a valid username and wrong password.",
                    "Assert the response remains on /login.",
                    "Assert a role=alert error is rendered."
                ],
                expectedResult: "HTTP 200 rendering login.html with Invalid credentials. Try again.",
                postconditions: "None verified by this test."
            },
            {
                id: "02.10",
                title: "Missing browser-form username renders accessible error",
                objective: "Verify that server-side browser-form validation reports a missing username.",
                preconditions: "The login form posts browser form data to /login.",
                testData: "POST /login form: username=\"\", password=secret_pass123",
                steps: [
                    "Submit the browser form with an empty username.",
                    "Assert the response remains on /login.",
                    "Assert a role=alert username-required error is rendered."
                ],
                expectedResult: "HTTP 200 rendering login.html with Username is a required field.",
                postconditions: "None verified by this test."
            },
            {
                id: "02.11",
                title: "Missing browser-form password renders accessible error",
                objective: "Verify that server-side browser-form validation reports a missing password.",
                preconditions: "The login form posts browser form data to /login.",
                testData: "POST /login form: username=automation_user1, password=\"\"",
                steps: [
                    "Submit the browser form with an empty password.",
                    "Assert the response remains on /login.",
                    "Assert a role=alert password-required error is rendered."
                ],
                expectedResult: "HTTP 200 rendering login.html with Password is a required field.",
                postconditions: "None verified by this test."
            }
        ]
    },
    {
        id: "03",
        title: "03 — UI Tests",
        description: "Validates login and AI-assisted QA behavior and user-visible feedback in Chromium using Playwright.",
        cases: [
            {
                id: "03.01",
                title: "Login page renders required controls",
                objective: "Verify that the login page renders the expected heading, input fields, and enabled submit button.",
                preconditions: "The login page is accessible in Chromium.",
                testData: "Browser navigation to /login",
                steps: [
                    "Open the login page in Chromium.",
                    "Locate the QA Lab heading.",
                    "Locate the Username field, Password field, and Login button using accessible locators."
                ],
                expectedResult: "The QA Lab heading, Username field, Password field, and Login button are visible; the Login button is enabled.",
                postconditions: "None verified by this test."
            },
            {
                id: "03.02",
                title: "Valid login shows accessible success message",
                objective: "Verify that valid browser-entered credentials keep the user on /login and render accessible success feedback.",
                preconditions: "The login page is accessible in Chromium and automation_user1 is configured.",
                testData: "username=automation_user1, password=secret_pass123",
                steps: [
                    "Open /login in Chromium.",
                    "Fill the Username and Password fields with valid credentials.",
                    "Click the Login button and inspect the resulting page state."
                ],
                expectedResult: "The browser remains on /login and a role=status message contains Login successful.",
                postconditions: "None verified by this test."
            },
            {
                id: "03.03",
                title: "Invalid credentials show accessible error",
                objective: "Verify that wrong credentials produce an accessible browser-visible error.",
                preconditions: "The login page is accessible in Chromium.",
                testData: "username=automation_user1, password=wrong_password",
                steps: [
                    "Open /login in Chromium.",
                    "Submit a valid username with an incorrect password.",
                    "Inspect the resulting page state."
                ],
                expectedResult: "The browser remains on /login and a role=alert message contains Invalid credentials. Try again.",
                postconditions: "None verified by this test."
            },
            {
                id: "03.04",
                title: "Missing username is blocked by native validation",
                objective: "Verify that the required username field blocks form submission before server-side success can occur.",
                preconditions: "The login page is accessible in Chromium and the Username input has a native required constraint.",
                testData: "username left empty, password=secret_pass123",
                steps: [
                    "Open /login in Chromium.",
                    "Fill only the Password field.",
                    "Click the Login button and inspect the Username input validity."
                ],
                expectedResult: "The browser remains on /login. The Username input is invalid, its validationMessage is non-empty, and no success feedback appears.",
                postconditions: "None verified by this test."
            },
            {
                id: "03.05",
                title: "Missing password is blocked by native validation",
                objective: "Verify that the required password field blocks form submission before server-side success can occur.",
                preconditions: "The login page is accessible in Chromium and the Password input has a native required constraint.",
                testData: "username=automation_user1, password left empty",
                steps: [
                    "Open /login in Chromium.",
                    "Fill only the Username field.",
                    "Click the Login button and inspect the Password input validity."
                ],
                expectedResult: "The browser remains on /login. The Password input is invalid, its validationMessage is non-empty, and no success feedback appears.",
                postconditions: "None verified by this test."
            },
            {
                id: "03.06",
                title: "AI-Assisted QA renders available report",
                objective: "Verify that the latest persisted AI-assisted QA report loads automatically in the Pull Request review layout and supports accessible detail navigation.",
                preconditions: "The AI-Assisted QA page is accessible in Chromium and its internal report APIs are intercepted with deterministic report data.",
                testData: "Mocked GET /api/ai-reports and GET /api/ai-reports/42 responses",
                steps: [
                    "Open /ai in Chromium.",
                    "Return a deterministic report index and selected Pull Request report from the intercepted Flask API requests.",
                    "Verify the newest Pull Request is selected automatically.",
                    "Inspect the compact risk, metrics, key findings, and changed-file summary in Overview.",
                    "Open Findings, Test Impact, and Details to inspect deeper observations, recommended tests, and provenance.",
                    "Select an older report and verify the backward-compatible changed-files message."
                ],
                expectedResult: "The page selects PR #42, displays the compact review, switches tabs without reloading, and safely renders an older report without per-file metadata.",
                postconditions: "No report is generated and no external GitHub or OpenAI request is made."
            },
            {
                id: "03.07",
                title: "AI-Assisted QA handles unavailable reports",
                objective: "Verify that the AI-Assisted QA page presents a safe, friendly state when persisted reports are unavailable.",
                preconditions: "The AI-Assisted QA page is accessible in Chromium and the internal index API is intercepted with its established unavailable response.",
                testData: "Mocked HTTP 503 response from GET /api/ai-reports",
                steps: [
                    "Open /ai in Chromium.",
                    "Return the established unavailable response from the intercepted report-index request.",
                    "Verify the loading state disappears.",
                    "Verify the friendly unavailable message is shown and report content remains hidden."
                ],
                expectedResult: "The page displays AI reports are not available yet, removes the loading state, and does not display stale report analysis.",
                postconditions: "No selected-report, GitHub, or OpenAI request is made."
            }
        ]
    }
];

document.addEventListener("DOMContentLoaded", function () {
    const suitesContainer = document.getElementById("testLibrarySuites");

    if (!suitesContainer) {
        return;
    }

    TEST_LIBRARY.forEach(suite => {
        suitesContainer.appendChild(createSuiteCard(suite));
    });

    suitesContainer.addEventListener("click", event => {
        const toggle = event.target.closest("[data-suite-toggle]");
        const testCaseButton = event.target.closest("[data-test-id]");

        if (toggle) {
            toggleSuite(toggle);
        }

        if (testCaseButton) {
            openTestCase(testCaseButton.getAttribute("data-test-id"));
        }
    });
});

function createSuiteCard(suite) {
    const suiteCard = document.createElement("article");
    suiteCard.className = "test-suite-card";

    const panelId = `suite-${suite.id}-cases`;

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "suite-toggle";
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-controls", panelId);
    toggle.setAttribute("data-suite-toggle", "");

    const header = document.createElement("span");
    header.className = "suite-header";

    const suiteId = document.createElement("span");
    suiteId.className = "suite-id";
    suiteId.textContent = suite.id;

    const title = document.createElement("span");
    title.className = "suite-title";
    title.textContent = suiteTitleWithoutNumber(suite.title);

    const count = document.createElement("span");
    count.className = "suite-count";
    count.textContent = `${suite.cases.length} cases`;

    header.append(suiteId, title, count);

    const summary = document.createElement("span");
    summary.className = "suite-summary";
    summary.textContent = suite.description;

    const state = document.createElement("span");
    state.className = "suite-state";
    state.textContent = "Show More";

    toggle.append(header, summary, state);

    const panel = document.createElement("div");
    panel.id = panelId;
    panel.className = "suite-panel d-none";

    const list = document.createElement("div");
    list.className = "test-case-list";

    suite.cases.forEach(testCase => {
        list.appendChild(createTestCaseRow(testCase));
    });

    panel.appendChild(list);
    suiteCard.append(toggle, panel);

    return suiteCard;
}

function createTestCaseRow(testCase) {
    const row = document.createElement("button");
    row.type = "button";
    row.className = "test-case-row";
    row.setAttribute("data-test-id", testCase.id);

    const id = document.createElement("span");
    id.className = "case-id";
    id.textContent = testCase.id;

    const title = document.createElement("span");
    title.className = "case-title";
    title.textContent = testCase.title;

    row.append(id, title);
    return row;
}

function toggleSuite(toggle) {
    const panel = document.getElementById(toggle.getAttribute("aria-controls"));
    const state = toggle.querySelector(".suite-state");
    const isExpanded = toggle.getAttribute("aria-expanded") === "true";

    if (!panel) {
        return;
    }

    toggle.setAttribute("aria-expanded", String(!isExpanded));
    panel.classList.toggle("d-none", isExpanded);
    state.textContent = isExpanded ? "Show More" : "Show Less";
}

function suiteTitleWithoutNumber(title) {
    return title.replace(/^\d{2}\s+—\s+/, "");
}

function openTestCase(testId) {
    const testCase = findTestCase(testId);

    if (!testCase) {
        return;
    }

    renderModalTitle(testCase);
    document.getElementById("modalObjective").textContent = testCase.objective;
    document.getElementById("modalPreconditions").textContent = testCase.preconditions;
    document.getElementById("modalTestData").textContent = testCase.testData;

    const stepsList = document.getElementById("modalSteps");
    stepsList.innerHTML = "";
    testCase.steps.forEach(step => {
        const li = document.createElement("li");
        li.textContent = step;
        stepsList.appendChild(li);
    });

    document.getElementById("modalExpectedResult").textContent = testCase.expectedResult;
    document.getElementById("modalPostconditions").textContent = testCase.postconditions;

    const modalElement = document.getElementById("testCaseModal");
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
}

function renderModalTitle(testCase) {
    const modalTitle = document.getElementById("testCaseModalLabel");
    modalTitle.innerHTML = "";

    const id = document.createElement("span");
    id.className = "case-id";
    id.textContent = testCase.id;

    const title = document.createElement("span");
    title.className = "case-title";
    title.textContent = testCase.title;

    modalTitle.append(id, title);
}

function findTestCase(testId) {
    for (const suite of TEST_LIBRARY) {
        const testCase = suite.cases.find(candidate => candidate.id === testId);

        if (testCase) {
            return testCase;
        }
    }

    return null;
}
