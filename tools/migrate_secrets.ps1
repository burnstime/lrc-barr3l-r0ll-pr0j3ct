<#
Safe helper to migrate local secret files into Docker secrets and print GitHub Actions secret commands.
This script will NOT upload secrets to remote systems automatically (except via `gh` if you explicitly run the provided commands).

Usage (safe preview):
  pwsh> .\tools\migrate_secrets.ps1 -ShowOnly

To print commands to create Docker secrets and GH secrets (you must run them):
  pwsh> .\tools\migrate_secrets.ps1 -SecretFiles './secrets/SECRET_KEY','./secrets/ADMIN_TOKEN'

To actually create Docker secrets (requires Docker in swarm mode and appropriate privileges):
  pwsh> .\tools\migrate_secrets.ps1 -SecretFiles './secrets/SECRET_KEY','./secrets/ADMIN_TOKEN' -CreateDockerSecrets

Notes:
- This script is a helper; review outputs before running any printed commands.
- For GitHub, install GitHub CLI (`gh`) and run the printed `gh secret set` commands manually or paste them.
#>
param(
    [string[]]$SecretFiles = @('.\secrets\SECRET_KEY', '.\secrets\ADMIN_TOKEN'),
    [switch]$CreateDockerSecrets,
    [switch]$ShowOnly
)

function Write-Ok($m){ Write-Host "[OK] $m" -ForegroundColor Green }
function Write-Warn($m){ Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Write-Err($m){ Write-Host "[ERR] $m" -ForegroundColor Red }

$repo = Get-Location
Write-Host "Repo: $repo"

foreach($path in $SecretFiles){
    if(-not (Test-Path $path)){
        Write-Warn "Secret file not found: $path"
    } else {
        $size = (Get-Item $path).Length
        Write-Ok "Found $path ($size bytes)"
    }
}

Write-Host "\nThese commands will help you migrate secrets. They are not executed unless you pass -CreateDockerSecrets.";

# Docker secret commands (Swarm mode)
foreach($path in $SecretFiles){
    $name = [System.IO.Path]::GetFileName($path)
    $cmd = "docker secret rm $name 2>$null; docker secret create $name $path"
    Write-Host "Docker secret command:`n  $cmd`n"
}

# GitHub CLI commands for Actions secrets (encrypted at rest)
foreach($path in $SecretFiles){
    $name = [System.IO.Path]::GetFileName($path)
    $cmd = "gh secret set $name --body \"$(Get-Content -Raw -Path $path)\""
    Write-Host "GitHub secret command (requires gh cli):`n  $cmd`n"
}

# Optional: show steps to rotate secrets
Write-Host "Rotation guidance:`n 1) Generate new secrets in your secret manager.\n 2) Deploy new secrets to the environment (docker secrets or cloud KMS).\n 3) Restart services using new secrets.\n 4) Revoke old secrets and update any external consumers.\n"

if($CreateDockerSecrets -and -not $ShowOnly){
    Write-Warn "You requested creation of Docker secrets. Ensure Docker Swarm is enabled and you understand this will replace any existing secrets with the same name."
    $ok = Read-Host "Type CREATE to proceed"
    if($ok -ne 'CREATE'){
        Write-Err "Confirmation mismatch. Aborting creation."; exit 3
    }
    foreach($path in $SecretFiles){
        if(Test-Path $path){
            $name = [System.IO.Path]::GetFileName($path)
            docker secret rm $name 2>$null
            docker secret create $name $path
            Write-Ok "Created Docker secret: $name"
        }
    }
}

Write-Ok "Done. Review commands above and run them in your environment as needed."
