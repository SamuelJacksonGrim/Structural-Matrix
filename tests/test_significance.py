"""Permutation null-model significance."""

from structural_matrix import structure_significance


def test_structured_stream_is_significant():
    # A clean periodic anchor cycle: real order is far more structured than chance.
    seq = "A B C A B C A B C A B C A B C"
    result = structure_significance(seq, trials=200, seed=1)
    assert result["observed_structuredness"] > result["mean_shuffled_structuredness"]
    assert result["p_value"] < 0.05
    assert result["significant"] is True


def test_all_distinct_stream_is_not_significant():
    # No structure in any ordering -> must NOT be flagged significant.
    seq = "Q W E R T Y U I O P"
    result = structure_significance(seq, trials=100, seed=1)
    assert result["significant"] is False


def test_p_value_is_a_probability():
    r = structure_significance("A A B A A B C C A A B", trials=50, seed=2)
    assert 0.0 < r["p_value"] <= 1.0


def test_deterministic_given_seed():
    a = structure_significance("A B B C A B C C C A", trials=80, seed=7)
    b = structure_significance("A B B C A B C C C A", trials=80, seed=7)
    assert a == b
