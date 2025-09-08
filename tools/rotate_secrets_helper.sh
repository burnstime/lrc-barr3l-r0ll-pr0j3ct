#!/usr/bin/env bash
set -euo pipefail
# tools/rotate_secrets_helper.sh
# Interactive helper to rotate ADMIN_TOKEN and SECRET_KEY in env and Docker secrets.

echo "This script will help you rotate ADMIN_TOKEN and SECRET_KEY. It will NOT change git history."

APPLY_LOCAL=0
if [[ "${1:-}" == "--apply-local" ]]; then
  APPLY_LOCAL=1
fi

read -p "Enter new ADMIN_TOKEN (or leave empty to auto-generate): " ADMIN_TOKEN
if [[ -z "$ADMIN_TOKEN" ]]; then
  ADMIN_TOKEN=$(python - <<PY
import secrets
print(secrets.token_urlsafe(32))
PY
)
  echo "Generated ADMIN_TOKEN: $ADMIN_TOKEN"
fi

read -p "Enter new SECRET_KEY (or leave empty to auto-generate): " SECRET_KEY
if [[ -z "$SECRET_KEY" ]]; then
  SECRET_KEY=$(python - <<PY
import secrets
print(secrets.token_hex(32))
PY
)
  echo "Generated SECRET_KEY: $SECRET_KEY"
fi

echo "Suggested steps to deploy rotated secrets:"
echo "1) Update your secret store (Vault / AWS Secrets Manager / Docker secrets)." 
echo "   For Docker secrets locally: echo -n \"$ADMIN_TOKEN\" > /run/secrets/ADMIN_TOKEN && echo -n \"$SECRET_KEY\" > /run/secrets/SECRET_KEY"
echo "2) Restart services to pick up new secrets."
echo "3) Run integration tests and smoke tests."
echo "4) Once confirmed, optionally run the git history purge dry-run and review before destructive purge."

cat <<EOF > rotate_secrets_preview.txt
ADMIN_TOKEN=$ADMIN_TOKEN
SECRET_KEY=$SECRET_KEY
EOF

echo "Preview written to rotate_secrets_preview.txt. Review before applying to production." 

if [[ "$APPLY_LOCAL" -eq 1 ]]; then
  echo "Applying secrets to local Docker secrets path /run/secrets (requires permission)"
  if [[ ! -d /run/secrets ]]; then
    echo "/run/secrets not present; creating (may require sudo)"
    mkdir -p /run/secrets || true
  fi
  echo -n "$ADMIN_TOKEN" > /run/secrets/ADMIN_TOKEN || sudo sh -c "echo -n '$ADMIN_TOKEN' > /run/secrets/ADMIN_TOKEN"
  echo -n "$SECRET_KEY" > /run/secrets/SECRET_KEY || sudo sh -c "echo -n '$SECRET_KEY' > /run/secrets/SECRET_KEY"
  echo "Applied local Docker secrets"
fi
