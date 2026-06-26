"""Unified `measure()` instrument readout."""

import json

from structural_matrix import measure


def test_base_readout_is_json_safe_and_complete():
    r = measure("A B B C A B C C C A")
    json.dumps(r)  # must not raise
    for k in (
        "classification",
        "confidence",
        "n",
        "alphabet_size",
        "roles",
        "motifs",
        "entropy",
        "transitions",
    ):
        assert k in r
    assert r["classification"] == "ENGINEERED"
    assert r["significance"] is None and r["stability"] is None and r["timeline"] is None


def test_opt_in_significance_and_stability():
    r = measure("A B C A B C A B C A B C", significance_trials=60, stability=True)
    assert r["significance"] is not None
    assert "p_value" in r["significance"]
    assert r["stability"] is not None
    assert r["stability"]["stability"] in {"robust", "marginal", "fragile"}


def test_opt_in_timeline():
    r = measure(["A", "B"] * 40, window=10)
    assert r["timeline"] is not None
    assert r["timeline"]["n_windows"] >= 1
    json.dumps(r)  # still serialisable with the timeline attached


def test_confidence_is_probability():
    r = measure("Q W E R T Y U I O P")
    assert 0.0 <= r["confidence"] <= 1.0
