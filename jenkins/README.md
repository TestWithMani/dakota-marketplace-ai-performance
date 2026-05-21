# Jenkins setup

## 1. Create Dakota login credential

In Jenkins: **Manage Jenkins → Credentials → Global → Add Credentials**

| Field | Value |
|-------|--------|
| Kind | Username with password |
| ID | `dakota-marketplace-login` |
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
| `SMOKE_ONLY` | Smoke prompts only (default: true) |
| `BROWSER` | chrome / edge / firefox |
| `HEADLESS` | Headless browser |
| `RESPONSE_TIMEOUT` | Link wait seconds (default 100) |
| `RUNS_PER_OBJECT` | Samples per object (default 3) |
| `GENERATE_ALLURE` | Build HTML report |
| `SEND_EMAIL` | Email summary + Excel |
| `USE_DAKOTA_CREDENTIALS` | Use `dakota-marketplace-login` |

## Agent requirements

- Windows with Chrome (and Edge/Firefox if selected)
- Python 3.11+ on PATH
- Node.js + `npm install -g allure-commandline`
- Email Extension plugin
