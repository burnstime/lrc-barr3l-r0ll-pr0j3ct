#!/usr/bin/env python3
"""Install pylint and run it on all tracked Python files, saving output.

Usage: python tools/run_pylint.py
"""
import subprocess
import sys
from pathlib import Path

def run(cmd, **kwargs):
    return subprocess.run(cmd, shell=False, **kwargs)

def main():
    # Ensure pylint is installed
    print('Ensuring pylint is installed...')
    r = run([sys.executable, '-m', 'pip', 'install', 'pylint==2.17.4', '--disable-pip-version-check', '-q'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        print('pip install failed:', r.stderr[:1000])
        # continue to try running if already present

    # Gather tracked python files
    p = run(['git', 'ls-files', '*.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        print('Failed to list python files:', p.stderr)
        return 2
    files = [s for s in p.stdout.splitlines() if s.strip()]
    if not files:
        print('No tracked python files found.')
        return 0

    print('Running pylint on', len(files), 'files...')
    out = run([sys.executable, '-m', 'pylint', '--score=no', '--output-format=text'] + files, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    report = Path('pylint_report.txt')
    report.write_text(out.stdout or '')
    print('Wrote', report)
    head = '\n'.join((out.stdout or '').splitlines()[:300])
    print(head)
    return out.returncode

if __name__ == '__main__':
    raise SystemExit(main())
