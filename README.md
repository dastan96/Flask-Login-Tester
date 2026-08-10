# QA Lab - Flask Login Tester

QA Lab is a Flask-based QA automation portfolio project. It demonstrates layered application testing, API automation, route validation, Playwright browser automation, CI validation, automated result aggregation, public test reporting, and deployment.

The application is intentionally compact: the login flow is simple, but the surrounding test and reporting architecture shows how a QA/SDET project can move from local validation to CI artifacts and a public quality dashboard.

## Live Project Links

- [Live QA Lab application](https://qa.datlas.me)
- [Public automated results page](https://dastan96.github.io/Flask-Login-Tester/)
- [GitHub repository](https://github.com/dastan96/Flask-Login-Tester)

## What This Project Demonstrates

- Login API automation with JSON response and validation assertions
- Flask route validation for rendered pages, redirects, public navigation, and form responses
- Playwright Chromium UI automation for user-visible login behavior
- Layered QA strategy across API, route, and browser-level checks
- GitHub Actions CI with separate backend and UI test jobs
- JUnit XML and pytest HTML report generation
- Combined result normalization into a sanitized public feed
- GitHub Pages result publishing
- Render-hosted Flask application consuming the public feed server-side

## Test Architecture

### Login API Tests

The Login API suite uses pytest and Flask test-client behavior to validate JSON `POST /login` responses. It covers successful authentication, unknown users, wrong passwords, required-field handling, empty values, null values, and empty JSON input.

### Flask Route Tests

The route suite uses pytest to validate server-rendered behavior without a real browser. It covers the dashboard route, `/welcome` redirect behavior, legacy `/welcome?api=true` JSON behavior, public navigation, Architecture page content, Test Library content, and browser-form login responses.

### UI Tests

The UI suite uses Playwright with Chromium. It starts the Flask application locally during pytest execution and validates login-page controls, successful login feedback, invalid-credentials feedback, and browser-native required-field validation.

The repository also contains internal tests for the reporting feed validator and JUnit normalization script. Those tests support the CI/reporting infrastructure rather than the public Test Library.

## CI & Reporting

GitHub Actions runs the project in separate jobs:

1. `test` runs the non-UI pytest suite, excluding `tests/ui`, and produces JUnit XML plus a self-contained pytest HTML report.
2. `ui-tests` installs Playwright Chromium and runs only the login UI suite.
3. `aggregate-results` downloads the backend and UI JUnit reports, then runs `scripts/normalize_test_results.py` to produce a combined sanitized `latest.json` and `index.html`.
4. `deploy-pages` publishes the generated public results page and feed through GitHub Pages on successful pushes to `main`.

Pull requests validate the backend tests, UI tests, and combined aggregation path. GitHub Pages deployment remains restricted to successful pushes to `main`.

The Flask dashboard does not fetch GitHub Pages directly from the browser. Flask fetches the public `latest.json` server-side, validates it, exposes it through `GET /api/test-results/latest`, and the dashboard consumes that internal endpoint.

Raw JUnit XML and pytest HTML reports are retained as GitHub Actions artifacts. The public Pages output exposes only sanitized result metadata.

## Application and Hosting Architecture

- GitHub stores the source code and workflow definitions.
- GitHub Actions runs backend and browser automation.
- GitHub Pages publishes the sanitized public results feed and generated results page.
- Render hosts the Flask application.
- The Flask application consumes the public results feed server-side and renders the QA Lab dashboard.

## Technology Stack

- Python
- Flask
- pytest
- pytest-html
- Playwright
- Bootstrap
- GitHub Actions
- GitHub Pages
- Render

## Run Locally

Clone the repository:

```bash
git clone https://github.com/dastan96/Flask-Login-Tester.git
cd Flask-Login-Tester
```

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows, activate the environment with:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Install Chromium for local Playwright execution:

```bash
python -m playwright install chromium
```

Run the Flask application:

```bash
python app.py
```

By default, the application runs at `http://127.0.0.1:5001` unless `PORT` is set.

## Running Tests

Run the complete suite:

```bash
pytest -q
```

Run the Login API tests:

```bash
pytest -q tests/api/test_login_api.py
```

Run the Flask Route tests:

```bash
pytest -q tests/test_routes.py
```

Run the Playwright login UI tests:

```bash
pytest -q tests/ui/test_login_ui.py --browser chromium
```

Generate local CI-style reports and a public feed:

```bash
mkdir -p test-results public
pytest \
  --junitxml=test-results/junit.xml \
  --html=test-results/report.html \
  --self-contained-html
python scripts/normalize_test_results.py \
  --junit test-results/junit.xml \
  --out-dir public \
  --branch local \
  --commit-sha local \
  --trigger local \
  --workflow-run-url ""
```

## Project Structure

```text
.github/workflows/          GitHub Actions test, aggregation, and Pages workflow
scripts/                    JUnit normalization into public reporting output
services/                   Server-side latest.json fetching and validation
static/                     CSS and JavaScript for public pages
templates/                  Flask-rendered Dashboard, Login Demo, Test Library, and Architecture pages
tests/
  api/                      Login API pytest suite
  ui/                       Playwright login UI suite and local Flask server fixture
  fixtures/                 Test fixtures for feed/dashboard validation
app.py                      app.py — Flask routes, login behavior, and dashboard results endpoint
requirements.txt            Python runtime and test dependencies
```

## Public Reporting

The public dashboard is designed to show useful QA status without exposing raw CI output. GitHub Actions keeps raw JUnit XML and pytest HTML reports as short-lived artifacts, while the public GitHub Pages feed contains sanitized fields such as suite names, test IDs, statuses, durations, branch, commit SHA, trigger, and workflow run URL.

The Flask application validates that feed before returning it through `GET /api/test-results/latest`, so the browser receives a clean internal contract rather than directly depending on GitHub Pages.
