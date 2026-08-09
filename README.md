# Flask Login Tester / QA Lab

Flask Login Tester is a lightweight QA automation portfolio project. It demonstrates layered application testing for a Flask login demo, CI execution, automated reporting, and deployment through a live QA dashboard.

## Live Links

- QA Lab application: https://qa.datlas.me
- Public automated-results page: https://dastan96.github.io/Flask-Login-Tester/
- Repository: https://github.com/dastan96/Flask-Login-Tester

## What This Project Demonstrates

- API automation for positive, negative, missing-field, empty-value, and null-value login scenarios
- Flask route testing for dashboard, navigation, redirects, page content, and browser-form responses
- Playwright UI automation for login-page behavior in Chromium
- CI/CD with separate backend and UI test jobs
- Automated JUnit XML and pytest HTML report generation
- Sanitized public test-result publishing through GitHub Pages
- Render-hosted Flask application consuming the public results feed server-side

## Test Architecture

The public dashboard and Test Library represent 26 application-facing test cases:

- Login API Tests: JSON POST `/login` coverage for valid credentials, invalid credentials, required fields, empty values, null values, and empty JSON input.
- Flask Route Tests: route and template coverage for the dashboard, `/welcome` redirect behavior, legacy `/welcome?api=true` JSON behavior, public navigation, About content, and browser-form login feedback.
- UI Tests: Playwright Chromium coverage for login-page controls, successful login feedback, invalid-credentials feedback, and native required-field validation.

The repository also includes internal pytest coverage for result-feed validation and CI result normalization.

## CI & Reporting

GitHub Actions runs the automated test suite in separate jobs:

- `test`: runs the non-UI pytest suite, excluding `tests/ui`, and produces JUnit XML plus a self-contained pytest HTML report.
- `ui-tests`: installs Playwright Chromium and runs the login UI suite.
- `aggregate-results`: downloads backend and UI JUnit reports, then runs `scripts/normalize_test_results.py` to create a sanitized combined `latest.json` and `index.html`.
- `deploy-pages`: deploys the generated public results feed/page to GitHub Pages on successful pushes to `main`.

The Flask application fetches the GitHub Pages `latest.json` feed server-side and exposes it through `GET /api/test-results/latest`. The dashboard consumes that Flask endpoint rather than fetching GitHub Pages directly from the browser.

Raw CI reports are kept as GitHub Actions artifacts with limited retention. The public GitHub Pages output contains only sanitized result metadata.

## Technology Stack

- Python
- Flask
- Flask-SQLAlchemy
- pytest
- pytest-html
- Playwright
- GitHub Actions
- GitHub Pages
- Render
- Bootstrap

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

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the Flask application:

```bash
python app.py
```

By default, the app runs on `http://127.0.0.1:5001` unless `PORT` is set.

Run the full pytest suite:

```bash
./venv/bin/pytest -q
```

Install Chromium for local Playwright execution when needed:

```bash
./venv/bin/python -m playwright install chromium
```

Run only the Playwright login UI suite:

```bash
./venv/bin/pytest -q tests/ui/test_login_ui.py --browser chromium
```

Generate local CI-style backend reports:

```bash
mkdir -p test-results public
./venv/bin/pytest \
  --ignore=tests/ui \
  --junitxml=test-results/junit.xml \
  --html=test-results/report.html \
  --self-contained-html
```

## Project Structure

- `app.py`: Flask application routes, login behavior, legacy `/welcome?api=true` response, and dashboard results endpoint.
- `services/`: server-side fetching and validation for the public test-results feed.
- `scripts/`: CI result normalization from JUnit XML into public `latest.json` and `index.html`.
- `templates/`: server-rendered pages for the dashboard, login demo, Test Library, and About page.
- `static/`: CSS and JavaScript for the dashboard and Test Library experiences.
- `tests/api/`: Login API pytest suite.
- `tests/ui/`: Playwright login UI suite.
- `tests/fixtures/`: local fixtures used by test-result feed and dashboard tests.
- `.github/workflows/`: GitHub Actions CI, aggregation, and Pages deployment workflow.

## Deployment

Render hosts the Flask application used by the public QA Lab site.

GitHub Actions runs the backend and Playwright UI tests, generates raw reports, normalizes combined results, and publishes the sanitized public feed/page through GitHub Pages.

The live QA Lab dashboard reads the latest public test results through the Flask server-side endpoint.
