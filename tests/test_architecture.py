"""Architecture-claim tests: the mapping-agnostic property and the swappable seam.

These guard two promises the docs make:
  * Contracts/§2: the *classification* is mapping-agnostic.
  * Interfaces: any stage can be replaced via constructor injection (Open/Closed).
"""

from structural_matrix import StructuralMatrix
from structural_matrix.interfaces import Classifier
from structural_matrix.mapping import FrequencyMapper, OrdinalMapper
from structural_matrix.types import (
    Classification,
    StructuralClass,
)

EXAMPLES = [
    "A B B C A B C C C A",
    "X Y X Z Y X Y Y Z X Y Z",
    "Q W E R T Y U I O P",
    "A A B A A B C C A A B",
]


def test_classification_is_mapping_agnostic():
    # H5: swapping the f:Σ→ℝ strategy must not change the structural verdict,
    # because behaviour is derived from symbol *transitions*, not the numeric map.
    ordinal = StructuralMatrix(mapper=OrdinalMapper())
    frequency = StructuralMatrix(mapper=FrequencyMapper())
    for text in EXAMPLES:
        a = ordinal.analyze(text).classification.label
        b = frequency.analyze(text).classification.label
        assert a == b, f"{text!r}: {a} != {b}"


class _AlwaysRandom:
    """A stub Classifier proving the seam: ignores everything, returns RANDOM."""

    def classify(self, sequence, bv, scv, roles, motifs) -> Classification:
        scores = {c: 0.0 for c in StructuralClass}
        scores[StructuralClass.RANDOM] = 1.0
        return Classification(StructuralClass.RANDOM, scores, 1.0)


def test_classifier_is_swappable_via_interface():
    # H6: inject a custom Classifier; the engine must use it unchanged.
    assert isinstance(_AlwaysRandom(), Classifier)  # structural Protocol check
    engine = StructuralMatrix(classifier=_AlwaysRandom())
    # Even the canonical Engineered example now reports RANDOM.
    report = engine.analyze("A B B C A B C C C A")
    assert report.classification.label == StructuralClass.RANDOM
    # ...while the upstream stages still ran (roles/motifs are populated).
    assert len(report.roles.roles) == report.sequence.n
    assert len(report.motifs.motifs) >= 1
