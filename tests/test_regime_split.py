"""Entropy-cascade regime split (spec §5.7) — structure -> noise health signal."""

import random

from structural_matrix import StructuralMatrix
from structural_matrix.motifs import StandardMotifDetector
from structural_matrix.types import MotifType

engine = StructuralMatrix()


def test_structure_then_noise_emits_cascade():
    # First half: a clean deterministic cycle (low entropy). Second half: random
    # high-entropy churn. The regime split should fire.
    rng = random.Random(3)
    structured = ["A", "B"] * 15           # A->B->A->B ... entropy ~0
    noisy = [rng.choice("CDEFGHIJ") for _ in range(30)]
    report = engine.analyze(structured + noisy)
    assert report.motifs.has(MotifType.ENTROPY_CASCADE)


def test_stationary_stream_no_false_cascade():
    # Uniformly random throughout -> halves have similar entropy -> no split.
    split = StandardMotifDetector._entropy_regime_split(tuple([1.0] * 40))
    assert split is None


def test_short_sequence_never_splits():
    assert StandardMotifDetector._entropy_regime_split((0.0, 1.0, 0.0)) is None


def test_worked_examples_keep_their_classification():
    # The regime split must not disturb the four canonical verdicts.
    from structural_matrix.types import StructuralClass

    cases = {
        "A B B C A B C C C A": StructuralClass.ENGINEERED,
        "X Y X Z Y X Y Y Z X Y Z": StructuralClass.NATURAL,
        "Q W E R T Y U I O P": StructuralClass.RANDOM,
        "A A B A A B C C A A B": StructuralClass.CONSTRUCTED,
    }
    for text, expected in cases.items():
        assert engine.analyze(text).classification.label == expected
