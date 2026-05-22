// Dakota GPT Performance — parameterized Pipeline (SCM: Jenkinsfile from GitHub)
//
// Jenkins job setup (one-time):
//   1. Jenkins credential ID: sf-marketplace-creds (Dakota / Salesforce marketplace user)
//   2. Ensure Windows agent has Chrome (+ Edge/Firefox if used), Node, Allure CLI, Python 3.11+
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
        NODE_PATH  = "${env.NODE_PATH ?: 'C:\\Program Files\\nodejs'}"
        NPM_PATH   = "${env.NPM_PATH ?: 'C:\\Users\\wishma.khurram\\AppData\\Roaming\\npm'}"
        VENV_PY    = "${WORKSPACE}\\venv\\Scripts\\python.exe"
        ALLURE_CMD = "${env.ALLURE_CMD ?: 'allure'}"
        REPO_URL   = 'https://github.com/TestWithMani/dakota_gpt_performance.git'
        DAKOTA_CREDENTIAL_ID = 'sf-marketplace-creds'
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

        stage('Setup Node and Allure') {
            steps {
                bat """
                    @echo off
                    cd /d "%WORKSPACE%"
                    set "PATH=${NODE_PATH};${NPM_PATH};%PATH%"
                    if exist "${NODE_PATH}\\node.exe" set "PATH=${NODE_PATH};%PATH%"
                    if exist "%APPDATA%\\npm" set "PATH=%APPDATA%\\npm;%PATH%"
                    echo === Node.js ===
                    where node >nul 2>&1
                    if errorlevel 1 (
                        echo ERROR: Node.js not found. Install Node.js on this Jenkins agent or set NODE_PATH.
                        exit /b 1
                    )
                    node --version
                    echo === Java (required by Allure CLI) ===
                    where java >nul 2>&1
                    if errorlevel 1 (
                        echo ERROR: Java not found. Install JDK 8+ on this Jenkins agent and add java to PATH.
                        exit /b 1
                    )
                    java -version
                    echo === Allure CLI ===
                    where allure >nul 2>&1
                    if errorlevel 1 (
                        echo Installing allure-commandline via npm...
                        call npm install -g allure-commandline
                    )
                    where allure >nul 2>&1
                    if errorlevel 1 (
                        echo ERROR: Allure CLI not available after npm install.
                        exit /b 1
                    )
                    allure --version
                """
            }
        }

        stage('Run Dakota Automation') {
            steps {
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
                        set PATH=${NODE_PATH};${NPM_PATH};%PATH%
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

        stage('Generate Allure Report') {
            when {
                expression { return params.GENERATE_ALLURE }
            }
            steps {
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    bat """
                        @echo off
                        cd /d "%WORKSPACE%"
                        set "PATH=${NODE_PATH};${NPM_PATH};%PATH%"
                        if exist "${NODE_PATH}\\node.exe" set "PATH=${NODE_PATH};%PATH%"
                        if exist "%APPDATA%\\npm" set "PATH=%APPDATA%\\npm;%PATH%"
                        if not exist allure-results (
                            echo ERROR: allure-results folder missing.
                            exit /b 1
                        )
                        node --version
                        java -version
                        allure generate allure-results --clean -o allure-report
                        if errorlevel 1 exit /b 1
                        if not exist allure-report\\index.html (
                            echo ERROR: allure-report\\index.html was not created.
                            exit /b 1
                        )
                        echo Allure report ready.
                        dir allure-report
                    """
                }
            }
        }

        stage('Archive Reports') {
            steps {
                script {
                    if (fileExists('allure-report/index.html')) {
                        archiveArtifacts artifacts: 'allure-report/**', fingerprint: true, allowEmptyArchive: true
                    } else {
                        echo 'Skipping Allure archive (report not generated).'
                    }
                    if (fileExists('Performance evaluation results.xlsx')) {
                        archiveArtifacts artifacts: 'Performance evaluation results.xlsx', fingerprint: true, allowEmptyArchive: true
                    }
                }
            }
        }

        stage('Send Email Report') {
            when {
                expression { return params.SEND_EMAIL }
            }
            steps {
                script {
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
                    def result = bat(
                        script: "@\"${VENV_PY}\" parse_results.py",
                        returnStdout: true
                    ).trim()

                    def lastLine = result.readLines().last().trim()
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

                    def passedPct = total > 0 ? (int)((passed * 100) / total) : 0
                    def failedList = failed > 0 ? "${failed} failed: ${failedNames}" : 'No failures detected.'
                    def allureUrl = "${env.BUILD_URL}artifact/allure-report/index.html"
                    def duration = currentBuild.durationString
                    def dateStr = new Date().format('yyyy-MM-dd')
                    def modeLabel = params.SMOKE_ONLY ? 'Smoke' : 'Full'
                    def marketLabel = env.DAKOTA_MARKET ?: params.MARKET

                    def emailBody = """<!DOCTYPE html><html><body style="font-family:Segoe UI,Arial,sans-serif;">
<h2>Dakota GPT Performance — ${modeLabel}</h2>
<p><b>Build:</b> ${env.JOB_NAME} #${env.BUILD_NUMBER}<br/>
<b>Market:</b> ${marketLabel}<br/>
<b>Base URL:</b> ${env.DAKOTA_BASE_URL}<br/>
<b>Browser:</b> ${params.BROWSER} (headless=${params.HEADLESS})<br/>
<b>Duration:</b> ${duration}</p>
<table cellpadding="8" style="border-collapse:collapse;">
<tr><td><b>Total</b></td><td>${total}</td></tr>
<tr><td><b>Passed</b></td><td>${passed} (${passedPct}%)</td></tr>
<tr><td><b>Failed</b></td><td>${failed}</td></tr>
<tr><td><b>Skipped</b></td><td>${skipped}</td></tr>
</table>
<p>${failedList}</p>
<p><a href="${allureUrl}">Open Allure Report</a></p>
<p style="color:#64748b;font-size:12px;">Excel metrics attached when generated.</p>
</body></html>"""

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
                        error('SEND_EMAIL is enabled but no recipients in EMAIL_RECIPIENTS or ADDITIONAL_EMAIL_RECIPIENTS.')
                    }
                    echo "Email To: ${emailTo}"

                    emailext(
                        to: "${emailTo}",
                        subject: "Dakota GPT Performance | ${marketLabel} | ${modeLabel} | ${dateStr}",
                        mimeType: 'text/html',
                        attachmentsPattern: 'Performance evaluation results.xlsx',
                        body: emailBody
                    )
                }
            }
        }
    }

    post {
        always {
            echo "Build ${currentBuild.currentResult} — market=${params.MARKET}, smoke=${params.SMOKE_ONLY}, browser=${params.BROWSER}"
        }
        success {
            echo 'Pipeline completed successfully.'
        }
        failure {
            echo 'Pipeline failed — review console log and archived Allure report.'
        }
    }
}
