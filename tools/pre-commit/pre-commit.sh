#!/usr/bin/env bash
# Simple pre-commit hook to run the tiny secrets scanner and black/flake8 optionally
# Install by copying to .git/hooks/pre-commit and making executable.

set -e
ROOT_DIR=$(git rev-parse --show-toplevel)
python3 "$ROOT_DIR/tools/secrets_scanner.py" "$ROOT_DIR"
# add other linters if desired
# python3 -m black --check .
# python3 -m flake8 .
