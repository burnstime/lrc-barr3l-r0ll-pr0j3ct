import sys
sys.path.insert(0, r'C:\Users\12265\OneDrive\Documents')

import random
import string
import time

from leftrightbarrelroll import (
    worst_case_spoof,
    generate_attack_corpus,
    INVISIBLES,
    COMBINING,
    DIRECTIONALS,
    CONTROLS,
)


def random_input(alphabet: str, min_len=1, max_len=50):
    length = random.randint(min_len, max_len)
    return ''.join(random.choice(alphabet) for _ in range(length))


def test_fuzz_uniqueness_and_no_controls_default():
    random.seed(12345)
    alphabet = string.ascii_letters + string.digits + string.punctuation + ' '
    samples = [random_input(alphabet, 1, 40) for _ in range(200)]

    total = 0
    changed = 0
    for s in samples:
        total += 1
        variants = generate_attack_corpus([s], variants_per_item=5, seed=42, allow_controls=False)
        spoofs = [v['spoofed'] for v in variants]
        # Ensure at least one variant differs from original when input contains a letter
        if any(ch.isalpha() for ch in s):
            assert any(sp != s for sp in spoofs)
        # Ensure no control characters were injected
        for sp in spoofs:
            assert not any(c in sp for c in CONTROLS)
        if any(sp != s for sp in spoofs):
            changed += 1

    # At least some fraction of inputs should produce changed variants
    assert changed / total > 0.3


def test_fuzz_safe_mode_no_artifacts():
    random.seed(54321)
    alphabet = string.ascii_letters + string.digits + ' '
    samples = [random_input(alphabet, 1, 60) for _ in range(200)]

    for s in samples:
        sp = worst_case_spoof(s, stealth=False, allow_controls=False, safe=True)
        # safe mode must not include invisibles, combining marks, directionals, or controls
        assert not any(ch in sp for ch in INVISIBLES)
        assert not any(ch in sp for ch in COMBINING)
        assert not any(ch in sp for ch in DIRECTIONALS)
        assert not any(ch in sp for ch in CONTROLS)


def test_fuzz_performance_long_inputs():
    random.seed(1)
    alphabet = string.ascii_letters
    samples = [random_input(alphabet, 80, 120) for _ in range(200)]

    start = time.time()
    for s in samples:
        _ = worst_case_spoof(s, stealth=True, allow_controls=False, safe=False)
    elapsed = time.time() - start

    # Should complete reasonably quickly in local environment
    assert elapsed < 5.0

