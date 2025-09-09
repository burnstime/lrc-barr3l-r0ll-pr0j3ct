#!/usr/bin/env python3
"""Run pylint on a single file using the pylint API and append to pylint_report.txt

Usage: python tools/pylint_one.py path/to/file.py
"""
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print('Usage: pylint_one.py file.py')
        return 2
    f = sys.argv[1]
    try:
        from pylint.lint import Run  # type: ignore
        from pylint.reporters.text import TextReporter  # type: ignore
        import io
    except Exception as e:
        print('pylint import failed:', e)
        return 3

    sio = io.StringIO()
    reporter = TextReporter(output=sio)
    try:
        Run(['--score=no', '--output-format=text', f], reporter=reporter, do_exit=False)
    except Exception as e:
        sio.write('\nPylint run exception: {}\n'.format(e))

    report = Path('pylint_report.txt')
    with report.open('a', encoding='utf8') as fh:
        fh.write('\n--- FILE: {} ---\n'.format(f))
        fh.write(sio.getvalue())

    print('Appended pylint output for', f)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
