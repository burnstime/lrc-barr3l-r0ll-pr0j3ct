#!/usr/bin/env python3
"""Compile-check all tracked .py files and write a report for failures.

Usage: python tools/compile_check.py
"""
import os
import sys
import py_compile
import subprocess
from datetime import datetime

def git_tracked_py_files():
    p = subprocess.run(["git", "ls-files", "*.py"], capture_output=True, text=True)
    if p.returncode != 0:
        print("Failed to list tracked files", file=sys.stderr)
        sys.exit(1)
    return [l.strip() for l in p.stdout.splitlines() if l.strip()]

def main():
    files = git_tracked_py_files()
    if not files:
        print("No tracked .py files found.")
        return 0
    failures = []
    for f in files:
        print(f"Checking: {f}")
        try:
            # py_compile raises PyCompileError on syntax errors
            py_compile.compile(f, doraise=True)
        except Exception as e:
            failures.append((f, str(e)))

    if not failures:
        print("All files compiled successfully.")
        return 0

    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    report = f"compile_errors_{ts}.txt"
    with open(report, 'w', encoding='utf-8') as fh:
        for f, msg in failures:
            fh.write(f"--- FILE: {f} ---\n")
            fh.write(msg + "\n\n")

    print(f"Total compile failures: {len(failures)}")
    for f, _ in failures:
        print(f"FAIL: {f}")
    print(f"Wrote detailed report to: {report}")
    return 2

if __name__ == '__main__':
    sys.exit(main())
