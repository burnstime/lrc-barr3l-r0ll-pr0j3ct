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
