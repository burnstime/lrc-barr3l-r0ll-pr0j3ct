# Install GitHub CLI in this environment (Windows)
# Tries winget first, otherwise downloads the latest portable ZIP and extracts to .\tools\gh

param()

function Write-Ok($m){ Write-Host "[OK] $m" -ForegroundColor Green }
function Write-Warn($m){ Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Write-Err($m){ Write-Host "[ERR] $m" -ForegroundColor Red }

# Try winget
try{
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "Attempting to install gh via winget..."
        & winget install --id GitHub.cli -e --source winget
        if (Get-Command gh -ErrorAction SilentlyContinue) {
            Write-Ok "gh installed via winget"
            gh --version
            exit 0
        }
        Write-Warn "winget ran but gh not found afterwards"
    } else {
        Write-Warn "winget not available"
    }
} catch {
    Write-Warn "winget install failed: $_"
}

# Fallback: download latest release ZIP
try{
    $api = 'https://api.github.com/repos/cli/cli/releases/latest'
    Write-Host "Fetching latest gh release metadata..."
    $rel = Invoke-RestMethod -Uri $api -Headers @{ 'User-Agent' = 'PowerShell' }
    # Prefer .zip assets for portable installation; fall back to other windows amd64 assets
    $asset = $rel.assets | Where-Object { $_.name -match '(windows.*amd64.*\.zip$)|(gh_.*windows_amd64.zip$)' } | Select-Object -First 1
    if (-not $asset) { $asset = $rel.assets | Where-Object { $_.name -match 'windows.*amd64' } | Select-Object -First 1 }
    if (-not $asset) { Write-Err 'No windows_amd64 asset found in release'; exit 2 }
    $url = $asset.browser_download_url
    Write-Host "Downloading $($asset.name) ..."
    $dest = Join-Path $env:TEMP 'gh_download.zip'
    Invoke-WebRequest -Uri $url -OutFile $dest
    $extractDir = Join-Path (Get-Location) '.tools\gh'
    if (-not (Test-Path $extractDir)) { New-Item -ItemType Directory -Path $extractDir | Out-Null }
    Write-Host "Extracting to $extractDir ..."
    Expand-Archive -Path $dest -DestinationPath $extractDir -Force
    $ghex = Get-ChildItem -Path $extractDir -Recurse -Filter 'gh.exe' | Select-Object -First 1
    if (-not $ghex) { Write-Err 'gh.exe not found after extraction'; exit 3 }
    $bin = $ghex.DirectoryName
    $absBin = (Resolve-Path $bin).Path
    # Add to PATH for this session
    $env:PATH = "$absBin;" + $env:PATH
    Write-Ok "gh installed to $absBin and added to PATH for this session"
    gh --version
    exit 0
} catch {
    Write-Err "Failed to install gh: $_"
    exit 4
}
