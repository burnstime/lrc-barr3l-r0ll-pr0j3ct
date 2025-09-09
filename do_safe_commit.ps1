Set-Location "C:\Users\12265\OneDrive\Documents"
Write-Host "Running local secrets scanner: tools/secrets_scanner.py"
$scannerOutput = & python "tools\secrets_scanner.py" 2>&1
$scannerExit = $LASTEXITCODE
Write-Host "--- scanner output start ---"
Write-Host $scannerOutput
Write-Host "--- scanner output end ---"
if ($scannerExit -ne 0) {
    Write-Host "SECRETS_SCANNER_FAILED_OR_FOUND"
    Write-Host "Aborting commit. Please review scanner output above."
    exit 2
}
# No scanner errors; continue to commit
$status = git status --porcelain
if ([string]::IsNullOrEmpty($status)) {
    Write-Host "NO_CHANGES"
    exit 0
}
$branch = git rev-parse --abbrev-ref HEAD
$ts = (Get-Date).ToString("o")
$msg = "work: save all changes on $branch at $ts"
Write-Host "Committing with message: $msg"
# Stage and commit
git add -A
git commit -m $msg
if ($LASTEXITCODE -eq 0) {
    $h = git rev-parse --short HEAD
    Write-Host "COMMITTED $h on $branch"
    git --no-pager show --name-status -1
    exit 0
} else {
    Write-Host "COMMIT_FAILED"
    exit 3
}
