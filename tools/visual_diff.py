import html
from typing import Tuple


def mark_differences(a: str, b: str) -> Tuple[str, str]:
    """Return (a_html, b_html) where differing codepoints are wrapped in <mark> tags and output is HTML-escaped.

    This function is intentionally conservative: it compares codepoints and highlights positions where they differ.
    """
    a_pts = [ord(c) for c in a]
    b_pts = [ord(c) for c in b]
    maxlen = max(len(a_pts), len(b_pts))

    a_out = []
    b_out = []
    for i in range(maxlen):
        ca = chr(a_pts[i]) if i < len(a_pts) else ''
        cb = chr(b_pts[i]) if i < len(b_pts) else ''
        if i >= len(a_pts) or i >= len(b_pts) or a_pts[i] != b_pts[i]:
            a_fragment = html.escape(ca) if ca else ''
            b_fragment = html.escape(cb) if cb else ''
            if a_fragment:
                a_out.append(f"<mark>{a_fragment}</mark>")
            if b_fragment:
                b_out.append(f"<mark>{b_fragment}</mark>")
        else:
            esc = html.escape(ca)
            a_out.append(esc)
            b_out.append(esc)

    return ''.join(a_out), ''.join(b_out)


def row_to_html(original: str, spoofed: str) -> str:
    a_html, b_html = mark_differences(original, spoofed)
    return f"<tr><td><code>{a_html}</code></td><td><code>{b_html}</code></td></tr>"
