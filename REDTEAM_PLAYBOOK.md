Red Team Finish Playbook

Purpose
- A concrete, safe playbook of the steps the red team would perform to finish assessment of this lab repository and prepare findings.
- Includes exact commands you can run locally (PowerShell examples) and an automated helper script to run non-invasive checks.

Important safety notes
- These steps rewrite repository history or exercise services running on your host. Only run destructive steps (history rewrite, force-push) with full backups and coordination with collaborators.
- The automated script `tools/run_redteam_checks.ps1` performs non-destructive checks locally. It does not perform active attacks outside your environment.

Overview (high level)
1) Recon & Inventory
2) Local exploit & validation (lab focus)
3) Hardening verification
4) Clean-up and reporting

1) Recon & Inventory
- Identify all hosts/services (docker-compose):
  pwsh> docker compose ps
- Inspect exposed ports and config files:
  pwsh> Get-Content docker-compose.yml
  pwsh> Get-Content lab_server/nginx.conf
- Search repo for potential secrets:
  pwsh> Select-String -Path **/* -Pattern "(password|passwd|secret|TOKEN|SECRET|KEY)" -SimpleMatch -List
- Run quick secret-scanners (recommend on isolated machine):
  - git-secrets (install): https://github.com/awslabs/git-secrets
  - truffleHog (python/pip): pip install truffleHog
  pwsh> trufflehog filesystem . --quiet

2) Local exploit & validation (lab-specific)
- Start the stack locally (use override for local testing already present):
  pwsh> docker compose up -d
  pwsh> docker compose logs -f --tail 100 lab
- Run the automated checks (non-destructive):
  pwsh> .\tools\run_redteam_checks.ps1
- Manual checks/examples (PowerShell)
  - Decode endpoint (requires ADMIN_TOKEN):
    pwsh> Invoke-RestMethod -Uri "http://127.0.0.1:8000/decode-login?username=user&password=userpass" -Headers @{"X-ADMIN-TOKEN" = (Get-Content .\secrets\ADMIN_TOKEN).Trim()} -Method GET
  - CSRF enforcement test:
    pwsh> # Use the included probe scripts which use Flask test client; see tools/redteam_probe.py

3) Hardening verification
- Confirm `SESSION_COOKIE_SECURE` set to 1 in production and ensure HTTPS/nginx terminates TLS.
- Ensure `DECODE_ENABLED` is disabled in production config.
- Rate-limit /decode-login and admin endpoints via Redis or upstream WAF.
- Confirm `uploads/` uses `secure_filename` and maximum content length.

4) Cleanup and reporting
- If secrets were accidentally committed, purge history (see next section), rotate any leaked secrets, and force-push the cleaned repo.
- Produce red-team report with: scope, findings (vulns, PoCs), risk rating, remediation steps, and verification checklist.

History purge (exact commands)
- Recommended: use git-filter-repo.
  1) Create a mirror backup (do this on a machine where you have credentials):
     pwsh> git clone --mirror https://github.com/burnstime/lrc-barr3l-r0ll-pr0j3ct.git repo-mirror.git
  2) Run filter-repo to remove paths (example removing uploads/secret.txt):
     pwsh> cd repo-mirror.git
     pwsh> git-filter-repo --invert-paths --paths uploads/secret.txt
  3) Verify the file is gone:
     pwsh> git log --all -- uploads/secret.txt
  4) Force-push cleaned mirror back to GitHub:
     pwsh> git push --force
  5) Coordinate: ask all collaborators to reclone.

- Alternative: BFG cleaner
  1) git clone --mirror https://github.com/your/repo.git repo-mirror.git
  2) java -jar bfg.jar --delete-files uploads/secret.txt repo-mirror.git
  3) cd repo-mirror.git
     git reflog expire --expire=now --all
     git gc --prune=now --aggressive
  4) git push --force

Collaboration & rollback guidance
- Announce a maintenance window and backup the repo mirror.
- After force-push, any forks or local clones will have diverging history. Instruct contributors to re-clone or run:
  pwsh> git fetch origin
  pwsh> git reset --hard origin/main
- Keep the backup mirror until all collaborators have migrated (then securely delete it).

Deliverables the red team would produce
- A PoC repository or branch with safe scripts demonstrating findings (no secret exfiltration in artifacts).
- A final report (PDF/Markdown) listing findings, PoCs, remediation steps, and evidence (logs/screenshots).
- A remediation verification checklist (unit tests, CI guards, git pre-commit hooks for secret scanning).

If you want me to automate the full purge (mirror, filter-repo, force-push) I can prepare a runnable script — I will not execute it unless you explicitly ask me to run it here.

