"""The offline BCU seed→key derivation harness.

Pairs synthesised from a known transform must be recovered; pairs from no transform
must report no fit; and too-little evidence must stay unconfirmed rather than guess.
"""
from d2diag.bcu.keygen import MASK16, build_keygen, fit
from d2diag.td5.keygen import key_from_seed

_SEEDS = [0x1234, 0xABCD, 0x0001, 0x8000, 0x4A4D, 0xEB12]


def _pairs(fn):
    return [(s, fn(s) & MASK16) for s in _SEEDS]


def test_recovers_xor_mask():
    report = fit(_pairs(lambda s: s ^ 0xBEEF))
    assert report["ok"] and report["model"] == "xor-mask"
    assert report["params"]["mask"] == 0xBEEF
    keygen = build_keygen(report)
    assert all(keygen(s) == (s ^ 0xBEEF) for s in _SEEDS)


def test_recovers_affine():
    a, b = 0x4A2B, 0x1234  # a is odd → invertible mod 2**16
    report = fit(_pairs(lambda s: (a * s + b) & MASK16))
    assert report["ok"] and report["model"] == "affine"
    keygen = build_keygen(report)
    assert all(keygen(s) == ((a * s + b) & MASK16) for s in _SEEDS)


def test_recovers_rotate_xor():
    report = fit(_pairs(lambda s: (((s << 3) | (s >> 13)) & MASK16) ^ 0x00FF))
    assert report["ok"] and report["model"] == "rotl-xor"
    assert report["params"]["rot"] == 3


def test_recognises_the_td5_algorithm():
    report = fit(_pairs(key_from_seed))
    assert report["ok"] and report["model"] == "td5-lfsr"


def test_no_fit_for_unstructured_pairs():
    report = fit([(0x0001, 0x0005), (0x0002, 0x0009), (0x0003, 0x0002), (0x0004, 0x00FF)])
    assert not report["ok"] and "fits" in report["reason"]


def test_one_pair_is_not_confirmed():
    report = fit([(0x1234, 0x5678)])
    assert not report["ok"] and report["pairs_used"] == 1


def test_identical_seeds_cannot_confirm():
    report = fit([(0x1234, 0x9999), (0x1234, 0x9999)])
    assert not report["ok"] and "identical" in report["reason"]


def test_build_keygen_returns_none_for_a_failed_fit():
    assert build_keygen({"ok": False, "reason": "x"}) is None
