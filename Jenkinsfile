// Dakota GPT Performance — parameterized Pipeline (SCM: Jenkinsfile from GitHub)
//
// Jenkins job setup (one-time):
//   1. Jenkins credential ID: sf-marketplace-creds (Dakota / Salesforce marketplace user)
//   2. Ensure Windows agent has Chrome (+ Edge/Firefox if used), JDK 8+, Python 3.11+
//      (Allure CLI is downloaded automatically; Node.js is not required)
//   3. Optional: set agent tool paths below or define on the agent as env vars
//
// Do NOT store Jenkins or Dakota passwords in this file.

pipeline {
    agent any

    options {
        buildDiscarder(logRotator(numToKeepStr: '20', artifactNumToKeepStr: '10'))
        timeout(time: 180, unit: 'MINUTES')
        timestamps()
        disableConcurrentBuilds()
    }

    parameters {
        choice(
            name: 'MARKET',
            choices: ['marketplace', 'sandbox', 'uat', 'custom'],
            description: 'Target Dakota environment (maps to base URL and optional prompts file)'
        )
        string(
            name: 'CUSTOM_BASE_URL',
            defaultValue: '',
            description: 'Required when MARKET=custom. Optional override for sandbox/uat if agent env vars are not set.'
        )
        booleanParam(
            name: 'SMOKE_ONLY',
            defaultValue: true,
            description: 'Run only Prompts.csv rows where Marker=smoke'
        )
        choice(
            name: 'BROWSER',
            choices: ['chrome', 'edge', 'firefox'],
            description: 'Browser engine (Chrome recommended on Windows agent)'
        )
        booleanParam(
            name: 'HEADLESS',
            defaultValue: false,
            description: 'Run browser headless (use true on agents without a display)'
        )
        string(
            name: 'RESPONSE_TIMEOUT',
            defaultValue: '100',
            description: 'Max seconds to wait for a report link per prompt'
        )
        string(
            name: 'RUNS_PER_OBJECT',
            defaultValue: '3',
            description: 'Performance timing samples per object type'
        )
        booleanParam(
            name: 'GENERATE_ALLURE',
            defaultValue: true,
            description: 'Generate HTML Allure report after the run'
        )
        booleanParam(
            name: 'SEND_EMAIL',
            defaultValue: true,
            description: 'Send summary email with Excel attachment'
        )
        string(
            name: 'EMAIL_RECIPIENTS',
            defaultValue: 'usman.arshad@rolustech.com',
            description: 'Primary comma-separated recipients for the report email'
        )
        string(
            name: 'ADDITIONAL_EMAIL_RECIPIENTS',
            defaultValue: '',
            description: 'Extra comma-separated recipients added to To (merged with EMAIL_RECIPIENTS)'
        )
        booleanParam(
            name: 'USE_DAKOTA_CREDENTIALS',
            defaultValue: true,
            description: 'Inject DAKOTA_USERNAME/PASSWORD from Jenkins credential sf-marketplace-creds'
        )
        string(
            name: 'GIT_BRANCH',
            defaultValue: 'main',
            description: 'Branch to build (when not using multibranch)'
        )
    }

    environment {
        VENV_PY         = "${WORKSPACE}\\venv\\Scripts\\python.exe"
        REPO_URL        = 'https://github.com/TestWithMani/dakota_gpt_performance.git'
        DAKOTA_CREDENTIAL_ID = 'sf-marketplace-creds'
        ALLURE_VERSION  = '2.32.0'
        ALLURE_HOME     = "${WORKSPACE}\\tools\\allure-${ALLURE_VERSION}"
        ALLURE_ZIP      = "${WORKSPACE}\\tools\\allure-${ALLURE_VERSION}.zip"
        ALLURE_DOWNLOAD = "https://github.com/allure-framework/allure2/releases/download/${ALLURE_VERSION}/allure-${ALLURE_VERSION}.zip"
    }

    stages {

        stage('Initialize') {
            steps {
                script {
                    def market = params.MARKET.trim().toLowerCase()
                    def customUrl = params.CUSTOM_BASE_URL?.trim() ?: ''
                    def marketplaceUrl = 'https://dakotanetworks.my.site.com/dakotaMarketplace/s/'
                    def resolvedUrl = ''

                    if (market == 'marketplace') {
                        resolvedUrl = marketplaceUrl
                    } else if (market == 'sandbox') {
                        resolvedUrl = customUrl ?: (env.DAKOTA_SANDBOX_URL ?: '').trim()
                    } else if (market == 'uat') {
                        resolvedUrl = customUrl ?: (env.DAKOTA_UAT_URL ?: '').trim()
                    } else if (market == 'custom') {
                        resolvedUrl = customUrl ?: (env.DAKOTA_BASE_URL ?: '').trim()
                        if (!resolvedUrl) {
                            error("MARKET=custom requires CUSTOM_BASE_URL (or DAKOTA_BASE_URL on the agent).")
                        }
                    } else {
                        error("Unknown MARKET '${params.MARKET}'.")
                    }

                    if (!resolvedUrl) {
                        error(
                            "No base URL for market '${market}'. " +
                            "Set CUSTOM_BASE_URL on this build or configure DAKOTA_SANDBOX_URL / DAKOTA_UAT_URL on the Jenkins agent."
                        )
                    }
                    if (!resolvedUrl.endsWith('/') && !resolvedUrl.contains('?')) {
                        resolvedUrl = resolvedUrl + '/'
                    }

                    env.DAKOTA_MARKET = market
                    env.DAKOTA_BASE_URL = resolvedUrl

                    currentBuild.description = "market=${market} | smoke=${params.SMOKE_ONLY} | ${params.BROWSER} | headless=${params.HEADLESS}"
                    echo "Market: ${market}"
                    echo "Base URL: ${resolvedUrl}"
                    echo "Credential ID: ${DAKOTA_CREDENTIAL_ID}"
                    echo "SMOKE_ONLY=${params.SMOKE_ONLY}, BROWSER=${params.BROWSER}, HEADLESS=${params.HEADLESS}"
                    echo "TIMEOUT=${params.RESPONSE_TIMEOUT}, RUNS=${params.RUNS_PER_OBJECT}"
                }
            }
        }

        stage('Checkout') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: "*/${params.GIT_BRANCH}"]],
                    userRemoteConfigs: [[url: "${REPO_URL}"]],
                    extensions: [[$class: 'CloneOption', shallow: true, depth: 1]]
                ])
            }
        }

        stage('Setup Python') {
            steps {
                bat '''
                    @echo off
                    cd /d "%WORKSPACE%"
                    python -m venv venv
                    call venv\\Scripts\\activate.bat
                    python -m pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install pytest allure-pytest
                    python --version
                '''
            }
        }

        stage('Run Dakota Automation') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                script {
                    def smokeFlag = params.SMOKE_ONLY ? '--smoke' : ''
                    def headlessFlag = params.HEADLESS ? '--headless' : ''
                    def baseUrlFlag = ''
                    if (params.MARKET == 'custom' || params.CUSTOM_BASE_URL?.trim()) {
                        baseUrlFlag = "--base-url \"${env.DAKOTA_BASE_URL}\""
                    }
                    def cmd = """
                        @echo off
                        cd /d "%WORKSPACE%"
                        call venv\\Scripts\\activate.bat
                        if exist allure-results rmdir /s /q allure-results
                        if exist allure-report  rmdir /s /q allure-report
                        echo Running automation for market ${env.DAKOTA_MARKET}...
                        "%VENV_PY%" -u chatbot_tester.py --market ${env.DAKOTA_MARKET} ${baseUrlFlag} ${smokeFlag} ${headlessFlag} --browser ${params.BROWSER} --timeout ${params.RESPONSE_TIMEOUT} --runs ${params.RUNS_PER_OBJECT}
                        echo Exit code: %ERRORLEVEL%
                        if errorlevel 1 exit /b %ERRORLEVEL%
                    """
                    def runEnv = [
                        "DAKOTA_MARKET=${env.DAKOTA_MARKET}",
                        "DAKOTA_BASE_URL=${env.DAKOTA_BASE_URL}",
                        "BROWSER=${params.BROWSER}",
                    ]
                    if (params.USE_DAKOTA_CREDENTIALS) {
                        withCredentials([
                            usernamePassword(
                                credentialsId: "${DAKOTA_CREDENTIAL_ID}",
                                usernameVariable: 'DAKOTA_USERNAME',
                                passwordVariable: 'DAKOTA_PASSWORD'
                            )
                        ]) {
                            withEnv(runEnv + [
                                "DAKOTA_USERNAME=${DAKOTA_USERNAME}",
                                "DAKOTA_PASSWORD=${DAKOTA_PASSWORD}",
                            ]) {
                                bat cmd
                            }
                        }
                    } else {
                        withEnv(runEnv) {
                            bat cmd
                        }
                    }
                }
                }
            }
        }
    }

    post {
        always {
            script {
                echo "Post-build: result=${currentBuild.currentResult}, market=${params.MARKET}"

                // --- Allure: always attempt (success or failure); uses Java + standalone CLI zip (no Node.js) ---
                if (params.GENERATE_ALLURE) {
                    catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                        bat """
                            @echo off
                            cd /d "%WORKSPACE%"
                            if not exist tools mkdir tools
                            if not exist allure-results mkdir allure-results
                            if not exist allure-results\\environment.properties (
                                echo Browser=${params.BROWSER}> allure-results\\environment.properties
                                echo Platform=windows>> allure-results\\environment.properties
                                echo Market=${env.DAKOTA_MARKET ?: params.MARKET}>> allure-results\\environment.properties
                                echo BaseURL=${env.DAKOTA_BASE_URL ?: ''}>> allure-results\\environment.properties
                            )
                            echo === Java (required for Allure) ===
                            where java >nul 2>&1
                            if errorlevel 1 (
                                echo ERROR: Java not found. Install JDK 8+ on this Jenkins agent.
                                exit /b 1
                            )
                            java -version
                            if not exist "${ALLURE_HOME}\\bin\\allure.bat" (
                                echo Downloading Allure ${ALLURE_VERSION}...
                                powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '${ALLURE_DOWNLOAD}' -OutFile '${ALLURE_ZIP}'"
                                if errorlevel 1 exit /b 1
                                powershell -NoProfile -Command "Expand-Archive -Path '${ALLURE_ZIP}' -DestinationPath '${WORKSPACE}\\tools' -Force"
                                if errorlevel 1 exit /b 1
                            )
                            if not exist "${ALLURE_HOME}\\bin\\allure.bat" (
                                echo ERROR: Allure CLI not found after extract.
                                exit /b 1
                            )
                            echo === Generating Allure report ===
                            call "${ALLURE_HOME}\\bin\\allure.bat" generate allure-results --clean -o allure-report
                            if errorlevel 1 exit /b 1
                            if not exist allure-report\\index.html (
                                echo ERROR: allure-report\\index.html missing.
                                exit /b 1
                            )
                            echo Allure report ready: allure-report\\index.html
                        """
                    }
                }

                // --- Archive artifacts ---
                if (fileExists('allure-report/index.html')) {
                    archiveArtifacts artifacts: 'allure-report/**', fingerprint: true, allowEmptyArchive: true
                } else {
                    echo 'Allure HTML report was not produced; skipping Allure archive.'
                }
                if (fileExists('Performance evaluation results.xlsx')) {
                    archiveArtifacts artifacts: 'Performance evaluation results.xlsx', fingerprint: true, allowEmptyArchive: true
                }

                // --- Email (exact HTML template) ---
                if (params.SEND_EMAIL) {
                    def pyScript = """
import os, json
results_dir = r'${env.WORKSPACE}\\\\allure-results'
total = passed = failed = skipped = 0
failed_names = []
if os.path.exists(results_dir):
    for f in os.listdir(results_dir):
        if f.endswith('-result.json'):
            with open(os.path.join(results_dir, f), encoding='utf-8') as fh:
                data = json.load(fh)
                status = data.get('status', '').lower()
                name = data.get('name', 'Unknown')
                total += 1
                if status == 'passed':
                    passed += 1
                elif status == 'failed':
                    failed += 1
                    failed_names.append(name)
                elif status == 'skipped':
                    skipped += 1
failed_names_str = '|'.join(failed_names) if failed_names else ''
print(str(total) + ',' + str(passed) + ',' + str(failed) + ',' + str(skipped) + ',' + failed_names_str)
"""
                    writeFile file: 'parse_results.py', text: pyScript
                    def parseOut = bat(
                        script: "@\"${VENV_PY}\" parse_results.py",
                        returnStdout: true
                    ).trim()
                    def lastLine = parseOut.readLines().last().trim()

                    def total = 0, passed = 0, failed = 0, skipped = 0, failedNames = ''
                    def p1 = lastLine.indexOf(',')
                    def p2 = lastLine.indexOf(',', p1 + 1)
                    def p3 = lastLine.indexOf(',', p2 + 1)
                    def p4 = lastLine.indexOf(',', p3 + 1)
                    if (p4 > 0) {
                        total = lastLine.substring(0, p1).toInteger()
                        passed = lastLine.substring(p1 + 1, p2).toInteger()
                        failed = lastLine.substring(p2 + 1, p3).toInteger()
                        skipped = lastLine.substring(p3 + 1, p4).toInteger()
                        failedNames = lastLine.substring(p4 + 1).replace('|', ', ')
                    }

                    def stats = [total: total, passed: passed, failed: failed, skipped: skipped]
                    def passRate = total > 0 ? (int)((passed * 100) / total) : 0
                    def durationString = currentBuild.durationString ?: '-'
                    def failedTestSummary = failed > 0 ?
                        "${failed} test(s) failed: ${failedNames}" :
                        'No failed tests or tab timeouts were detected in this run.'
                    def allureUrl = fileExists('allure-report/index.html') ?
                        "${env.BUILD_URL}artifact/allure-report/index.html" :
                        "${env.BUILD_URL} (Allure report was not generated — see console log)"
                    def dateStr = new Date().format('yyyy-MM-dd')
                    def marketLabel = env.DAKOTA_MARKET ?: params.MARKET
                    def modeLabel = params.SMOKE_ONLY ? 'Smoke' : 'Full'

                    def body = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Dakota Performance Report</title>
</head>
<body style="margin:0;padding:0;background:linear-gradient(140deg,#e0ecff 0%,#efe7ff 45%,#fff6e5 100%);font-family:'Segoe UI',Roboto,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding:24px;">
        <table width="760" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;border:1px solid #dbe3ee;box-shadow:0 14px 32px rgba(30,64,175,0.14);">
          <tr>
            <td style="padding:26px 30px;background:linear-gradient(135deg,#0f172a 0%,#1e40af 52%,#7c3aed 100%);color:#ffffff;">
              <h2 style="margin:0;font-size:30px;letter-spacing:0.2px;">Dakota Marketplace Performance</h2>
            </td>
          </tr>

          <tr>
            <td style="padding:24px 30px 10px;">
              <h3 style="margin:0 0 12px;color:#0f172a;font-size:17px;">Build Details</h3>
              <table width="100%" cellpadding="8" cellspacing="8" style="font-size:13px;margin-bottom:12px;">
                <tr align="center">
                  <td style="background:linear-gradient(180deg,#ccfbf1 0%,#99f6e4 100%);color:#134e4a;border-radius:12px;box-shadow:0 6px 14px rgba(20,184,166,0.22);"><div style="font-size:11px;letter-spacing:0.4px;">TOTAL</div><div style="font-size:24px;font-weight:800;">${stats.total}</div></td>
                  <td style="background:linear-gradient(180deg,#dcfce7 0%,#86efac 100%);color:#14532d;border-radius:12px;box-shadow:0 6px 14px rgba(34,197,94,0.25);"><div style="font-size:11px;letter-spacing:0.4px;">PASSED</div><div style="font-size:24px;font-weight:800;">${stats.passed}</div></td>
                  <td style="background:linear-gradient(180deg,#fee2e2 0%,#fca5a5 100%);color:#7f1d1d;border-radius:12px;box-shadow:0 6px 14px rgba(239,68,68,0.22);"><div style="font-size:11px;letter-spacing:0.4px;">FAILED</div><div style="font-size:24px;font-weight:800;">${stats.failed}</div></td>
                  <td style="background:linear-gradient(180deg,#ede9fe 0%,#c4b5fd 100%);color:#4c1d95;border-radius:12px;box-shadow:0 6px 14px rgba(124,58,237,0.22);"><div style="font-size:11px;letter-spacing:0.4px;">SKIPPED</div><div style="font-size:24px;font-weight:800;">${stats.skipped}</div></td>
                </tr>
              </table>
              <table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;color:#1e293b;border:1px solid #bfdbfe;border-radius:12px;overflow:hidden;background:linear-gradient(180deg,#f8fbff 0%,#ffffff 100%);table-layout:fixed;">
                <tr>
                  <td width="32%" style="padding:10px 12px;background:linear-gradient(180deg,#dbeafe 0%,#bfdbfe 100%);border-bottom:1px solid #bfdbfe;"><strong>Duration</strong></td>
                  <td style="padding:10px 12px;border-bottom:1px solid #dbe3f3;font-weight:600;color:#1e3a8a;">${durationString}</td>
                </tr>
                <tr>
                  <td style="padding:10px 12px;background:linear-gradient(180deg,#dbeafe 0%,#bfdbfe 100%);border-bottom:1px solid #bfdbfe;"><strong>Passed Percentage</strong></td>
                  <td style="padding:10px 12px;border-bottom:1px solid #dbe3f3;color:#0f766e;font-weight:700;">${passRate}%</td>
                </tr>
                <tr>
                  <td style="padding:10px 12px;background:linear-gradient(180deg,#dbeafe 0%,#bfdbfe 100%);"><strong>Failed Tests / Affected Tabs</strong></td>
                  <td style="padding:10px 12px;line-height:1.45;">${failedTestSummary}</td>
                </tr>
              </table>
            </td>
          </tr>

          <tr>
            <td style="padding:8px 30px 24px;">
              <h3 style="margin:0 0 12px;color:#0f172a;font-size:17px;">Report Access</h3>
              <table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;color:#1e293b;border:1px solid #c4b5fd;border-radius:10px;overflow:hidden;background:linear-gradient(180deg,#faf5ff 0%,#f3f0ff 100%);">
                <tr>
                  <td width="32%" style="padding:10px 12px;background:linear-gradient(180deg,#ede9fe 0%,#ddd6fe 100%);"><strong>Allure Report</strong></td>
                  <td style="padding:10px 12px;">
                    <a style="color:#6d28d9;text-decoration:underline;font-weight:700;" href="${allureUrl}">Open Allure Report</a>
                  </td>
                </tr>
              </table>
              <p style="margin:12px 0 0;color:#64748b;font-size:12px;">Please see the attached Excel performance sheet for detailed run metrics.</p>
            </td>
          </tr>

          <tr>
            <td style="padding:13px 30px;background:#0f172a;color:#cbd5e1;font-size:12px;">
              Jenkins CI/CD • Dakota Marketplace Test Framework
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

                    def emailToList = []
                    [params.EMAIL_RECIPIENTS, params.ADDITIONAL_EMAIL_RECIPIENTS].each { raw ->
                        if (raw?.trim()) {
                            raw.split(',').each { addr ->
                                def trimmed = addr.trim()
                                if (trimmed && !emailToList.contains(trimmed)) {
                                    emailToList << trimmed
                                }
                            }
                        }
                    }
                    def emailTo = emailToList.join(', ')
                    if (!emailTo) {
                        echo 'WARNING: No email recipients configured; skipping email.'
                    } else {
                        echo "Email To: ${emailTo}"
                        emailext(
                            to: "${emailTo}",
                            subject: "Dakota Marketplace Performance | ${marketLabel} | ${modeLabel} | ${dateStr}",
                            mimeType: 'text/html',
                            attachmentsPattern: 'Performance evaluation results.xlsx',
                            body: body
                        )
                    }
                }
            }
            echo "Build ${currentBuild.currentResult} — market=${params.MARKET}, smoke=${params.SMOKE_ONLY}, browser=${params.BROWSER}"
        }
        success {
            echo 'Pipeline finished (tests passed).'
        }
        failure {
            echo 'Pipeline finished with failures — Allure/email still attempted in post build.'
        }
    }
}
