#!/usr/bin/env bash
# Installs the simple pre-commit hook
ROOT=$(git rev-parse --show-toplevel)
HOOK_DEST="$ROOT/.git/hooks/pre-commit"
cp "$ROOT/tools/pre-commit/pre-commit.sh" "$HOOK_DEST"
chmod +x "$HOOK_DEST"
echo "Installed local pre-commit hook to $HOOK_DEST"
# Optionally install pre-commit framework
if command -v pre-commit >/dev/null 2>&1; then
  pre-commit install
  echo "pre-commit framework installed and hooks enabled"
else
  echo "pre-commit not installed. To enable automatic hook installation run: pip install pre-commit && pre-commit install"
fi
