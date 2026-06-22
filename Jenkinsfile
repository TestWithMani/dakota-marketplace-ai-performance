// Dakota GPT Performance — parameterized Pipeline (SCM: Jenkinsfile from GitHub)
//
// Jenkins job setup (one-time):
//   1. Credential ID: sf-marketplace-creds (Dakota / Salesforce marketplace user)
//   2. Windows agent: Chrome, JDK 8+, Python 3.11+ (Allure CLI downloaded automatically)
//   3. Email Extension plugin for HTML report emails
//
// Do NOT store passwords in this file.

pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '30', artifactNumToKeepStr: '30'))
        timeout(time: 180, unit: 'MINUTES')
    }

    triggers {
        cron('0 12 * * 1')
    }

    parameters {
        choice(
            name: 'MARKET',
            choices: ['marketplace', 'test', 'sandbox', 'uat', 'custom'],
            description: 'Environment: test = single RIA prompt (Prompts.test.csv); marketplace = production'
        )
        choice(
            name: 'RUN_MODE',
            choices: ['smoke', 'test', 'all'],
            description: 'Prompts: smoke (Marker=smoke), test (Prompts.test.csv / 1 run), all (full CSV)'
        )
        string(
            name: 'CUSTOM_BASE_URL',
            defaultValue: '',
            description: 'Required when MARKET=custom. Optional override for sandbox/uat/test.'
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
            description: 'Performance timing samples per object (forced to 1 for MARKET=test or RUN_MODE=test)'
        )
        booleanParam(
            name: 'FRESH_REPORT_OUTPUT',
            defaultValue: false,
            description: 'Clear previous Excel / Allure artifacts before this run'
        )
        booleanParam(
            name: 'GENERATE_ALLURE',
            defaultValue: true,
            description: 'Generate and archive HTML Allure report after the run'
        )
        booleanParam(
            name: 'SEND_EMAIL',
            defaultValue: true,
            description: 'Send HTML email summary after pipeline completion'
        )
        string(
            name: 'EMAIL_RECIPIENTS',
            defaultValue: 'draftcrm@rolustech.com',
            description: 'Primary comma-separated recipients for the report email'
        )
        string(
            name: 'ADDITIONAL_EMAIL_RECIPIENTS',
            defaultValue: '',
            description: 'Extra comma-separated recipients (merged with EMAIL_RECIPIENTS)'
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
        VENV_PY              = "${WORKSPACE}\\venv\\Scripts\\python.exe"
        REPO_URL             = 'https://github.com/TestWithMani/dakota_gpt_performance.git'
        DAKOTA_CREDENTIAL_ID = 'sf-marketplace-creds'
        ALLURE_VERSION       = '2.32.0'
        ALLURE_HOME          = "${WORKSPACE}\\tools\\allure-${ALLURE_VERSION}"
        ALLURE_ZIP           = "${WORKSPACE}\\tools\\allure-${ALLURE_VERSION}.zip"
        ALLURE_DOWNLOAD      = "https://github.com/allure-framework/allure2/releases/download/${ALLURE_VERSION}/allure-${ALLURE_VERSION}.zip"
        EXCEL_ARTIFACT       = 'Performance evaluation results.xlsx'
    }

    stages {

        stage('Initialize') {
            steps {
                script {
                    def cfg = getEffectiveRunConfig()
                    validateRuntimeParameters(
                        cfg.market as String,
                        cfg.runMode as String,
                        cfg.browser as String,
                        cfg.responseTimeout as String,
                        cfg.runsPerObject as String
                    )
                    env.DAKOTA_MARKET = cfg.market
                    env.DAKOTA_BASE_URL = cfg.baseUrl
                    env.DAKOTA_RUN_MODE = cfg.runMode
                    env.EFFECTIVE_RUNS = cfg.runsPerObject

                    currentBuild.description = "market=${cfg.market} | mode=${cfg.runMode} | ${cfg.browser} | headless=${cfg.headless}"
                    echo "Market: ${cfg.market}"
                    echo "Run mode: ${cfg.runMode}"
                    echo "Base URL: ${cfg.baseUrl}"
                    echo "Credential ID: ${DAKOTA_CREDENTIAL_ID}"
                    echo "BROWSER=${cfg.browser}, HEADLESS=${cfg.headless}"
                    echo "TIMEOUT=${cfg.responseTimeout}, RUNS=${cfg.runsPerObject}"
                    echo "FRESH_REPORT_OUTPUT=${cfg.freshReportOutput}, GENERATE_ALLURE=${cfg.generateAllure}"
                    if (cfg.scheduledBuild) {
                        echo 'Scheduled run detected: applying Monday 12:00 PM preset parameters.'
                    }
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
                    if not exist venv python -m venv venv
                    call venv\\Scripts\\activate.bat
                    python -m pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install pytest allure-pytest
                    python --version
                '''
            }
        }

        stage('Prepare Report Directories') {
            steps {
                script {
                    def cfg = getEffectiveRunConfig()
                    if (cfg.freshReportOutput) {
                        echo 'Fresh report mode: clearing previous Excel and Allure artifacts.'
                        bat '''
                            @echo off
                            cd /d "%WORKSPACE%"
                            if exist "%EXCEL_ARTIFACT%" del /q "%EXCEL_ARTIFACT%"
                            if exist allure-results rmdir /s /q allure-results
                            if exist allure-report rmdir /s /q allure-report
                        '''
                    } else {
                        bat '''
                            @echo off
                            cd /d "%WORKSPACE%"
                            if not exist allure-results mkdir allure-results
                        '''
                    }
                }
            }
        }

        stage('Run Dakota Automation') {
            steps {
                script {
                    def cfg = getEffectiveRunConfig()
                    def headlessFlag = cfg.headless ? '--headless' : ''
                    def baseUrlFlag = ''
                    if (cfg.market == 'custom' || params.CUSTOM_BASE_URL?.trim()) {
                        baseUrlFlag = "--base-url \"${cfg.baseUrl}\""
                    }

                    def cmd = """
                        @echo off
                        cd /d "%WORKSPACE%"
                        call venv\\Scripts\\activate.bat
                        if not exist allure-results mkdir allure-results
                        echo Running automation: market=${cfg.market} run-mode=${cfg.runMode}...
                        "%VENV_PY%" -u chatbot_tester.py --market ${cfg.market} --run-mode ${cfg.runMode} ${baseUrlFlag} ${headlessFlag} --browser ${cfg.browser} --timeout ${cfg.responseTimeout} --runs ${cfg.runsPerObject}
                        echo Exit code: %ERRORLEVEL%
                        if errorlevel 1 exit /b %ERRORLEVEL%
                    """

                    def runEnv = [
                        "DAKOTA_MARKET=${cfg.market}",
                        "DAKOTA_BASE_URL=${cfg.baseUrl}",
                        "DAKOTA_RUN_MODE=${cfg.runMode}",
                        "BROWSER=${cfg.browser}",
                    ]

                    catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                        if (cfg.useCredentials) {
                            withCredentials([
                                usernamePassword(
                                    credentialsId: "${DAKOTA_CREDENTIAL_ID}",
                                    usernameVariable: 'DAKOTA_USERNAME',
                                    passwordVariable: 'DAKOTA_PASSWORD'
                                )
                            ]) {
                                withEnv(runEnv + [
                                    'DAKOTA_USERNAME=' + DAKOTA_USERNAME,
                                    'DAKOTA_PASSWORD=' + DAKOTA_PASSWORD,
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

        stage('Publish Reports') {
            steps {
                script {
                    def cfg = getEffectiveRunConfig()
                    if (cfg.generateAllure) {
                        ensureAllureEnvironmentProperties(cfg.market as String, cfg.baseUrl as String, cfg.browser as String)
                        if (fileExists('allure-results')) {
                            try {
                                allure([
                                    includeProperties: false,
                                    jdk: '',
                                    properties: [],
                                    reportBuildPolicy: 'ALWAYS',
                                    results: [[path: 'allure-results']],
                                    reportName: 'Allure Report',
                                ])
                                echo "Allure plugin report: ${env.BUILD_URL}allure/"
                            } catch (MissingMethodException ex) {
                                echo 'Allure Jenkins plugin not installed; generating standalone HTML report.'
                                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                                    generateAllureReport(cfg.market as String, cfg.baseUrl as String, cfg.browser as String)
                                }
                            }
                        } else {
                            echo 'Skipping Allure publish: allure-results directory not found.'
                        }
                    }
                    if (fileExists('allure-report/index.html')) {
                        archiveArtifacts artifacts: 'allure-report/**', fingerprint: true, allowEmptyArchive: true
                    }
                    if (fileExists(env.EXCEL_ARTIFACT)) {
                        archiveArtifacts artifacts: "${env.EXCEL_ARTIFACT}", fingerprint: true, allowEmptyArchive: true
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                def cfg = getEffectiveRunConfig()
                logTestSummaryToConsole('Post pipeline summary')
                if (cfg.sendEmail) {
                    sendEmailNotification(
                        currentBuild.currentResult ?: 'UNKNOWN',
                        cfg.emailRecipients as String,
                        cfg.additionalEmailRecipients as String
                    )
                }
                echo "Build ${currentBuild.currentResult} — market=${cfg.market}, mode=${cfg.runMode}, browser=${cfg.browser}"
            }
        }
        success {
            echo 'Pipeline finished (automation passed).'
        }
        failure {
            echo 'Pipeline finished with failures — reports/email were still attempted where configured.'
        }
    }
}

// ---------------------------------------------------------------------------
// Shared helpers (same style as salesforce_tab_performance Jenkinsfile)
// ---------------------------------------------------------------------------

def isScheduledBuild() {
    try {
        def timerCauses = currentBuild?.getBuildCauses('hudson.triggers.TimerTrigger$TimerTriggerCause') ?: []
        if (!timerCauses.isEmpty()) {
            return true
        }
        def genericCauses = currentBuild?.getBuildCauses() ?: []
        return genericCauses.any { cause ->
            def cls = cause?._class ?: ''
            return cls.contains('TimerTriggerCause')
        }
    } catch (Exception ignored) {
        return false
    }
}

def getEffectiveRunConfig() {
    def scheduled = isScheduledBuild()
    def market = scheduled ? 'marketplace' : (params.MARKET ?: 'marketplace').trim().toLowerCase()
    def runMode = scheduled ? 'all' : (params.RUN_MODE ?: 'smoke').trim().toLowerCase()
    def runsPerObject = scheduled ? '3' : (params.RUNS_PER_OBJECT ?: '3').trim()

    if (market == 'test') {
        runMode = 'all'
        runsPerObject = '1'
    } else if (runMode == 'test') {
        runsPerObject = '1'
    }

    return [
        scheduledBuild           : scheduled,
        market                   : market,
        runMode                  : runMode,
        baseUrl                  : resolveMarketUrl(market, params.CUSTOM_BASE_URL?.trim() ?: ''),
        browser                  : scheduled ? 'chrome' : (params.BROWSER ?: 'chrome').trim().toLowerCase(),
        headless                 : scheduled ? false : (params.HEADLESS as boolean),
        responseTimeout          : scheduled ? '100' : (params.RESPONSE_TIMEOUT ?: '100').trim(),
        runsPerObject            : runsPerObject,
        freshReportOutput        : scheduled ? false : (params.FRESH_REPORT_OUTPUT as boolean),
        generateAllure           : scheduled ? true : (params.GENERATE_ALLURE as boolean),
        sendEmail                : scheduled ? true : (params.SEND_EMAIL as boolean),
        emailRecipients          : scheduled
            ? 'pstanley@dakota.com'
            : (params.EMAIL_RECIPIENTS ?: '').trim(),
        additionalEmailRecipients: scheduled
            ? 'omer.shafiq@rolustech.net, dakota.ai@rolustech.com, wishma.khurram@rolustech.com'
            : (params.ADDITIONAL_EMAIL_RECIPIENTS ?: '').trim(),
        useCredentials           : scheduled ? true : (params.USE_DAKOTA_CREDENTIALS as boolean),
    ]
}

def resolveMarketUrl(String market, String customUrl) {
    def marketplaceUrl = 'https://dakotanetworks.my.site.com/dakotaMarketplace/s/'
    def resolvedUrl = ''

    if (market == 'marketplace') {
        resolvedUrl = marketplaceUrl
    } else if (market == 'test') {
        resolvedUrl = customUrl ?: (env.DAKOTA_TEST_URL ?: '').trim() ?: marketplaceUrl
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
        error("Unknown MARKET '${market}'.")
    }

    if (!resolvedUrl) {
        error(
            "No base URL for market '${market}'. " +
            "Set CUSTOM_BASE_URL on this build or configure DAKOTA_SANDBOX_URL / DAKOTA_UAT_URL on the agent."
        )
    }
    if (!resolvedUrl.endsWith('/') && !resolvedUrl.contains('?')) {
        resolvedUrl = resolvedUrl + '/'
    }
    return resolvedUrl
}

def validateRuntimeParameters(
    String market,
    String runMode,
    String browser,
    String responseTimeout,
    String runsPerObject
) {
    if (!(market in ['marketplace', 'test', 'sandbox', 'uat', 'custom'])) {
        error("Invalid MARKET='${market}'.")
    }
    if (!(runMode in ['smoke', 'test', 'all'])) {
        error("Invalid RUN_MODE='${runMode}'. Allowed: smoke, test, all.")
    }
    if (!(browser in ['chrome', 'edge', 'firefox'])) {
        error("BROWSER must be chrome, edge, or firefox. Got '${browser}'.")
    }
    if (!(responseTimeout ==~ /^\d+$/)) {
        error("RESPONSE_TIMEOUT must be a non-negative integer, got '${responseTimeout}'.")
    }
    if (!(runsPerObject ==~ /^\d+$/)) {
        error("RUNS_PER_OBJECT must be a non-negative integer, got '${runsPerObject}'.")
    }
    if ((runsPerObject as int) < 1) {
        error("RUNS_PER_OBJECT must be >= 1, got '${runsPerObject}'.")
    }
}

def readLastStdoutLine(String output) {
    if (!output?.trim()) {
        return ''
    }
    def lines = output.readLines().collect { it?.trim() }.findAll { it }
    return lines ? lines.last() : ''
}

def formatEmailSubjectDate() {
    // Use Python (already on agent) — SimpleDateFormat/Locale are blocked by Jenkins sandbox.
    try {
        writeFile file: 'format_email_date.py', text: '''
from datetime import date
today = date.today()
print(f"{today.strftime('%B')} {today.day}, {today.year}")
'''
        def out = bat(
            script: "@\"${env.VENV_PY}\" format_email_date.py",
            returnStdout: true
        ).trim()
        def line = readLastStdoutLine(out)
        if (line) {
            return line
        }
    } catch (Exception ex) {
        echo "Email date formatting fallback: ${ex.message}"
    }
    return new Date().format('yyyy-MM-dd')
}

def getTestStatistics() {
    def stats = [total: 0, passed: 0, failed: 0, skipped: 0]
    def resultsDir = "${env.WORKSPACE}\\allure-results"
    if (!fileExists('allure-results')) {
        echo 'allure-results not found; email stats will be zero.'
        return stats
    }

    try {
        def pyScript = """
import os, json
results_dir = r'${env.WORKSPACE}\\\\allure-results'
total = passed = failed = skipped = 0
if os.path.exists(results_dir):
    for f in os.listdir(results_dir):
        if f.endswith('-result.json'):
            with open(os.path.join(results_dir, f), encoding='utf-8') as fh:
                data = json.load(fh)
                status = data.get('status', '').lower()
                total += 1
                if status == 'passed':
                    passed += 1
                elif status == 'failed':
                    failed += 1
                elif status == 'skipped':
                    skipped += 1
print(','.join([str(total), str(passed), str(failed), str(skipped)]))
"""
        writeFile file: 'parse_allure_stats.py', text: pyScript
        def parseOut = bat(
            script: "@\"${env.VENV_PY}\" parse_allure_stats.py",
            returnStdout: true
        ).trim()
        def lastLine = readLastStdoutLine(parseOut)
        if (!lastLine) {
            return stats
        }
        def parts = lastLine.split(',')
        if (parts.size() >= 4) {
            stats.total = (parts[0] ?: '0') as int
            stats.passed = (parts[1] ?: '0') as int
            stats.failed = (parts[2] ?: '0') as int
            stats.skipped = (parts[3] ?: '0') as int
        }
    } catch (Exception ex) {
        echo "Could not parse Allure stats: ${ex.message}"
    }
    return stats
}

def getFailedTestNames() {
    def failures = []
    if (!fileExists('allure-results')) {
        return failures
    }
    try {
        def pyScript = """
import os, json
results_dir = r'${env.WORKSPACE}\\\\allure-results'
names = []
if os.path.exists(results_dir):
    for f in os.listdir(results_dir):
        if f.endswith('-result.json'):
            with open(os.path.join(results_dir, f), encoding='utf-8') as fh:
                data = json.load(fh)
                if data.get('status', '').lower() == 'failed':
                    names.append(data.get('name', 'Unknown'))
print('|'.join(names))
"""
        writeFile file: 'parse_allure_failures.py', text: pyScript
        def parseOut = bat(
            script: "@\"${env.VENV_PY}\" parse_allure_failures.py",
            returnStdout: true
        ).trim()
        def lastLine = readLastStdoutLine(parseOut)
        if (lastLine) {
            failures = lastLine.tokenize('|').findAll { it?.trim() }.unique()
        }
    } catch (Exception ex) {
        echo "Could not parse failed test names: ${ex.message}"
    }
    return failures
}

def logTestSummaryToConsole(String label = 'Test summary') {
    def stats = getTestStatistics()
    echo """
================ ${label} ================
Total  : ${stats.total}
Passed : ${stats.passed}
Failed : ${stats.failed}
Skipped: ${stats.skipped}
==========================================
""".stripIndent()
}

def ensureAllureEnvironmentProperties(String market, String baseUrl, String browser) {
    bat """
        @echo off
        cd /d "%WORKSPACE%"
        if not exist allure-results mkdir allure-results
        echo Browser=${browser}> allure-results\\environment.properties
        echo Platform=windows>> allure-results\\environment.properties
        echo Market=${market}>> allure-results\\environment.properties
        echo BaseURL=${baseUrl}>> allure-results\\environment.properties
    """
}

def generateAllureReport(String market, String baseUrl, String browser) {
    ensureAllureEnvironmentProperties(market, baseUrl, browser)
    bat """
        @echo off
        cd /d "%WORKSPACE%"
        if not exist tools mkdir tools
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

def collectRecipientEmails(String defaultEmail, String additionalEmails) {
    def recipients = []
    def seen = [] as Set

    [defaultEmail, additionalEmails].findAll { it?.trim() }.each { source ->
        source
            .split(/[,\s;]+/)
            .collect { it.trim() }
            .findAll { it }
            .each { mail ->
                def normalized = mail.toLowerCase()
                if (!seen.contains(normalized)) {
                    seen.add(normalized)
                    recipients.add(mail)
                }
            }
    }

    echo "Email recipients resolved: ${recipients.join(', ')}"
    return recipients
}

def sendEmailNotification(
    String buildStatus,
    String defaultEmail,
    String additionalEmails
) {
    def stats = getTestStatistics()
    def failedTests = getFailedTestNames()
    def actualStatus = currentBuild.result ?: buildStatus

    if (!(actualStatus in ['FAILURE', 'ABORTED'])) {
        if (stats.total == 0) {
            actualStatus = 'UNSTABLE'
        } else if (stats.failed > 0) {
            actualStatus = 'FAILURE'
        } else {
            actualStatus = 'SUCCESS'
        }
    }

    def recipients = collectRecipientEmails(defaultEmail, additionalEmails)
    if (recipients.isEmpty()) {
        echo 'No email recipients configured; skipping email notification.'
        return
    }

    def jobUrl = env.BUILD_URL ?: ''
    def buildUrlBase = jobUrl.endsWith('/') ? jobUrl : "${jobUrl}/"
    def excelPath = env.EXCEL_ARTIFACT ?: 'Performance evaluation results.xlsx'
    def excelExists = fileExists(excelPath)
    def allureUrl = "${buildUrlBase}allure/"
    def durationString = (currentBuild.durationString ?: 'N/A').replace(' and counting', '')
    def passRate = stats.total > 0 ? ((stats.passed * 100) / stats.total) as int : 0
    def dateStr = formatEmailSubjectDate()

    def failedTestSummary = failedTests
        ? failedTests.collect { item ->
            "<div style=\"margin:0 0 6px;padding:7px 10px;background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;color:#9a3412;\">${item}</div>"
        }.join('')
        : '<span style="color:#065f46;font-weight:600;">No failed tests or tab timeouts were detected in this run.</span>'

    def subject = "Dakota GPT Performance | ${dateStr}"

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
              <h2 style="margin:0;font-size:30px;letter-spacing:0.2px;">Dakota GPT JOE BOT Performance</h2>
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
                  <td style="padding:10px 12px;background:linear-gradient(180deg,#dbeafe 0%,#bfdbfe 100%);"><strong>Failed Tests / Prompts</strong></td>
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
              Jenkins CI/CD • Dakota GPT Performance Framework
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

    def baseArgs = [
        subject         : subject,
        body            : body,
        mimeType        : 'text/html',
        attachLog       : false,
        compressLog     : false,
        attachmentsPattern: excelExists ? excelPath : '',
    ]

    def recipientList = recipients.join(', ')
    echo "Sending email to: ${recipientList}"

    try {
        emailext(baseArgs + [to: recipientList])
    } catch (Exception ex) {
        echo "Combined email send failed: ${ex.message}"
        echo 'Falling back to one-by-one recipient delivery.'
        recipients.each { recipient ->
            try {
                echo "Sending fallback email to: ${recipient}"
                emailext(baseArgs + [to: recipient])
            } catch (Exception innerEx) {
                echo "Failed to send email to ${recipient}: ${innerEx.message}"
            }
        }
    }
}
