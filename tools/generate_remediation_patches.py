#!/usr/bin/env python3
"""Generate remediation patch files from semgrep JSON results.

This script reads artifacts/security/semgrep.json and produces unified diff
patch files under REMEDIATION_PATCHES/. It inserts a safe TODO comment above
the offending line with a short suggested remediation message so maintainers
can review and apply the patch.

The script is intentionally conservative: it does not change code semantics,
only inserts hint comments.
"""
import json
import os
import sys
import difflib
from collections import defaultdict

SEM_FILE = 'artifacts/security/semgrep.json'
OUT_DIR = 'REMEDIATION_PATCHES'

if not os.path.exists(SEM_FILE):
    print(f'{SEM_FILE} not found', file=sys.stderr)
    sys.exit(0)

with open(SEM_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

results = data.get('results', []) if isinstance(data, dict) else []

# aggregate comments per file
comments = defaultdict(list)

for r in results:
    path = r.get('path') or r.get('path')
    if not path:
        # semgrep v1 uses path/extra; attempt to extract
        path = r.get('extra', {}).get('path')
    if not path:
        continue
    start = r.get('start', {}).get('line') or r.get('extra', {}).get('start')
    message = r.get('extra', {}).get('message') or r.get('message') or ''
    check_id = r.get('check_id') or r.get('rule_id') or r.get('rule') or r.get('id')
    suggestion = f"[semgrep:{check_id}] Suggested remediation: {message}" if check_id else f"Suggested remediation: {message}"
    try:
        ln = int(start)
    except Exception:
        ln = 1
    comments[path].append((ln, suggestion))

os.makedirs(OUT_DIR, exist_ok=True)

for path, items in comments.items():
    if not os.path.exists(path):
        print(f'skipping missing file {path}')
        continue
    # read original content
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        orig_lines = f.readlines()

    # insert comments; sort by line descending to keep indices stable
    items_sorted = sorted(items, key=lambda x: x[0], reverse=True)
    new_lines = orig_lines[:]
    for ln, suggestion in items_sorted:
        insert_at = max(0, ln - 1)
        comment = f"# REMEDIATION-SUGGESTION: {suggestion}\n"
        # avoid duplicate comment insertion
        if insert_at < len(new_lines) and suggestion in new_lines[insert_at]:
            continue
        new_lines.insert(insert_at, comment)

    # compute unified diff
    diff = ''.join(difflib.unified_diff(orig_lines, new_lines, fromfile=path, tofile=path + '.remediated', lineterm=''))
    if not diff.strip():
        continue
    safe_name = path.replace(os.sep, '_').replace('/', '_')
    out_path = os.path.join(OUT_DIR, f'{safe_name}.patch')
    with open(out_path, 'w', encoding='utf-8') as out:
        out.write(diff)
    print(f'Wrote patch {out_path}')

print('Remediation patch generation complete')
