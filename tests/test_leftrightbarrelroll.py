import sys
sys.path.insert(0, r'C:\Users\12265\OneDrive\Documents')
from leftrightbarrelroll import worst_case_spoof, generate_attack_corpus, LATIN_TO_SPOOF


def test_seed_reproducibility():
    s1 = generate_attack_corpus(["admin"], variants_per_item=3, seed=42, allow_controls=False)
    s2 = generate_attack_corpus(["admin"], variants_per_item=3, seed=42, allow_controls=False)
    assert [e['spoofed'] for e in s1] == [e['spoofed'] for e in s2]


def test_preserve_case():
    spoofed_obj = worst_case_spoof("Admin", stealth=False, allow_controls=False)
    spoofed = spoofed_obj['spoofed']
    assert spoofed[0].upper() == spoofed[0]


def test_disable_controls():
    s_obj = worst_case_spoof("test", stealth=False, allow_controls=False)
    s = s_obj['spoofed']
    assert "\x00" not in s
    assert "\x07" not in s


def test_defaults_and_safe_mode():
    c = generate_attack_corpus(["admin"], variants_per_item=1)
    assert c[0]["allow_controls"] is False

    s_obj = worst_case_spoof("admin", safe=True, allow_controls=False)
    s = s_obj['spoofed']
    for ch in ['\u200b', '\u202e', '\u0301']:
        assert ch not in s


def test_glyph_coverage():
    keys = list(LATIN_TO_SPOOF.keys())[:10]
    corpus = generate_attack_corpus(keys, variants_per_item=10, seed=123, allow_controls=False)
    groups = {}
    for e in corpus:
        groups.setdefault(e['original'], []).append(e['spoofed'])
    for orig, spoofs in groups.items():
        assert any(s != orig for s in spoofs)


def test_performance_long_input():
    s = 'a' * 20000
    import time
    start = time.time()
    _ = worst_case_spoof(s, stealth=True, allow_controls=False)
    elapsed = time.time() - start
    assert elapsed < 2.0
