"""JSON-safe spec output."""

import json

from structural_matrix import analyze_sequence, to_json_safe


def test_default_keeps_tuple_keys():
    r = analyze_sequence("A B B C A B C C C A")
    assert all(isinstance(k, tuple) for k in r["transitions"])


def test_json_safe_is_serialisable():
    r = analyze_sequence("A B B C A B C C C A", json_safe=True)
    s = json.dumps(r)  # must not raise
    back = json.loads(s)
    assert back["classification"] == "ENGINEERED"
    assert all("->" in k for k in back["transitions"])


def test_helper_matches_flag():
    text = "A A B A A B C C A A B"
    assert to_json_safe(analyze_sequence(text)) == analyze_sequence(text, json_safe=True)


def test_transition_counts_preserved_through_stringify():
    r = analyze_sequence("A B B C A B C C C A")
    safe = to_json_safe(r)
    assert sum(r["transitions"].values()) == sum(safe["transitions"].values())
