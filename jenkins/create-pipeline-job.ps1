# Creates or updates Jenkins pipeline job (credentials via environment variables only).
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

$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
try {
    $crumbResp = Invoke-RestMethod -Uri "$base/crumbIssuer/api/json" -Headers $headers -WebSession $session -Method Get
    if ($crumbResp.crumbRequestField -and $crumbResp.crumb) {
        $headers[$crumbResp.crumbRequestField] = $crumbResp.crumb
    }
} catch {
    Write-Warning "Crumb issuer unavailable: $_"
}

$configPath = Join-Path $PSScriptRoot 'pipeline-job.xml'
if (-not (Test-Path $configPath)) {
    Write-Error "Missing $configPath"
    exit 1
}
$configXml = Get-Content -Path $configPath -Raw -Encoding UTF8

$jobExists = $false
try {
    $null = Invoke-WebRequest -Uri "$base/job/$JobName/api/json" -Headers $headers -WebSession $session -Method Get -UseBasicParsing
    $jobExists = $true
} catch {
    $jobExists = $false
}

if ($jobExists) {
    Write-Host "Updating existing job: $JobName"
    $uri = "$base/job/$JobName/config.xml"
} else {
    Write-Host "Creating job: $JobName"
    $uri = "$base/createItem?name=$JobName"
}

$response = Invoke-WebRequest -Uri $uri -Headers $headers -WebSession $session -Method Post -Body $configXml -ContentType 'application/xml; charset=UTF-8' -UseBasicParsing
Write-Host "OK ($($response.StatusCode)) - $base/job/$JobName/"
