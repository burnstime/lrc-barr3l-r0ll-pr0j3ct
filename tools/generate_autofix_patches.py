#!/usr/bin/env python3
"""Generate conservative auto-fix patches for obvious high-confidence issues.

Current rules implemented (conservative):
- Replace patterns like `os.system(<literal string>)` with `subprocess.run([...], shell=False)` when safe.
- Replace `subprocess.call(cmd, shell=True)` with `subprocess.run(cmd, shell=False)` if cmd is a literal list or simple string without concatenation.

The script is intentionally conservative and will only produce patches when the pattern is simple.
"""
import os
import re
import difflib
from pathlib import Path

SRC_EXTS = ['.py']
OUT_DIR = 'AUTO_FIXES'
os.makedirs(OUT_DIR, exist_ok=True)


def scan_files():
    for root, dirs, files in os.walk('.'):
        for f in files:
            if any(f.endswith(ext) for ext in SRC_EXTS):
                yield os.path.join(root, f)


def apply_rules_to_file(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
        orig = fh.read().splitlines(keepends=True)

    new = orig[:]
    changed = False

    # rule: os.system("cmd") -> subprocess.run(["cmd"], shell=False)
    pattern_os_system = re.compile(r"^\s*(?:os\.)system\((['\"])(.+?)\1\)\s*$")
    for i, line in enumerate(orig):
        m = pattern_os_system.search(line)
        if m:
            cmd = m.group(2)
            replacement = f"subprocess.run([{repr(cmd)}], shell=False)\n"
            new[i] = replacement
            changed = True

    # rule: subprocess.call('cmd', shell=True) -> subprocess.run(cmd, shell=False) if cmd is literal
    pattern_sub_call = re.compile(r"^\s*subprocess\.call\((['\"])(.+?)\1\s*,\s*shell\s*=\s*True\s*\)\s*$")
    for i, line in enumerate(list(new)):
        m = pattern_sub_call.search(line)
        if m:
            cmd = m.group(2)
            replacement = f"subprocess.run({repr(cmd)}, shell=False)\n"
            new[i] = replacement
            changed = True

    if not changed:
        return None

    diff = ''.join(difflib.unified_diff(orig, new, fromfile=path, tofile=path + '.autofix', lineterm=''))
    if diff.strip():
        out_name = path.replace(os.sep, '_').lstrip('./') + '.patch'
        out_path = os.path.join(OUT_DIR, out_name)
        with open(out_path, 'w', encoding='utf-8') as out:
            out.write(diff)
        return out_path
    return None


def main():
    patches = []
    for f in scan_files():
        try:
            p = apply_rules_to_file(f)
            if p:
                print('Wrote autofix patch', p)
                patches.append(p)
        except Exception as e:
            print('Error scanning', f, e)
    print('Auto-fix patch generation complete')


if __name__ == '__main__':
    main()
