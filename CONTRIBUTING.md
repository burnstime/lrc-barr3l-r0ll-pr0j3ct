# Contributing

Thank you for contributing. Please open PRs against `main`. Keep secrets out of the repository. Use Docker secrets or environment variables for sensitive values.

## Local development

- Use `python -m venv .venv` and `pip install -r lab_server/requirements.txt` to get started.

## Pre-commit hook (optional)

We provide a simple pre-commit hook template at `tools/pre-commit-hook-template.sh` that performs a quick high-entropy scan and a smoke test. To enable it locally:

```pwsh
cp tools/pre-commit-hook-template.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

Customize the script as needed for your workflow.

---

Contributing — secrets allowlist workflow

This repository includes a developer-friendly secrets scanner and an automated allowlist flow to safely manage false positives.

Quick overview
- A lightweight secrets scanner runs on every PR and uploads findings as an artifact.
- The scanner posts a short top-5 summary as a PR comment (no long dumps).
- If findings are legitimate secrets, rotate them immediately and update the PR accordingly.

Handling false positives (allowlist flow)
1. If the scanner reports legitimate false positives, create a PR that adds a file named `secrets-allowlist.txt` at the repository root.
	- The file should contain one path or glob per line (examples: `tools/reports`, `tests/data/test_keys.txt`).
	- Include justification in the PR description explaining why entries are safe to ignore.
2. Request a review from a repo maintainer.
3. When a maintainer approves the PR, the `Apply secrets allowlist` workflow will run. It:
	- Installs the GitHub CLI in the runner,
	- Creates a branch that merges the new allowlist entries into `.secrets-ignore`,
	- Pushes the branch and opens a follow-up PR to merge the updated `.secrets-ignore` into the default branch.
4. After the follow-up PR is merged, the scanner will ignore the listed paths.

Notes and security
- This system is opt-in for allowlist changes: only approved PRs lead to automatic allowlist application.
- The CI scanner is warn-only by default. To make CI fail on findings, set the repository secret `SCANNER_FAIL_ON_FINDINGS=1`.
- The allowlist workflow uses the `gh` CLI in the runner; the workflow installs it automatically, and uses the built-in `GITHUB_TOKEN` for auth.

Local developer setup
- To run the scanner locally before committing, install the pre-commit hook with:

  tools/pre-commit/install-hook.sh

- Or use the `pre-commit` framework if installed (`pip install pre-commit && pre-commit install`).

Files of interest
- `tools/secrets_scanner.py` — local scanner used by CI and pre-commit hook.
- `.secrets-ignore` — repo-level ignore list used by the scanner.
- `.github/workflows/apply-secrets-allowlist.yml` — workflow that applies approved allowlist entries.

If you have questions about the process or need a maintainer to review an allowlist PR, ping the maintainers in the PR description.
