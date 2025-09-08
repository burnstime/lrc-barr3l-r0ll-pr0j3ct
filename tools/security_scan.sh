#!/usr/bin/env bash
set -euo pipefail
# tools/security_scan.sh
# Run a suite of security scans: pip-audit, bandit, semgrep, and trivy (if Dockerfile present)


ROOT=$(git rev-parse --show-toplevel)
cd "$ROOT"

OUT_DIR="artifacts/security"
mkdir -p "$OUT_DIR"

FAIL_ON_FINDINGS="${FAIL_ON_FINDINGS:-0}"
DRY_RUN=0
JSON_OUT="${JSON_OUT:-$OUT_DIR/summary.json}"

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }

usage(){
  cat <<EOF
Usage: $0 [--dry-run] [--json-out path]
  --dry-run   Run scans but do not build images or write heavy artifacts
  --json-out  Write machine-readable summary JSON to given path (default: $JSON_OUT)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --json-out) JSON_OUT="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) shift ;;
  esac
done

log "Starting security scans (dry_run=$DRY_RUN)"

# ensure pip packages
python -m pip install --upgrade pip >/dev/null
python -m pip install pip-audit bandit semgrep --quiet
# optionally install syft for SBOM generation
python -m pip install syft --quiet || true

log "Running pip-audit"
python -m pip_audit --format=json > "$OUT_DIR/pip_audit.json" || true

log "Running bandit"
bandit -r . -f json -o "$OUT_DIR/bandit.json" || true

log "Running semgrep"
semgrep --config .semgrep.yml --json > "$OUT_DIR/semgrep.json" || true

# Optional trivy image scan if Dockerfile exists and not dry-run
if [[ -f Dockerfile ]]; then
  if [[ "$DRY_RUN" -eq 0 ]]; then
    log "Dockerfile found; building image for trivy scan"
    IMAGE_NAME="security-scan-temp:latest"
    docker build -t "$IMAGE_NAME" . >/dev/null
    log "Running trivy image scan"
    docker run --rm -v "$OUT_DIR":/tmp/out aquasec/trivy:latest image --format json -o /tmp/out/trivy_image.json "$IMAGE_NAME" || true
  else
    log "Dry-run: skipping image build and trivy scan"
  fi
else
  log "No Dockerfile found; skipping image scan"
fi

# Generate SBOM with syft if available
if command -v syft >/dev/null 2>&1; then
  log "Generating SBOM with syft"
  syft packages dir:. -o json > "$OUT_DIR/sbom.json" || true
else
  log "syft not installed in PATH; attempting python syft"
  python -c "import syft" >/dev/null 2>&1 && python -m syft packages dir:. -o json > "$OUT_DIR/sbom.json" || log "syft unavailable; skipping SBOM"
fi

# Summarize findings (simple heuristic) into both text and JSON
python - <<PY > "$OUT_DIR/summary.txt"
import json,sys
out={}
try:
  pa=json.load(open('artifacts/security/pip_audit.json'))
  out['pip_audit_vulns']=len(pa.get('vulns',[])) if isinstance(pa,dict) else 0
except Exception:
  out['pip_audit_vulns']='?'
try:
  b=json.load(open('artifacts/security/bandit.json'))
  out['bandit_issues']=len(b.get('results',[]))
except Exception:
  out['bandit_issues']='?'
try:
  s=json.load(open('artifacts/security/semgrep.json'))
  out['semgrep_findings']=len(s.get('results',[]))
except Exception:
  out['semgrep_findings']='?'
print(json.dumps(out))
PY

python - <<PY > "$JSON_OUT"
import json
print(open('artifacts/security/summary.txt').read())
PY

log "Scans finished. Artifacts: $OUT_DIR"

if [[ "$FAIL_ON_FINDINGS" == "1" ]]; then
  # Fail if any findings >0 (basic)
  jq -e '.pip_audit_vulns>0 or .bandit_issues>0 or .semgrep_findings>0' "$OUT_DIR/summary.txt" >/dev/null 2>&1 && {
    log "Findings detected and FAIL_ON_FINDINGS=1; exiting with failure"
    exit 2
  } || log "No high-level findings according to summary"
fi

log "security_scan.sh complete"
