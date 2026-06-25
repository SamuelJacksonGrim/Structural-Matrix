"""Stage-level tests: types, mapping, behaviour, cohesion."""

import math

import pytest

from structural_matrix.behaviour import StandardBehaviourAnalyzer
from structural_matrix.cohesion import StandardCohesionAnalyzer
from structural_matrix.mapping import (
    FrequencyMapper,
    OrdinalMapper,
    get_mapper,
)
from structural_matrix.types import Sequence


# --------------------------------------------------------------------------- #
# Sequence
# --------------------------------------------------------------------------- #
def test_sequence_from_whitespace():
    s = Sequence.from_text("A B B C")
    assert s.symbols == ("A", "B", "B", "C")
    assert s.n == 4
    assert s.alphabet == ("A", "B", "C")


def test_sequence_from_chars():
    s = Sequence.from_text("ABBC", sep="")
    assert s.symbols == ("A", "B", "B", "C")


def test_alphabet_is_first_appearance_order():
    s = Sequence.from_text("C A C B A")
    assert s.alphabet == ("C", "A", "B")


def test_empty_sequence():
    s = Sequence.from_text("")
    assert s.n == 0 and s.alphabet == ()


# --------------------------------------------------------------------------- #
# Mapping
# --------------------------------------------------------------------------- #
def test_ordinal_mapping_is_first_appearance():
    sv = OrdinalMapper().map(Sequence.from_text("A B C A"))
    assert sv.mapping == {"A": 1.0, "B": 2.0, "C": 3.0}
    assert sv.values == (1.0, 2.0, 3.0, 1.0)


def test_frequency_mapping_ranks_by_count():
    # B appears most, then A, then C.
    sv = FrequencyMapper().map(Sequence.from_text("A B B B A C"))
    assert sv.mapping["B"] == 1.0
    assert sv.mapping["A"] == 2.0
    assert sv.mapping["C"] == 3.0


def test_mapping_is_deterministic():
    seq = Sequence.from_text("X Y X Z Y")
    a = OrdinalMapper().map(seq)
    b = OrdinalMapper().map(seq)
    assert a.values == b.values


def test_get_mapper_unknown_raises():
    with pytest.raises(ValueError):
        get_mapper("does-not-exist")


# --------------------------------------------------------------------------- #
# Behaviour
# --------------------------------------------------------------------------- #
def _bv(text):
    seq = Sequence.from_text(text)
    sv = OrdinalMapper().map(seq)
    return seq, StandardBehaviourAnalyzer().analyze(seq, sv)


def test_positional_weight_last_is_one():
    _, bv = _bv("A B C D")
    assert bv.positional_weight[-1] == pytest.approx(1.0)
    assert bv.positional_weight[0] == pytest.approx(0.25)


def test_deterministic_symbol_has_zero_entropy():
    # A always goes to B -> entropy 0.
    _, bv = _bv("A B A B A B")
    assert bv.symbol_entropy["A"] == pytest.approx(0.0)
    assert bv.max_transition_prob["A"] == pytest.approx(1.0)


def test_balanced_transition_entropy_is_one_bit():
    # C goes equally to A and C -> 1 bit of entropy.
    _, bv = _bv("C A C C C A")  # transitions: C->A, A->C, C->C, C->C, C->A
    # C: A twice, C twice -> p=.5/.5 -> 1 bit
    assert bv.symbol_entropy["C"] == pytest.approx(1.0, abs=1e-9)


def test_transition_probabilities_sum_to_one():
    _, bv = _bv("A B B C A B C C C A")
    for sym, dist in bv.transition_prob.items():
        if dist:
            assert sum(dist.values()) == pytest.approx(1.0)


# --------------------------------------------------------------------------- #
# Cohesion
# --------------------------------------------------------------------------- #
def test_cohesion_zero_without_proximity():
    seq = Sequence.from_text("A B C")
    scv = StandardCohesionAnalyzer().analyze(seq, None)
    assert scv.cohesion == (0.0, 0.0, 0.0)
    assert not scv.dominant


def test_cohesion_accumulates_both_endpoints():
    seq = Sequence.from_text("A B C D")
    scv = StandardCohesionAnalyzer().analyze(seq, [(0, 3, 2.0)])
    assert scv.cohesion[0] == pytest.approx(2.0)
    assert scv.cohesion[3] == pytest.approx(2.0)
    assert scv.dominant


def test_cohesion_rejects_out_of_range():
    seq = Sequence.from_text("A B")
    with pytest.raises(IndexError):
        StandardCohesionAnalyzer().analyze(seq, [(0, 5, 1.0)])


def test_cohesion_rejects_negative_weight():
    seq = Sequence.from_text("A B")
    with pytest.raises(ValueError):
        StandardCohesionAnalyzer().analyze(seq, [(0, 1, -1.0)])
