#!/usr/bin/env python3
"""A tiny, conservative secrets scanner used for CI and local pre-commit.

Checks:
- High entropy base64-like strings (length >= 20, entropy threshold)
- Common secret keywords in files: AWS, SECRET_KEY, ADMIN_TOKEN, password=, token=

This is intentionally conservative; it exits with code 1 when findings are present.
"""
import os
import sys
import re
import math

# entropy helper
BASE64_RE = re.compile(rb'^[A-Za-z0-9+/=\\n\\r]+$')

KEYWORDS = [
    b'SECRET', b'PASSWORD', b'AWS', b'API_KEY', b'ADMIN_TOKEN', b'TOKEN', b'PRIVATE', b'KEY'
]

findings = []

def shannon_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = {}
    for b in data:
        counts[b] = counts.get(b, 0) + 1
    entropy = 0.0
    length = len(data)
    for c in counts.values():
        p = c / length
        entropy -= p * math.log2(p)
    return entropy


def scan_file(path: str):
    try:
        with open(path, 'rb') as f:
            raw = f.read()
    except Exception:
        return
    # skip binary-ish files over some size
    if len(raw) > 1024 * 1024:
        return
    # keyword scan (case-insensitive)
    low = raw.upper()
    for kw in KEYWORDS:
        if kw in low:
            findings.append((path, f'Keyword match: {kw.decode()}'))
            # don't return; collect multiple
    # base64-ish high-entropy string detection
    tokens = re.findall(rb'[A-Za-z0-9+/=]{20,}', raw)
    for t in tokens:
        if BASE64_RE.match(t):
            ent = shannon_entropy(t)
            if ent > 4.5:
                findings.append((path, f'High-entropy token (len={len(t)}, ent={ent:.2f})'))


def walk_and_scan(root: str):
    # paths to ignore (reports, third-party artifacts)
    IGNORE_PATHS = ['.git', 'node_modules', '__pycache__', 'tools/reports', 'reports']
    for dirpath, dirnames, filenames in os.walk(root):
        # skip ignored dirs
        if any(p in dirpath for p in IGNORE_PATHS):
            continue
        for fn in filenames:
            if fn.endswith(('.pyc', '.png', '.jpg', '.jpeg', '.gif', '.zip')):
                continue
            # skip installer artifacts
            if fn in ('findings.txt',):
                continue
            scan_file(os.path.join(dirpath, fn))


if __name__ == '__main__':
    repo = os.environ.get('GITHUB_WORKSPACE', '.')
    root = sys.argv[1] if len(sys.argv) > 1 else repo
    walk_and_scan(root)
    if findings:
        print('Potential secret findings:')
        for p, m in findings:
            print(f'- {p}: {m}')
        sys.exit(1)
    print('No findings')
    sys.exit(0)
