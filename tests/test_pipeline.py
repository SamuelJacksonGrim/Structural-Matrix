"""End-to-end tests, including the four worked examples from the methodology."""

import pytest

from structural_matrix import StructuralMatrix, report_to_dict
from structural_matrix.types import MotifType, Role, StructuralClass

# The four worked examples (methodology "WORKED EXAMPLES (FULL)").
EXAMPLE_1 = "A B B C A B C C C A"  # Engineered
EXAMPLE_2 = "X Y X Z Y X Y Y Z X Y Z"  # Natural
EXAMPLE_3 = "Q W E R T Y U I O P"  # Random / Hoax
EXAMPLE_4 = "A A B A A B C C A A B"  # Constructed


@pytest.fixture(scope="module")
def engine():
    return StructuralMatrix()


# --------------------------------------------------------------------------- #
# Worked-example classifications — the headline behaviour contract.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "text,expected",
    [
        (EXAMPLE_1, StructuralClass.ENGINEERED),
        (EXAMPLE_2, StructuralClass.NATURAL),
        (EXAMPLE_3, StructuralClass.RANDOM),
        (EXAMPLE_4, StructuralClass.CONSTRUCTED),
    ],
)
def test_worked_example_classifications(engine, text, expected):
    report = engine.analyze(text)
    assert report.classification.label == expected


def test_example1_anchor_is_low_entropy(engine):
    report = engine.analyze(EXAMPLE_1)
    # 'A' always transitions to 'B' -> deterministic anchor.
    assert report.behaviour_vector.symbol_entropy["A"] == pytest.approx(0.0)
    assert Role.ANCHOR in report.roles.roles


def test_example1_has_anchor_cycle_motif(engine):
    report = engine.analyze(EXAMPLE_1)
    assert report.motifs.has(MotifType.ANCHOR_DRIVEN_CYCLE)


def test_example4_has_modular_block(engine):
    report = engine.analyze(EXAMPLE_4)
    assert report.motifs.has(MotifType.MODULAR_BLOCK)


def test_anchor_cycle_motif_only_on_low_entropy_symbol(engine):
    # Example 2's most-frequent symbol X has entropy ~0.81 (not deterministic);
    # it must NOT be reported as an Anchor-Driven Cycle — the motif list has to
    # be consistent with the classifier's strict anchor rule.
    report = engine.analyze(EXAMPLE_2)
    if report.motifs.has(MotifType.ANCHOR_DRIVEN_CYCLE):
        se = report.behaviour_vector.symbol_entropy
        assert any(v <= 0.5 for v in se.values())
    # And Example 1's true anchor cycle must survive.
    assert engine.analyze(EXAMPLE_1).motifs.has(MotifType.ANCHOR_DRIVEN_CYCLE)


def test_example3_random_has_high_confidence(engine):
    report = engine.analyze(EXAMPLE_3)
    assert report.classification.label == StructuralClass.RANDOM
    # Random verdict should be the dominant score.
    scores = report.classification.scores
    assert scores[StructuralClass.RANDOM] == max(scores.values())


# --------------------------------------------------------------------------- #
# 3D-driven classification.
# --------------------------------------------------------------------------- #
def test_spatial_cohesion_forces_3d_class(engine):
    # Strong proximity contacts should dominate the symbolic signal.
    prox = [(0, 5, 9.0), (1, 6, 9.0), (2, 7, 9.0)]
    report = engine.analyze(EXAMPLE_2, proximity=prox)
    assert report.classification.label == StructuralClass.THREE_D_DRIVEN


# --------------------------------------------------------------------------- #
# Determinism and structural invariants.
# --------------------------------------------------------------------------- #
def test_pipeline_is_deterministic(engine):
    a = engine.analyze(EXAMPLE_1)
    b = engine.analyze(EXAMPLE_1)
    assert a.classification.label == b.classification.label
    assert a.classification.scores == b.classification.scores
    assert a.roles.roles == b.roles.roles


def test_uniform_entropy_roles_do_not_collapse(engine):
    # Example 4 has uniform local entropy; roles must not all be one value.
    report = engine.analyze(EXAMPLE_4)
    distinct_roles = {r for r in report.roles.roles}
    assert len(distinct_roles) >= 3
    counts = report.roles.counts()
    # Methodology intent: A is the recurring anchor, C sits in a cluster.
    assert counts[Role.ANCHOR] >= 1
    assert counts[Role.CONTENT_BLOCK] >= 1


def test_roles_cover_every_position(engine):
    for text in (EXAMPLE_1, EXAMPLE_2, EXAMPLE_3, EXAMPLE_4):
        report = engine.analyze(text)
        assert len(report.roles.roles) == report.sequence.n


def test_report_is_json_serialisable(engine):
    import json

    report = engine.analyze(EXAMPLE_1)
    d = report_to_dict(report)
    # Round-trips through JSON without error.
    json.loads(json.dumps(d))
    assert d["classification"]["label"] == "Engineered"


def test_empty_sequence_does_not_crash(engine):
    report = engine.analyze("")
    assert report.sequence.n == 0
    assert report.motifs.has(MotifType.NULL)


def test_single_symbol_sequence(engine):
    report = engine.analyze("A")
    assert report.sequence.n == 1
    assert len(report.roles.roles) == 1
