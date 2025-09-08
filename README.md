# leftrightbarrelroll

This repository contains a small utility to generate "spoofed" variants of input strings using Unicode confusables, combining marks, invisible characters, directional overrides, and (optionally) raw control characters.

Key modes

- Full mode (default *historical* behaviour): applies confusable glyph replacements, invisibles, combining marks, directionals, and control characters. This mode can produce visually deceptive strings and may include characters that affect rendering, searching, logging, or terminal behavior.

- Safe mode (`safe=True` or CLI: `--disable-controls` plus enabling safe checks): disables all risky injections: no raw control characters, no directional overrides, and no invisible or combining marks. Use safe mode for unit tests, analysis, or any context where you must avoid altering text semantics or terminal behavior.

Defaults and CLI

- Function defaults: `generate_attack_corpus(..., allow_controls=False, safe=False)` — controls are disabled by default for safety; `safe` must be explicitly enabled if you want to block invisibles/combining/directionals.
- CLI options (when running `python leftrightbarrelroll.py`):
  - `--variants/-n`: variants per input (default 5)
  - `--stealth`: reduces intensity/probabilities of injected artifacts
  - `--seed`: optional RNG seed for reproducible output
  - `--disable-controls`: disables raw control-character injection (controls are disabled by default)

Safety and warnings

- Do NOT copy/paste generated strings from the full mode into terminals, logs, or systems that interpret directionals or control characters. Spoofed text may:
  - Visually look like legitimate strings while being different (homoglyphs), which can be used for phishing or deception.
  - Contain directional override characters that change the visual order when rendered.
  - Contain control characters (e.g. NUL, BEL, ESC) that can interfere with terminals or file formats.

- Use `safe=True` or `--disable-controls` when you only need to test matching/processing logic without the side-effects.

Recommended usage

- Tests: use deterministic seeds (via `--seed` or `seed=`) and `safe=True` to avoid non-determinism and side-effects.
- Exploratory / demonstration: try `python leftrightbarrelroll.py --variants 10 --seed 123` and inspect outputs carefully in a safe viewer.

License

- This is a small demo utility; treat generated strings responsibly.
