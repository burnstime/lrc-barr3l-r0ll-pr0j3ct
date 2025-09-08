#!/usr/bin/env bash
# Simple pre-commit hook template to run a light secret scan and tests locally
# Install locally as .git/hooks/pre-commit and make executable: chmod +x .git/hooks/pre-commit

echo "Running local pre-commit checks..."
# Quick high-entropy regex scan for base64-like strings
if git grep -I --line-number -n "[A-Za-z0-9+/]\{40,\}" -- ':!tools/*' ':!.git/*' > /dev/null; then
  echo "ERROR: Potential high-entropy strings found in repository. Please review before committing.";
  git grep -I --line-number -n "[A-Za-z0-9+/]\{40,\}" -- ':!tools/*' ':!.git/*'
  exit 1
fi

# Run pytest quick checks (adjust as necessary)
pytest -q tests/test_leftrightbarrelroll.py::test_smoke || { echo 'Tests failed'; exit 1; }

echo "Pre-commit checks passed."
