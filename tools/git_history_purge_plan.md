# Git history purge plan (safe, step-by-step)

This document outlines a safe approach to remove secrets from git history after rotating them.

1) Rotate all live secrets in all environments and verify the app works.
2) Create an allowlist (`.secrets-ignore`) for any acceptable artifacts.
3) Install `git-filter-repo` locally:

   pip install git-filter-repo

4) Run an initial analysis to find candidate files/strings (use `tools/secrets_scanner.py`).
5) Create a local clone of the repo and run `git-filter-repo --path-glob 'path/to/file' --invert-paths` in dry-run mode first (or use `--replace-text` with a mapping file). Review diffs.
6) Push to a new branch and open a PR for team review. Do NOT force-push `main` until verified.
7) Once approved, perform the rewrite and coordinate rotations and CI secrets.

Note: This operation is destructive for history. Only proceed after rotating live secrets.
