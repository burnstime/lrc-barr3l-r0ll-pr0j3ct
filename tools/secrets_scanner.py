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

# compiled regexes for known secret formats
REGEX_PATTERNS = [
    re.compile(rb'AKIA[0-9A-Z]{16}'),  # AWS Access Key ID
    re.compile(rb'AIza[0-9A-Za-z\-_]{35}'),  # Google API key
    re.compile(rb'"private_key"\s*:\s*"-----BEGIN [A-Z ]+ PRIVATE KEY-----'),  # GCP service account JSON
    re.compile(rb'-----BEGIN (RSA |)PRIVATE KEY-----'),  # PEM private keys
    re.compile(rb'xox[baprs]-[0-9A-Za-z-]{10,}'),  # Slack-ish tokens (approx)
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
    # respect ignore file entries
    try:
        root = os.getcwd()
        ignore_path = os.path.join(root, '.secrets-ignore')
        if os.path.exists(ignore_path):
            with open(ignore_path, 'r', encoding='utf-8') as ig:
                for line in ig:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if line in path or os.path.abspath(os.path.join(root, line)) in path:
                        return
    except Exception:
        pass
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

    # regex-based secret checks
    for rx in REGEX_PATTERNS:
        try:
            if rx.search(raw):
                findings.append((path, f'Regex match: {rx.pattern.decode(errors="ignore")}'))
        except Exception:
            pass


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
