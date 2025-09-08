<#
Safe history purge helper for Windows PowerShell.
This script prepares commands to purge specified paths from a repo mirror using git-filter-repo.
It will NOT perform destructive operations unless you pass the -ConfirmPurge switch and set $RunConfirmed = $true interactively.

Usage (non-destructive):
  pwsh> .\tools\purge_history.ps1 -RepoUrl 'https://github.com/burnstime/lrc-barr3l-r0ll-pr0j3ct.git' -PathsToRemove 'uploads/secret.txt','sensitive/file'

To actually run the purge (destructive):
  pwsh> .\tools\purge_history.ps1 -RepoUrl 'https://github.com/burnstime/lrc-barr3l-r0ll-pr0j3ct.git' -PathsToRemove 'uploads/secret.txt' -ConfirmPurge

Important: This script expects git-filter-repo to be installed and on PATH. It will bail safely if not found.
#>
param(
    [Parameter(Mandatory=$true)]
    [string]$RepoUrl,

    [Parameter(Mandatory=$true)]
    [string[]]$PathsToRemove,

    [switch]$ConfirmPurge
)

function Write-Ok($m){ Write-Host "[OK] $m" -ForegroundColor Green }
function Write-Warn($m){ Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Write-Err($m){ Write-Host "[ERR] $m" -ForegroundColor Red }

$mirror = "repo-mirror.git"
$runConfirmed = $false

# Check prerequisites
try{
    git --version | Out-Null
}catch{
    Write-Err "git not found in PATH. Install Git for Windows and retry."; exit 2
}

if(-not (Get-Command git-filter-repo -ErrorAction SilentlyContinue)){
    Write-Warn "git-filter-repo not found in PATH. The script will print the exact commands to run if you choose to continue."
}

Write-Host "Preparing mirror clone of: $RepoUrl"
Write-Host "Mirror dir: $mirror"
Write-Host "Paths to remove: $($PathsToRemove -join ', ')"
Write-Host "Confirm destructive purge with -ConfirmPurge"

if($ConfirmPurge){
    Write-Warn "You passed -ConfirmPurge. This will perform destructive operations after an explicit interactive confirmation."
    $ok = Read-Host "Type PURGE to proceed"
    if($ok -eq 'PURGE'){
        $runConfirmed = $true
    }else{
        Write-Err "Confirmation mismatch. Aborting."; exit 3
    }
}

# Non-destructive steps: print commands and create a zip backup of the mirrored repo if it exists
if(Test-Path $mirror){
    Write-Warn "$mirror already exists. Will not overwrite. Creating zip backup 'repo-mirror-backup.zip'"
    if(Test-Path "$mirror"){
        Compress-Archive -LiteralPath $mirror -DestinationPath "repo-mirror-backup.zip" -Force
        Write-Ok "Backup created: repo-mirror-backup.zip"
    }
}

$cloneCmd = "git clone --mirror $RepoUrl $mirror"
Write-Host "Clone command (safe to run):`n  $cloneCmd"

$filterCmd = "cd $mirror; git-filter-repo --invert-paths --paths $($PathsToRemove -join ' ')"
Write-Host "Filter command (run inside mirror dir if git-filter-repo installed):`n  $filterCmd"

$verifyCmd = "cd $mirror; git log --all -- $($PathsToRemove -join ' ') || echo 'no results'"
Write-Host "Verify command:`n  $verifyCmd"

$pushCmd = "cd $mirror; git push --force"
Write-Host "Force-push command (destructive):`n  $pushCmd"

if(-not $runConfirmed){
    Write-Host "Purge not executed. To execute, re-run with -ConfirmPurge and follow prompts."
    exit 0
}

# If we reach here, user confirmed.
if(-not (Get-Command git-filter-repo -ErrorAction SilentlyContinue)){
    Write-Err "git-filter-repo not found. Install it before running the destructive steps."; exit 4
}

# Execute destructive steps
Write-Host "Executing destructive purge steps..."
Push-Location
try{
    & git clone --mirror $RepoUrl $mirror
    Set-Location $mirror
    & git-filter-repo --invert-paths --paths $PathsToRemove
    Write-Ok "Filter-repo completed. Verifying..."
    & git log --all -- $PathsToRemove
    Write-Ok "Pushing cleaned mirror to origin (force)"
    & git push --force
    Write-Ok "Force-push complete. Inform collaborators to re-clone."
}catch{
    Write-Err "Error during purge: $_"; exit 5
}finally{
    Pop-Location
}

Write-Ok "Purge completed"
