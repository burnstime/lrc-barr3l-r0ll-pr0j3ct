#!/usr/bin/env python3
"""Safer pylint runner that uses pylint API and writes a stable report.

Usage: python tools/run_pylint_safe.py
"""
import sys
import subprocess
from pathlib import Path
import io


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
    out_lines = []
    out_lines.append('Pylint run: {} files\n'.format(len(files)))

    # Import here to minimize side-effects if installation failed above
    from pylint import lint  # type: ignore

    for f in files:
        out_lines.append('\n--- FILE: {} ---\n'.format(f))
        sio = io.StringIO()
        try:
            # pylint.lint.Run writes to stdout; capture it
            lint.Run(['--score=no', '--output-format=text', f], do_exit=False, reporter=None)
        except SystemExit:
            # Some versions may call exit; ignore
            pass
        except Exception as e:
            sio.write('pylint error for {}: {}\n'.format(f, e))
        # Fetch the output by running pylint as a subprocess to be reliable per-file
        p = subprocess.run([sys.executable, '-m', 'pylint', '--score=no', '--output-format=text', f], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        out_lines.append(p.stdout or '')

    report.write_text(''.join(out_lines))
    print('Wrote', report)
    # Print head
    print('\n'.join(report.read_text().splitlines()[:300]))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
