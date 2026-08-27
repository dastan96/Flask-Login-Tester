# QA Lab

QA Lab is a Flask-based quality engineering portfolio demonstrating API testing, route and integration testing, browser automation, CI/CD, public test-result reporting, and AI-assisted Pull Request change-impact analysis.

The login application is intentionally compact. The engineering focus is the surrounding QA architecture: deterministic test execution, layered automation, sanitized reporting, controlled AI analysis, and clear trust boundaries. It is a portfolio environment, not a production authentication system.

## Live Project

- [QA Lab application](https://qa.datlas.me)
- [AI-Assisted QA explorer](https://qa.datlas.me/ai)
- [Public automated test results](https://dastan96.github.io/Flask-Login-Tester/)
- [GitHub repository](https://github.com/dastan96/Flask-Login-Tester)

## Key Capabilities

- Flask login demo with JSON API and browser-form behavior
- pytest coverage for authentication contracts, routes, redirects, rendering, and accessibility states
- Playwright Chromium automation against a deterministic local Flask server
- Separate backend and browser jobs in GitHub Actions
- JUnit aggregation, self-contained pytest HTML reports, and sanitized public result feeds
- Server-side consumption of GitHub Pages results by the public QA dashboard
- AI-Assisted QA analysis over merged Pull Requests and the real automated-test catalog
- Strict, versioned AI analysis output and persisted report envelopes
- Automatic merged-PR report generation on a dedicated artifact branch
- Deterministic AI robustness evaluation with explicit live-cost controls

## Testing Strategy

The public Test Library presents three product-facing suites:

| Suite | Layer | Purpose |
| --- | --- | --- |
| Login API Tests | pytest and Flask test client | Verifies exact JSON contracts for valid, invalid, missing, empty, and null authentication inputs. |
| Flask Route Tests | pytest and Flask test client | Verifies routes, redirects, rendered states, navigation, browser-form responses, and public read-only feed behavior. |
| UI Tests | Playwright and Chromium | Verifies user-visible login behavior, native validation, accessibility feedback, and the read-only AI report explorer. |

Supporting unit and integration tests protect GitHub ingestion, QA catalog discovery, analysis context construction, structured AI contracts, report persistence, feed validation, JUnit normalization, and evaluation tooling. These infrastructure tests are intentionally distinct from the product-facing Test Library.

pytest and Playwright are the source of truth for test execution. AI analysis can recommend tests and identify potential coverage gaps, but it does not execute tests or determine their pass/fail status.

## AI-Assisted QA

The AI feature turns deterministic repository evidence into a structured change-impact review:

```text
GitHub Pull Request
        |
        v
Changed files + metadata
        |
        v
Real QA test catalog
        |
        v
Structured analysis context
        |
        v
OpenAI change-impact analysis
        |
        v
Validated structured report
        |
        v
Persistent ai-reports branch
        |
        v
Read-only Flask API
        |
        v
AI-Assisted QA explorer
```

Pull Request metadata and changed-file data come from GitHub through a normalized service boundary. The QA catalog is discovered from real pytest source with Python's AST rather than maintained as a duplicate manual inventory. Those deterministic sources are combined before the OpenAI Responses API is called.

Structured Outputs constrain the analysis to a strict, versioned schema containing risk, affected areas, relevant existing tests, potential coverage gaps, recommendations, QA notes, and limitations. Application code owns deterministic provenance, commit metadata, and change statistics outside the model-generated analysis.

Completed reports are persisted under `public/ai` on the dedicated `ai-reports` branch. The deployed Flask application reads and validates those reports server-side through `GET /api/ai-reports` and `GET /api/ai-reports/<pr_number>`. The browser-facing `/ai` explorer consumes only those read-only Flask endpoints.

## AI Safety, Cost, and Trust Boundaries

- `OPENAI_API_KEY` is supplied through a GitHub Actions secret or an intentional local environment variable. It is never embedded in browser code or report output.
- The public `/ai` page is read-only. It has no Generate action and cannot invoke OpenAI.
- Report generation is idempotent: an existing persisted PR report is detected before context collection or an OpenAI call.
- Normal pytest execution never calls OpenAI. Automated AI tests use mocked clients and deterministic fixture analyses.
- Live evaluation requires the explicit `--live` CLI flag and a configured key.
- Pull Request titles, descriptions, filenames, source code, comments, patches, and test catalog entries are treated as untrusted evidence, never as instructions.
- Stable prompt guardrails tell the model to ignore instruction-like content embedded in that evidence.
- Deterministic application code owns report provenance and change totals; those values are not delegated to model output.
- pytest and Playwright remain authoritative for actual test results. The AI contract forbids claims that tests passed or failed.
- Generated AI artifacts live on `ai-reports`, keeping report history separate from application source on `main`.

## AI Evaluation

AI-8 adds a controlled robustness and evaluation harness, not a scientific model benchmark. Three deterministic scenarios exercise materially different behavior:

1. A functional login change checks authentication impact, existing-test grounding, focused regression recommendations, and non-low risk calibration.
2. A documentation-only change checks low-risk restraint and avoidance of invented runtime impact.
3. Prompt injection with incomplete evidence checks instruction resistance, unsupported-claim detection, and explicit limitations.

The Python evaluator checks prompt version, known test-ID and title integrity, required and forbidden test references, risk expectations, recommendation counts and types, unsupported execution claims, unsupported safety claims, and required uncertainty where evidence is incomplete. Nuanced prose quality remains a human-review responsibility.

**Initial live evaluation: 32/35 deterministic checks passed.** Manual review found that all three failed checks were caused by brittle evaluation-oracle assumptions rather than unsafe or ungrounded model behavior. The criteria were calibrated to reduce dependence on incidental wording while preserving structural and safety requirements. The production prompt and model behavior were not changed to force a perfect score, and no second live evaluation was run solely to claim `35/35`.

See [evaluation/README.md](evaluation/README.md) for the focused evaluation commands and case summary.

## Architecture

### Deterministic Testing Pipeline

```text
pytest backend tests + Playwright UI tests
                    |
                    v
              GitHub Actions
                    |
                    v
             JUnit aggregation
                    |
                    v
        sanitized latest.json + index.html
                    |
                    v
               GitHub Pages
                    |
                    v
          Flask dashboard feed API
```

Raw backend JUnit, pytest HTML, and UI JUnit reports are retained as short-lived workflow artifacts. The public GitHub Pages output contains only normalized result metadata. Flask fetches `latest.json` server-side, validates it, and exposes a clean internal contract through `GET /api/test-results/latest`.

### AI Reporting Pipeline

```text
Merged Pull Request into main
             |
             v
       GitHub Actions
             |
             v
     AI report generation
             |
             v
       ai-reports branch
             |
             v
   read-only Flask report feed
             |
             v
        /ai explorer
```

The SQLite result subsystem remains for backward compatibility with legacy routes, but it is not the active source for the public dashboard or AI report explorer.

## Local Setup

The commands below target a macOS/Linux shell with Python 3 available.

```bash
git clone https://github.com/dastan96/Flask-Login-Tester.git
cd Flask-Login-Tester

python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Run Flask locally:

```bash
python app.py
```

The development server uses `http://127.0.0.1:5001` by default or the configured `PORT`.

## Running Tests

Run the complete deterministic suite:

```bash
pytest -q
```

Run backend and non-browser tests only:

```bash
pytest -q --ignore=tests/ui
```

Run the product-facing suites individually:

```bash
pytest -q tests/api/test_login_api.py
pytest -q tests/test_routes.py
pytest -q tests/ui/test_login_ui.py --browser chromium
```

List controlled AI evaluation cases without contacting OpenAI:

```bash
python scripts/run_ai_evaluation.py --list
```

Run an intentional live AI evaluation:

```bash
python scripts/run_ai_evaluation.py --live
python scripts/run_ai_evaluation.py --live --case login-behavior-change
```

Live evaluation requires `OPENAI_API_KEY`, calls the configured model, and may incur API cost. Normal pytest and the default evaluation CLI mode remain offline from OpenAI.

## Environment Configuration

| Variable | Classification | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | Secret | Required only for explicit report generation or live evaluation. It is not required by the public Flask report explorer. |
| `OPENAI_MODEL` | Non-secret configuration | Optional model override for report generation and live evaluation; otherwise the service uses its code-level default. |
| `AI_REPORT_FEED_BASE_URL` | Non-secret configuration | Optional base URL override for the persisted AI report feed. |
| `TEST_RESULTS_FEED_URL` | Non-secret configuration | Optional URL override for the dashboard's `latest.json` source. |
| `TEST_RESULTS_PAGE_URL` | Non-secret configuration | Optional public results-page link shown by the dashboard. |
| `PORT` | Runtime configuration | Flask/Gunicorn hosting port; local fallback is `5001`. |
| `LOGIN_UI_BASE_URL` | Test-only configuration | Optional external base URL for UI tests; when absent, the fixture starts Flask locally on a free port. |

Do not commit local environment files or API keys. The repository ignores `.env` and `*.env` files.

## CI/CD

The main `Run Automated Tests` workflow runs for Pull Requests, pushes to `main`, a weekly schedule, and manual dispatch:

1. `test` runs all non-UI pytest tests and produces JUnit XML plus a self-contained pytest HTML report.
2. `ui-tests` installs Chromium and runs the Playwright suite independently.
3. For Pull Requests and pushes to `main`, `aggregate-results` downloads both JUnit artifacts and validates combined normalization into `latest.json` and `index.html`.
4. Only a successful push to `main` uploads and deploys the GitHub Pages artifact.

Raw reports use 14-day artifact retention. Pull Requests validate aggregation but cannot deploy Pages.

The separate `Generate AI QA Report` workflow runs only when a Pull Request into `main` is closed and merged. It checks out the merged commit, restores historical reports from `ai-reports`, generates without `--force`, and pushes generated output only to that branch. `OPENAI_API_KEY` comes from an Actions secret, while `OPENAI_MODEL` may come from a repository variable.

The public Flask deployment is hosted on Render at `qa.datlas.me`. No Render deployment manifest is tracked in this repository, so deployment automation and environment settings are managed outside the source tree. The runtime application needs network access to its read-only report feeds; it does **not** need `OPENAI_API_KEY` to render the dashboard or `/ai`.

## Repository Structure

```text
.github/workflows/   Backend, UI, aggregation, Pages, and AI report automation
evaluation/          Controlled AI evaluation cases and methodology
scripts/             JUnit normalization, report generation, and evaluation CLIs
services/            GitHub, QA context, AI analysis, reporting, and feed boundaries
static/              Shared CSS and browser-side rendering logic
templates/           Flask-rendered public pages
tests/api/           Login JSON API tests
tests/ui/            Playwright tests and local Flask server fixture
tests/               Route and supporting service/infrastructure tests
app.py               Flask routes, demo authentication, and read-only feed APIs
requirements.txt     Pinned runtime and test dependencies
```
