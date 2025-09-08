<#
tools/run_redteam_checks.ps1

Automates safe, local red-team validation steps for the lab.
It:
- Brings up docker-compose (detached)
- Waits for the lab service to be ready
- Runs the provided probe scripts (non-destructive)
- Collects logs into tools/reports
- Shuts the compose stack down if requested

Run: pwsh -ExecutionPolicy Bypass -File .\tools\run_redteam_checks.ps1
#>

Param(
    [switch]$DownAfter = $false
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
Set-Location $root

$reportsDir = Join-Path $root 'tools\reports'
if (-not (Test-Path $reportsDir)) { New-Item -ItemType Directory -Path $reportsDir | Out-Null }

Write-Output "Starting docker-compose stack..."
docker compose up -d

# Wait for service
Write-Output "Waiting for lab to accept connections on http://127.0.0.1:8000 ..."
$max = 30
$count = 0
while ($count -lt $max) {
    try {
        $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/' -UseBasicParsing -Method GET -TimeoutSec 3
        if ($r.StatusCode -eq 200) { Write-Output 'Lab ready.'; break }
    } catch { Start-Sleep -Seconds 2 }
    $count++
}

# Run pytest quick smoke
Write-Output 'Running pytest (quick)...'
pytest -q | Tee-Object -FilePath (Join-Path $reportsDir 'pytest.txt')

# Run redteam_probe.py if present
if (Test-Path '.\tools\redteam_probe.py') {
    Write-Output 'Running tools/redteam_probe.py (Flask test client probes)...'
    python .\tools\redteam_probe.py | Tee-Object -FilePath (Join-Path $reportsDir 'redteam_probe.txt')
} else { Write-Output 'tools/redteam_probe.py not found' }

# Run rt_checks.py which exercises HTTP endpoints
if (Test-Path '.\tools\rt_checks.py') {
    Write-Output 'Running tools/rt_checks.py (HTTP session-based checks)...'
    python .\tools\rt_checks.py | Tee-Object -FilePath (Join-Path $reportsDir 'rt_checks.txt')
} else { Write-Output 'tools/rt_checks.py not found' }

# Collect docker logs
Write-Output 'Collecting docker logs for lab...'
docker compose logs --tail 200 lab | Out-File (Join-Path $reportsDir 'lab_logs.txt') -Encoding utf8

if ($DownAfter) {
    Write-Output 'Stopping docker-compose stack...'
    docker compose down
}

Write-Output "Reports saved to $reportsDir"
