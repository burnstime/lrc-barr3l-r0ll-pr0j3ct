#!/usr/bin/env python3
"""Run pylint using its Python API and TextReporter to capture output per file.

This avoids shell quoting issues in the environment.
"""
import sys
import subprocess
from pathlib import Path


def ensure_pylint():
    try:
        import pylint  # type: ignore
        return True
    except Exception:
        print('pylint not importable; attempting to install via pip...')
        r = subprocess.run([sys.executable, '-m', 'pip', 'install', 'pylint==2.17.4', '--disable-pip-version-check', '-q'])
        return r.returncode == 0


def gather_files():
    r = subprocess.run(['git', 'ls-files', '*.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        print('git ls-files failed:', r.stderr)
        return []
    return [s for s in r.stdout.splitlines() if s.strip()]


def main():
    if not ensure_pylint():
        print('Failed to ensure pylint is installed/importable. Aborting.')
        return 2

    files = gather_files()
    if not files:
        print('No tracked python files found.')
        return 0

    report = Path('pylint_report.txt')
    parts = []
    parts.append(f'Pylint run: {len(files)} files\n')

    # Import pylint API
    from pylint.lint import Run  # type: ignore
    from pylint.reporters.text import TextReporter  # type: ignore
    import io

    for f in files:
        parts.append('\n--- FILE: {} ---\n'.format(f))
        sio = io.StringIO()
        reporter = TextReporter(output=sio)
        try:
            Run(['--score=no', '--output-format=text', f], reporter=reporter, do_exit=False)
        except Exception as e:
            parts.append(f'pylint exception for {f}: {e}\n')
        parts.append(sio.getvalue())

    report.write_text(''.join(parts))
    print('Wrote', report)
    print('\n'.join(report.read_text().splitlines()[:300]))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
