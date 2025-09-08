#!/usr/bin/env bash
set -euo pipefail
# tools/git_purge_dryrun.sh
# Performs a safe dry-run for removing files/strings from git history using git-filter-repo

if ! command -v git-filter-repo >/dev/null 2>&1; then
  echo "git-filter-repo not found. Install with: pip install git-filter-repo" >&2
  exit 1
fi

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <path-or-pattern> [output-branch-name]" >&2
  echo "Example: $0 secrets.txt purged-history-dryrun" >&2
  exit 1
fi

TARGET="$1"
OUT_BRANCH="${2:-purged-history-dryrun}"

ROOT=$(git rev-parse --show-toplevel)
TMPDIR=$(mktemp -d)
echo "Creating a mirror clone at $TMPDIR for dry-run"
git clone --mirror "$ROOT" "$TMPDIR/repo.git"
cd "$TMPDIR/repo.git"

echo "Running git-filter-repo in dry-run mode to remove $TARGET"
# Note: git-filter-repo doesn't have a dry-run flag, so we emulate by creating a new repo and inspecting refs.
git-filter-repo --invert-paths --paths "$TARGET" --path-rename :  || true

echo "Review the resulting refs in $TMPDIR/repo.git. If satisfied, repeat the operation on the real repo following the documented plan in tools/git_history_purge_plan.md"
echo "Temporary mirror at: $TMPDIR/repo.git (remove when done)"
