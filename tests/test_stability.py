"""Verdict stability metric."""

from structural_matrix import verdict_stability


def test_strongly_structured_stream_is_robust():
    r = verdict_stability("A B C A B C A B C A B C A B C", seed=1)
    assert r["stability"] in {"robust", "marginal"}
    assert r["score_margin"] > 0.0
    assert 0.0 <= r["jackknife_stability"] <= 1.0


def test_random_stream_verdict():
    r = verdict_stability("Q W E R T Y U I O P", seed=1)
    assert r["classification"] == "RANDOM"
    assert "stability" in r


def test_fields_present_and_typed():
    r = verdict_stability("A A B A A B C C A A B", seed=3)
    for k in (
        "classification",
        "score_margin",
        "jackknife_stability",
        "perturbations_tested",
        "stability",
    ):
        assert k in r
    assert r["stability"] in {"robust", "marginal", "fragile"}


def test_short_sequence_is_robust_by_convention():
    r = verdict_stability("A B", seed=0)
    assert r["jackknife_stability"] == 1.0


def test_deterministic_given_seed():
    a = verdict_stability("A B B C A B C C C A", seed=5, max_perturbations=10)
    b = verdict_stability("A B B C A B C C C A", seed=5, max_perturbations=10)
    assert a == b
