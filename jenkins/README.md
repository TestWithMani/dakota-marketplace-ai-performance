# Jenkins setup

## 1. Create Dakota login credential

In Jenkins: **Manage Jenkins → Credentials → Global → Add Credentials**

| Field | Value |
|-------|--------|
| Kind | Username with password |
| ID | `sf-marketplace-creds` |
| Username | Dakota marketplace user |
| Password | Dakota password |

## 2. Create the pipeline job

From PowerShell (do **not** commit passwords):

```powershell
$env:JENKINS_URL = 'http://110.93.205.18:8080'
$env:JENKINS_USER = 'your-jenkins-username'
$env:JENKINS_PASSWORD = 'your-jenkins-password'
.\jenkins\create-pipeline-job.ps1
```

Or manually: **New Item → Pipeline → Pipeline script from SCM → Git**  
Repository: `https://github.com/TestWithMani/dakota_gpt_performance`  
Branch: `main`  
Script Path: `Jenkinsfile`

## 3. Build parameters (on each run)

| Parameter | Description |
|-----------|-------------|
| `MARKET` | `marketplace`, `test`, `sandbox`, `uat`, `custom` |
| `RUN_MODE` | `smoke`, `test`, or `all` — `test` loads `Prompts.test.csv` (1 RIA prompt, 1 run) on any market |
| `CUSTOM_BASE_URL` | URL override (required for `custom`; optional for sandbox/uat/test) |
| `BROWSER` | chrome / edge / firefox |
| `HEADLESS` | Headless browser |
| `RESPONSE_TIMEOUT` | Link wait seconds (default 100) |
| `RUNS_PER_OBJECT` | Samples per object (default 3) |
| `GENERATE_ALLURE` | Build HTML report |
| `SEND_EMAIL` | Email summary + Excel |
| `EMAIL_RECIPIENTS` | Primary To list (comma-separated) |
| `ADDITIONAL_EMAIL_RECIPIENTS` | Extra To addresses merged with primary list |
| `USE_DAKOTA_CREDENTIALS` | Use `sf-marketplace-creds` for login |

## Market URLs on the Jenkins agent (optional)

Set global environment variables on the agent or pass `CUSTOM_BASE_URL` per build:

| Market | URL source |
|--------|------------|
| `marketplace` | Built-in production URL · `Prompts.csv` |
| `test` | Production URL (or `DAKOTA_TEST_URL`) · **`Prompts.test.csv`** (1 RIA prompt, 1 run) |
| `sandbox` | `DAKOTA_SANDBOX_URL` or `CUSTOM_BASE_URL` |
| `uat` | `DAKOTA_UAT_URL` or `CUSTOM_BASE_URL` |
| `custom` | `CUSTOM_BASE_URL` (required) |

Optional per-market prompt files: `Prompts.test.csv`, `Prompts.sandbox.csv`, `Prompts.uat.csv`.

## Agent requirements

- Windows with Chrome (and Edge/Firefox if selected)
- Python 3.11+ on PATH
- **JDK 8+** on PATH (`java -version` must work)
- Email Extension plugin

**Allure** is downloaded automatically (standalone zip from GitHub) in the **post-build** step. **Node.js is not required.**

Allure and email run in **`post { always }`** — even when the automation stage fails.

If Allure generation fails, the build is marked **UNSTABLE** but email and Excel archive still run.
