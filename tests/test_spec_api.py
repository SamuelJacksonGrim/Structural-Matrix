"""Conformance to docs/DEVELOPER_SPEC.md — the public API and output contract."""

import pytest

from structural_matrix import analyze_sequence
from structural_matrix.analyzer import StructuralMatrixAnalyzer

EXAMPLES = {
    "A B B C A B C C C A": "ENGINEERED",
    "X Y X Z Y X Y Y Z X Y Z": "NATURAL",
    "Q W E R T Y U I O P": "RANDOM",
    "A A B A A B C C A A B": "CONSTRUCTED",
}

SPEC_ROLE_NAMES = {"ANCHOR", "FRAME", "TRANSITION", "CONTENT", "TERMINATOR", "UNASSIGNED"}


def test_result_has_all_spec_keys():
    r = analyze_sequence("A B B C A B C C C A")
    for key in (
        "symbols",
        "mapping",
        "numeric_sequence",
        "roles",
        "role_sequence",
        "transitions",
        "motifs",
        "entropy",
        "classification",
    ):
        assert key in r, f"missing spec key: {key}"
    for key in ("symbol_entropy", "transition_entropy", "cluster_stats"):
        assert key in r["entropy"], f"missing entropy key: {key}"


@pytest.mark.parametrize("text,expected", EXAMPLES.items())
def test_classification_is_uppercase_and_correct(text, expected):
    assert analyze_sequence(text)["classification"] == expected


def test_classification_is_one_of_four_for_symbolic_input():
    # The facade passes no proximity, so 3D-Driven can never appear: the spec's
    # 4-class contract holds.
    for text in EXAMPLES:
        assert analyze_sequence(text)["classification"] in {
            "NATURAL",
            "ENGINEERED",
            "CONSTRUCTED",
            "RANDOM",
        }


def test_roles_is_symbol_to_role_mapping():
    r = analyze_sequence("A B B C A B C C C A")
    assert set(r["roles"].keys()) == {"A", "B", "C"}
    assert all(v in SPEC_ROLE_NAMES for v in r["roles"].values())


def test_role_sequence_aligns_with_symbols():
    r = analyze_sequence("A B B C A B C C C A")
    assert len(r["role_sequence"]) == len(r["symbols"])
    assert all(role in SPEC_ROLE_NAMES for role in r["role_sequence"])


def test_numeric_sequence_matches_mapping():
    r = analyze_sequence("A B C A")
    assert r["numeric_sequence"] == [r["mapping"][s] for s in r["symbols"]]
    assert all(isinstance(v, int) for v in r["numeric_sequence"])


def test_role_level_transition_matrix_counts():
    r = analyze_sequence("A A B A A B C C A A B")
    trans = r["transitions"]
    # Keys are (role_from, role_to) tuples; counts are positive ints.
    assert all(isinstance(k, tuple) and len(k) == 2 for k in trans)
    assert all(isinstance(v, int) and v > 0 for v in trans.values())
    # Total transitions == n - 1.
    assert sum(trans.values()) == len(r["symbols"]) - 1


def test_entropy_scalars_are_floats_in_bits():
    r = analyze_sequence("A B B C A B C C C A")
    e = r["entropy"]
    assert isinstance(e["symbol_entropy"], float) and e["symbol_entropy"] >= 0.0
    assert isinstance(e["transition_entropy"], float) and e["transition_entropy"] >= 0.0


def test_symbol_entropy_uniform_alphabet():
    # Four equally frequent symbols -> 2 bits.
    r = analyze_sequence("A B C D A B C D")
    assert r["entropy"]["symbol_entropy"] == pytest.approx(2.0)


def test_cluster_stats_detects_runs():
    cs = analyze_sequence("A B B C C C A")["entropy"]["cluster_stats"]
    assert cs["cluster_count"] == 2          # "BB" and "CCC"
    assert cs["max_cluster_length"] == 3     # "CCC"
    assert "C" in cs["dominant_symbols"]


def test_analyzer_class_matches_helper():
    text = "A A B A A B C C A A B"
    assert StructuralMatrixAnalyzer(text).analyze() == analyze_sequence(text)


def test_accepts_token_list_not_just_string():
    # Spec: sequences may be strings or lists of tokens.
    r = analyze_sequence(["A", "B", "B", "C"])
    assert r["symbols"] == ["A", "B", "B", "C"]
