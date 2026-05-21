# Creates or updates Jenkins pipeline job "dakota-gpt-performance" (does not store passwords in repo).
# Usage:
#   $env:JENKINS_URL = 'http://110.93.205.18:8080'
#   $env:JENKINS_USER = 'your-user'
#   $env:JENKINS_PASSWORD = 'your-password'
#   .\jenkins\create-pipeline-job.ps1

param(
    [string]$JenkinsUrl = $env:JENKINS_URL,
    [string]$JenkinsUser = $env:JENKINS_USER,
    [string]$JenkinsPassword = $env:JENKINS_PASSWORD,
    [string]$JobName = 'dakota-gpt-performance'
)

if (-not $JenkinsUrl -or -not $JenkinsUser -or -not $JenkinsPassword) {
    Write-Error 'Set JENKINS_URL, JENKINS_USER, and JENKINS_PASSWORD environment variables.'
    exit 1
}

$base = $JenkinsUrl.TrimEnd('/')
$pair = "${JenkinsUser}:${JenkinsPassword}"
$bytes = [System.Text.Encoding]::ASCII.GetBytes($pair)
$basic = [Convert]::ToBase64String($bytes)
$headers = @{ Authorization = "Basic $basic" }

try {
    $crumbResp = Invoke-RestMethod -Uri "$base/crumbIssuer/api/json" -Headers $headers -Method Get
    $headers['Jenkins-Crumb'] = $crumbResp.crumb
    if ($crumbResp.crumbRequestField) {
        $headers[$crumbResp.crumbRequestField] = $crumbResp.crumb
    }
} catch {
    Write-Warning "Crumb issuer unavailable (CSRF may be disabled): $_"
}

$configPath = Join-Path $PSScriptRoot 'pipeline-job.xml'
if (-not (Test-Path $configPath)) {
    Write-Error "Missing $configPath"
    exit 1
}
$configXml = Get-Content -Path $configPath -Raw -Encoding UTF8

$check = Invoke-WebRequest -Uri "$base/job/$JobName/api/json" -Headers $headers -Method Get -UseBasicParsing -ErrorAction SilentlyContinue
if ($check.StatusCode -eq 200) {
    Write-Host "Updating existing job: $JobName"
    $uri = "$base/job/$JobName/config.xml"
    $method = 'Post'
} else {
    Write-Host "Creating job: $JobName"
    $uri = "$base/createItem?name=$JobName"
    $method = 'Post'
}

$response = Invoke-WebRequest -Uri $uri -Headers $headers -Method $method -Body $configXml -ContentType 'application/xml; charset=UTF-8' -UseBasicParsing
Write-Host "OK ($($response.StatusCode)) — $base/job/$JobName/"
