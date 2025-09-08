Red Team Report — LRC Barr3l R0ll Project

Date: 2025-09-08
Author: automated red-team assistant
Branch: restrict-decode-endpoint

Scope
- Repository: lrc-barr3l-r0ll-pr0j3ct
- Focus: lab_server Flask app, Docker Compose stack (lab, redis, nginx), tests and CI, redteam tooling in `tools/`.

Summary of findings
- Sensitive/test files discovered:
  - `uploads/secret.txt` — contained placeholder text "test"; removed from index in this branch but remains in earlier commits/history.
  - `s1.txt`, `s2.txt` — contain Base64-like values that decode to JSON (potential test tokens); review and rotate if real secrets.
  - `secrets/SECRET_KEY` and `secrets/ADMIN_TOKEN` exist locally and are referenced by `docker-compose.yml` as Docker secrets; they are ignored by `.gitignore` and not committed (good).
- Runtime protections and fixes applied in this branch:
  - CSRF helpers added and unit tests pass (11 passed, 1 skipped).
  - `lab_server/app.py`: decoder endpoint `/decode-login` implemented and then restricted; tests allowed decoder in testing mode.
  - Added lightweight Redis/in-memory rate-limiter for `/decode-login` and admin/staff login endpoints.
  - Fixed `nginx.conf` proxy to point at `lab` service.
  - Added CI workflow (`.github/workflows/ci.yml`) to run tests on push/PR.
  - Added `REDTEAM_PLAYBOOK.md` and `tools/run_redteam_checks.ps1` to automate non-destructive checks.

Risk ratings (high-level)
- Secret in history (uploads/secret.txt): Low-to-Medium (placeholder now, but presence in history increases risk if real secrets are present).
- Exposed decoder endpoint if enabled in production: High — allows brute-force credential discovery; must remain disabled in production and gated by ADMIN_TOKEN + network ACL.
- Admin token management: Medium — ensure ADMIN_TOKEN stored in secret manager and rotated if leaked.
- Uploads: Low — `secure_filename`, extension allowlist, and MAX_CONTENT_LENGTH enforced, but traversal checks should remain monitored.

Remediation steps
1) Secrets and history
   - If any committed file contains real secrets, rotate those credentials immediately (API keys, tokens, passwords).
   - To purge sensitive files from repo history, follow the safe procedure and use the provided `tools/purge_history.ps1` script (this script will not run destructive steps without exact confirmation).
   - Keep the backup mirror generated before purge in a secure location until all collaborators confirm migration, then securely delete it.

2) Runtime protections
   - Set `DECODE_ENABLED=0` in production environment and do not enable it in compose files used for production.
   - Keep `SESSION_COOKIE_SECURE=1` in production (ensure TLS is terminated at nginx/ALB and app sees secure connections).
   - Move admin tokens and secrets to a secret manager (Docker secrets, HashiCorp Vault, cloud KMS or GitHub secrets for CI) and avoid storing them on disk or in source tree.
   - Enable Redis-backed rate-limiting in production (set `USE_REDIS_RATE_LIMIT=1` and configure a robust limit per IP and per account).

3) Monitoring and CI
   - Add secrets scanning to CI (truffleHog/git-secrets) as a gate on PRs.
   - Add alerts for repeated rate-limit events (`_send_alert` already exists; wire to webhook/ops channel).
   - Add smoke tests in CI that exercise login, CSRF, and upload flows.

Verification checklist
- [ ] All tests pass locally and in CI (pytest green on PR).
- [ ] `git log --all -- uploads/secret.txt` returns no results after purge (if purge performed).
- [ ] No tracked files contain high-entropy secrets (run truffleHog/git-secrets on repo mirror).
- [ ] `DECODE_ENABLED` is not set in any production deployment; `SESSION_COOKIE_SECURE` set to true behind TLS.
- [ ] Admin tokens rotated after purge (if applicable).
- [ ] Collaborators re-cloned after history rewrite, if any.

Artifacts created in branch
- `REDTEAM_PLAYBOOK.md` — playbook with commands and safe steps.
- `tools/run_redteam_checks.ps1` — non-destructive automation for local checks.
- `tools/purge_history.ps1` — safety-checked purge script (see below) — does NOT run destructive steps by default.

If you want, I can:
- Execute the full history purge and force-push cleaned history (requires confirmation and coordination).
- Produce a PDF of this report and the PoC artifacts.


