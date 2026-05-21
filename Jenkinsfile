// Dakota GPT performance — smoke automation + Allure report + email summary.
//
// Jenkins setup:
//   1. Checkout uses the public repo URL (no GitHub credentials required for clone)
//   2. Update PYTHON_EXE, ALLURE_CMD, NODE_PATH, NPM_PATH for your Windows agent (or use agent tool env vars)
//   3. Install Email Extension plugin for emailext
//   4. Do NOT embed GitHub PATs in this file (rotate any token that was ever committed in plain text)

pipeline {
    agent any

    environment {
        PYTHON_EXE = 'C:\\Users\\wishma.khurram\\AppData\\Local\\Programs\\Python\\Python312\\python.exe'
        ALLURE_CMD = 'C:\\Users\\wishma.khurram\\AppData\\Roaming\\npm\\allure.cmd'
        NODE_PATH  = 'C:\\Program Files\\nodejs'
        NPM_PATH   = 'C:\\Users\\wishma.khurram\\AppData\\Roaming\\npm'
        // Optional: set in Jenkins job or .env on the agent (recommended for secrets)
        // DAKOTA_BASE_URL, DAKOTA_USERNAME, DAKOTA_PASSWORD
    }

    stages {

        stage('Checkout') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    userRemoteConfigs: [[
                        url: 'https://github.com/TestWithMani/dakota_gpt_performance.git'
                    ]]
                ])
            }
        }

        stage('Setup Python') {
            steps {
                bat """
                    @echo off
                    cd /d "%WORKSPACE%"

                    "${PYTHON_EXE}" -m venv venv
                    call venv\\Scripts\\activate.bat

                    python -m pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install pytest allure-pytest
                """
            }
        }

        stage('Run Smoke Only') {
            options {
                timeout(time: 120, unit: 'MINUTES')
            }

            steps {
                withEnv([
                    "PATH=${NODE_PATH};${NPM_PATH};${PATH}"
                ]) {
                    bat """
                        @echo off
                        cd /d "%WORKSPACE%"
                        call venv\\Scripts\\activate.bat

                        if exist allure-results rmdir /s /q allure-results
                        if exist allure-report  rmdir /s /q allure-report

                        echo Running SMOKE ONLY...
                        python -u chatbot_tester.py --smoke
                        echo Exit code: %ERRORLEVEL%
                        if errorlevel 1 exit /b %ERRORLEVEL%

                        echo Smoke run completed.
                    """
                }
            }
        }

        stage('Generate Allure Report') {
            steps {
                withEnv([
                    "PATH=${NODE_PATH};${NPM_PATH};${PATH}"
                ]) {
                    bat """
                        @echo off
                        cd /d "%WORKSPACE%"

                        echo === Verifying Node.js ===
                        node --version
                        if errorlevel 1 (
                            echo ERROR: node not found even after PATH update!
                            exit /b 1
                        )

                        echo === Checking allure-results ===
                        if not exist allure-results (
                            echo ERROR: allure-results folder missing.
                            exit /b 1
                        )

                        echo === Generating Allure Report ===
                        "%ALLURE_CMD%" generate allure-results --clean -o allure-report

                        echo === Report generated. Contents: ===
                        dir allure-report
                    """
                }
            }
        }

        stage('Archive Allure Report') {
            steps {
                archiveArtifacts artifacts: 'allure-report/**',
                    fingerprint: true,
                    allowEmptyArchive: true
            }
        }

        stage('Parse Results and Send Email') {
            steps {
                script {

                    def pyScript = """
import os, json
results_dir = r'${env.WORKSPACE}\\allure-results'
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
                    def pyFile = "${env.WORKSPACE}\\parse_results.py"
                    writeFile file: pyFile, text: pyScript

                    def result = bat(
                        script: "@\"${env.PYTHON_EXE}\" \"${pyFile}\"",
                        returnStdout: true
                    ).trim()

                    def lastLine = result.readLines().last().trim()

                    def total       = 0
                    def passed      = 0
                    def failed      = 0
                    def skipped     = 0
                    def failedNames = ""

                    def p1 = lastLine.indexOf(',')
                    def p2 = lastLine.indexOf(',', p1 + 1)
                    def p3 = lastLine.indexOf(',', p2 + 1)
                    def p4 = lastLine.indexOf(',', p3 + 1)

                    if (p4 > 0) {
                        total       = lastLine.substring(0, p1).toInteger()
                        passed      = lastLine.substring(p1 + 1, p2).toInteger()
                        failed      = lastLine.substring(p2 + 1, p3).toInteger()
                        skipped     = lastLine.substring(p3 + 1, p4).toInteger()
                        failedNames = lastLine.substring(p4 + 1).replace('|', ', ')
                    } else if (p3 > 0) {
                        total   = lastLine.substring(0, p1).toInteger()
                        passed  = lastLine.substring(p1 + 1, p2).toInteger()
                        failed  = lastLine.substring(p2 + 1, p3).toInteger()
                        skipped = lastLine.substring(p3 + 1).toInteger()
                    }

                    echo "DEBUG: total=${total} passed=${passed} failed=${failed} skipped=${skipped} failedNames=${failedNames}"

                    def passedPct  = total > 0 ? (int)((passed * 100) / total) : 0
                    def failedList = failed > 0 ? (failed.toString() + " test(s) failed: " + failedNames) : "No failed tests or tab timeouts were detected in this run."
                    def allureUrl  = env.BUILD_URL + "artifact/allure-report/index.html"
                    def duration   = currentBuild.durationString
                    def dateStr    = new Date().format('yyyy-MM-dd')

                    def emailBody = """<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Dakota Performance Report</title>
</head>
<body style="margin:0;padding:0;background:linear-gradient(140deg,#e0ecff 0%,#efe7ff 45%,#fff6e5 100%);font-family:'Segoe UI',Roboto,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding:24px;">
        <table width="760" cellpadding="0" cellspacing="0"
          style="background:#ffffff;border-radius:16px;overflow:hidden;border:1px solid #dbe3ee;box-shadow:0 14px 32px rgba(30,64,175,0.14);">
          <tr>
            <td style="padding:26px 30px;background:linear-gradient(135deg,#0f172a 0%,#1e40af 52%,#7c3aed 100%);color:#ffffff;">
              <h2 style="margin:0;font-size:26px;letter-spacing:0.2px;">
                Dakota GPT JOE BOT Performance
              </h2>
            </td>
          </tr>
          <tr>
            <td style="padding:24px 30px 10px;">
              <h3 style="margin:0 0 12px;color:#0f172a;font-size:17px;">Build Details</h3>
              <table width="100%" cellpadding="8" cellspacing="8" style="font-size:13px;margin-bottom:12px;">
                <tr align="center">
                  <td style="background:linear-gradient(180deg,#ccfbf1 0%,#99f6e4 100%);color:#134e4a;border-radius:12px;box-shadow:0 6px 14px rgba(20,184,166,0.22);">
                    <div style="font-size:11px;letter-spacing:0.4px;">TOTAL</div>
                    <div style="font-size:24px;font-weight:800;">""" + total + """</div>
                  </td>
                  <td style="background:linear-gradient(180deg,#dcfce7 0%,#86efac 100%);color:#14532d;border-radius:12px;box-shadow:0 6px 14px rgba(34,197,94,0.25);">
                    <div style="font-size:11px;letter-spacing:0.4px;">PASSED</div>
                    <div style="font-size:24px;font-weight:800;">""" + passed + """</div>
                  </td>
                  <td style="background:linear-gradient(180deg,#fee2e2 0%,#fca5a5 100%);color:#7f1d1d;border-radius:12px;box-shadow:0 6px 14px rgba(239,68,68,0.22);">
                    <div style="font-size:11px;letter-spacing:0.4px;">FAILED</div>
                    <div style="font-size:24px;font-weight:800;">""" + failed + """</div>
                  </td>
                  <td style="background:linear-gradient(180deg,#ede9fe 0%,#c4b5fd 100%);color:#4c1d95;border-radius:12px;box-shadow:0 6px 14px rgba(124,58,237,0.22);">
                    <div style="font-size:11px;letter-spacing:0.4px;">SKIPPED</div>
                    <div style="font-size:24px;font-weight:800;">""" + skipped + """</div>
                  </td>
                </tr>
              </table>
              <table width="100%" cellpadding="0" cellspacing="0"
                style="font-size:14px;color:#1e293b;border:1px solid #bfdbfe;border-radius:12px;overflow:hidden;background:linear-gradient(180deg,#f8fbff 0%,#ffffff 100%);table-layout:fixed;">
                <tr>
                  <td width="32%" style="padding:10px 12px;background:linear-gradient(180deg,#dbeafe 0%,#bfdbfe 100%);border-bottom:1px solid #bfdbfe;">
                    <strong>Duration</strong>
                  </td>
                  <td style="padding:10px 12px;border-bottom:1px solid #dbe3f3;font-weight:600;color:#1e3a8a;">""" + duration + """</td>
                </tr>
                <tr>
                  <td style="padding:10px 12px;background:linear-gradient(180deg,#dbeafe 0%,#bfdbfe 100%);border-bottom:1px solid #bfdbfe;">
                    <strong>Passed Percentage</strong>
                  </td>
                  <td style="padding:10px 12px;border-bottom:1px solid #dbe3f3;font-weight:600;color:#15803d;">""" + passedPct + """%</td>
                </tr>
                <tr>
                  <td style="padding:10px 12px;background:linear-gradient(180deg,#dbeafe 0%,#bfdbfe 100%);">
                    <strong>Failed Tests / Affected Tabs</strong>
                  </td>
                  <td style="padding:10px 12px;font-weight:600;color:#15803d;">""" + failedList + """</td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 30px 24px;">
              <h3 style="margin:0 0 12px;color:#0f172a;font-size:17px;">Report Access</h3>
              <table width="100%" cellpadding="0" cellspacing="0"
                style="font-size:14px;color:#1e293b;border:1px solid #c4b5fd;border-radius:10px;overflow:hidden;background:linear-gradient(180deg,#faf5ff 0%,#f3f0ff 100%);">
                <tr>
                  <td width="32%" style="padding:10px 12px;background:linear-gradient(180deg,#ede9fe 0%,#ddd6fe 100%);">
                    <strong>Allure Report</strong>
                  </td>
                  <td style="padding:10px 12px;">
                    <a style="color:#6d28d9;text-decoration:underline;font-weight:700;" href=\"""" + allureUrl + """\">Open Allure Report</a>
                  </td>
                </tr>
              </table>
              <p style="margin:12px 0 0;color:#64748b;font-size:12px;">
                Please see the attached Excel performance sheet for detailed run metrics.
              </p>
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
</html>"""

                    emailext(
                        to: 'wishma.khurram@rolustech.com',
                        subject: "Dakota GPT Performance | " + dateStr,
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
            echo "Pipeline finished."
        }
        failure {
            echo "Pipeline failed — check console log and archived Allure report."
        }
    }
}
