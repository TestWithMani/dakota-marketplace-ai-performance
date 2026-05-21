# Dakota GPT Performance

Selenium automation for **Dakota Joe** chatbot performance testing on the Dakota Marketplace.

**Repository:** [https://github.com/TestWithMani/dakota_gpt_performance](https://github.com/TestWithMani/dakota_gpt_performance)

## Quick start

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Copy credentials into `.env` (see `config.py` for variable names):

```
DAKOTA_BASE_URL=
DAKOTA_USERNAME=
DAKOTA_PASSWORD=
```

Run smoke tests (3 smoke-marked prompts in `Prompts.csv`):

```bash
python chatbot_tester.py --smoke
```

Full prompt suite:

```bash
python chatbot_tester.py
```

## Outputs

- `Performance evaluation results.xlsx` — timing samples and run summaries
- `allure-results/` / `allure-report/` — Allure HTML report
- `screenshots/` — failures only

## CI

- **GitHub Actions:** `.github/workflows/ci.yml` (unit tests, no browser)
- **Jenkins:** `Jenkinsfile` (smoke E2E on Windows agent + Allure + email)

## Jenkins

Point the pipeline at this public repo — Jenkins checkout does not require GitHub credentials. You still need Dakota login secrets (`.env` or Jenkins env vars) for the smoke run.
