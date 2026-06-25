"""Property / fuzz tests — the engine must stay total (never crash, always valid).

These encode the runtime half of the Contracts: for *any* input, the pipeline
produces a well-formed report. We use a fixed RNG seed so failures reproduce.
"""

import math
import random
import string

import pytest

from structural_matrix import StructuralMatrix
from structural_matrix.types import Role, StructuralClass

engine = StructuralMatrix()


def _assert_valid_report(report):
    n = report.sequence.n
    # One role per position.
    assert len(report.roles.roles) == n
    assert all(isinstance(r, Role) for r in report.roles.roles)
    # At least one motif is always emitted (Null when nothing else).
    assert len(report.motifs.motifs) >= 1
    # Scores finite; confidence a valid probability.
    c = report.classification
    assert all(math.isfinite(v) for v in c.scores.values())
    assert 0.0 <= c.confidence <= 1.0
    assert isinstance(c.label, StructuralClass)
    # Behaviour vectors are the right length.
    assert len(report.behaviour_vector.entropy) == n
    assert len(report.behaviour_vector.positional_weight) == n


# --------------------------------------------------------------------------- #
# Adversarial fixed shapes.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "text,sep",
    [
        ("", None),               # empty
        ("A", None),              # single token
        ("A A A A A A", None),    # single-symbol alphabet (log2(1)=0 risk)
        ("A B C D E F", None),    # all distinct
        ("café déjà café", None), # unicode tokens
        ("AABBAABB", ""),         # char split
        ("x", ""),                # single char
    ],
)
def test_adversarial_shapes_are_total(text, sep):
    from structural_matrix.types import Sequence

    report = engine.analyze(Sequence.from_text(text, sep=sep))
    _assert_valid_report(report)


def test_single_symbol_alphabet_no_div_by_zero():
    # Alphabet size 1 -> max possible entropy log2(1)=0; must not divide by zero.
    report = engine.analyze("Z Z Z Z Z Z Z Z")
    _assert_valid_report(report)
    assert all(math.isfinite(v) for v in report.classification.scores.values())


# --------------------------------------------------------------------------- #
# Randomised fuzzing.
# --------------------------------------------------------------------------- #
def test_random_sequences_never_crash():
    rng = random.Random(20260625)
    alphabets = [
        "AB",
        "ACGT",
        string.ascii_uppercase[:6],
        string.ascii_letters,
    ]
    for _ in range(400):
        alpha = rng.choice(alphabets)
        n = rng.randint(0, 60)
        seq = [rng.choice(alpha) for _ in range(n)]
        report = engine.analyze(seq)
        _assert_valid_report(report)


def test_long_sequence_performance_smoke():
    rng = random.Random(7)
    seq = [rng.choice("ACGT") for _ in range(5000)]
    report = engine.analyze(seq)
    _assert_valid_report(report)
    assert report.sequence.n == 5000


def test_random_dna_classifies_to_a_real_class():
    # Per the methodology's "GEMINI INSTRUCTIONS": random DNA should land in a
    # natural/random-like class, never crash, and never be 3D-Driven (no proximity).
    rng = random.Random(1)
    dna = [rng.choice("ACGT") for _ in range(200)]
    report = engine.analyze(dna)
    _assert_valid_report(report)
    assert report.classification.label != StructuralClass.THREE_D_DRIVEN
