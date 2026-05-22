# Dakota GPT Performance

Selenium automation for **Dakota Joe** chatbot performance testing on the Dakota Marketplace.

**Repository:** [https://github.com/TestWithMani/dakota_gpt_performance](https://github.com/TestWithMani/dakota_gpt_performance)

## Quick start

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in credentials:

```
DAKOTA_BASE_URL=
DAKOTA_USERNAME=
DAKOTA_PASSWORD=
```

Run modes (`--run-mode`):

| Mode | What runs |
|------|-----------|
| `smoke` | Rows with `Marker=smoke` in the active prompts file (default) |
| `test` | Single RIA case from `Prompts.test.csv` (any market URL) |
| `all` | Every prompt in the active prompts file |

```bash
python chatbot_tester.py --run-mode smoke
python chatbot_tester.py --run-mode all
python chatbot_tester.py --market test
```

**Test market** (`--market test`) uses `Prompts.test.csv` — one RIA prompt (`Show me ria in usa`), **1 run** only.

## Outputs

- `Performance evaluation results.xlsx` — timing samples and run summaries (benchmark in column E on Run summary rows)
- `Benchmarks.csv` — default max seconds per object type (used when Excel has no benchmark yet; Excel overrides)
- `allure-results/` / `allure-report/` — Allure HTML report
- `screenshots/` — failures only

## CI

- **GitHub Actions:** `.github/workflows/ci.yml` (unit tests, no browser)
- **Jenkins:** `Jenkinsfile` (smoke E2E on Windows agent + Allure + email)

## Jenkins

Parameterized pipeline: see `Jenkinsfile` and `jenkins/README.md`.

1. Create credential ID **`sf-marketplace-creds`** (Dakota / Salesforce marketplace username/password).
2. Create job **`dakota-gpt-performance`** from SCM (`Jenkinsfile` on `main`).
3. Run with parameters: **MARKET**, **RUN_MODE** (smoke / test / all), **BROWSER**, **HEADLESS**, etc.

```powershell
$env:JENKINS_URL = 'http://your-jenkins:8080'
$env:JENKINS_USER = 'your-user'
$env:JENKINS_PASSWORD = 'your-password'
.\jenkins\create-pipeline-job.ps1
```
