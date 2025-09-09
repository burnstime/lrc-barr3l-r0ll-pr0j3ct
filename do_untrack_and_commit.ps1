cd 'C:\Users\12265\OneDrive\Documents'
Write-Host 'Removing tracked virtualenv directories from git (cached only)'
if (Test-Path .venv) { git rm -r --cached .venv || true }
if (Test-Path venv) { git rm -r --cached venv || true }
# Stage gitignore and semgrepignore changes
git add .gitignore .semgrepignore || true
# Run secrets scanner but filter out .venv/ and venv/ occurrences from output to avoid known noise
Write-Host 'Running secrets scanner (filtering .venv and venv paths from output)'
$raw = python tools\secrets_scanner.py 2>&1 | Out-String
$filtered = ($raw -split "\n") | Where-Object { ($_ -notmatch "\\.venv") -and ($_ -notmatch "\\bvenv\\b") }
$filtered | Write-Host
$exit = $LASTEXITCODE
if ($exit -ne 0) {
    Write-Host 'SCANNER_FOUND_OR_FAILED (filtered output shown above)'
    Write-Host 'Aborting commit. Please review scanner output.'
    exit 2
}
# If scanner is clean, commit ignores and removal of cached venv files
$s = git status --porcelain
if ([string]::IsNullOrEmpty($s)) {
    Write-Host 'NO_CHANGES_TO_COMMIT'
    exit 0
}
$msg = 'chore: add ignore patterns and untrack local virtualenvs'
Write-Host "Committing: $msg"
git commit -m "$msg" || { Write-Host 'COMMIT_FAILED'; exit 3 }
Write-Host 'COMMIT_OK'
