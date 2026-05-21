Set-Location $PSScriptRoot

if (-not (Test-Path "allure-results")) {
    Write-Error "allure-results folder not found. Run chatbot_tester.py first."
    exit 1
}

if (-not (Test-Path "allure-report\index.html")) {
    Write-Host "Generating allure-report from allure-results..."
    allure generate allure-results -o allure-report --clean
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Allure generate failed."
        exit 1
    }
}

if (-not (Test-Path "allure-report\index.html")) {
    Write-Error "allure-report\index.html was not created."
    exit 1
}

$port = 8765
while ($true) {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $port)
    try {
        $listener.Start()
        $listener.Stop()
        break
    } catch {
        $port++
        if ($port -gt 8795) {
            Write-Error "Could not find a free local port for the report server."
            exit 1
        }
    } finally {
        if ($listener) {
            try { $listener.Stop() } catch {}
        }
    }
}

$url = "http://127.0.0.1:$port/index.html"
Write-Host "Serving Allure report from allure-report"
Write-Host "Open: $url"
Write-Host "Keep this window open while viewing the report."
Start-Process $url
python -m http.server $port --bind 127.0.0.1 --directory allure-report
