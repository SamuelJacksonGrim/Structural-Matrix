"""Role-level motif detection (spec §5) — patterns over the role sequence."""

from structural_matrix import StructuralMatrix
from structural_matrix.motifs import StandardMotifDetector
from structural_matrix.types import Motif, MotifType, Role


def _roles(*names):
    return tuple(getattr(Role, n) for n in names)


def test_terminator_lock_from_role_handoff():
    roles = _roles(
        "ANCHOR", "TRANSITION", "CONTENT_BLOCK", "TERMINATOR", "ANCHOR",
        "TRANSITION", "CONTENT_BLOCK", "TERMINATOR", "ANCHOR",
    )
    motifs = StandardMotifDetector._role_level_motifs(roles)
    assert any(m.type == MotifType.TERMINATOR_LOCK for m in motifs)


def test_boundary_frame_from_enclosing_frames():
    roles = _roles("FRAME", "CONTENT_BLOCK", "CONTENT_BLOCK", "FRAME")
    motifs = StandardMotifDetector._role_level_motifs(roles)
    assert any(m.type == MotifType.BOUNDARY_FRAME for m in motifs)


def test_modular_block_from_repeated_role_template():
    roles = _roles(
        "ANCHOR", "TRANSITION", "CONTENT_BLOCK",
        "ANCHOR", "TRANSITION", "CONTENT_BLOCK",
    )
    motifs = StandardMotifDetector._role_level_motifs(roles)
    assert any(m.type == MotifType.MODULAR_BLOCK for m in motifs)


def test_anchor_cycle_gate_blocks_dishonest_emission():
    # Repeating inter-anchor segments, but caller forbids the anchor cycle
    # (no genuine low-entropy anchor) -> must NOT emit ANCHOR_DRIVEN_CYCLE.
    roles = _roles(
        "ANCHOR", "CONTENT_BLOCK", "ANCHOR", "CONTENT_BLOCK", "ANCHOR",
    )
    blocked = StandardMotifDetector._role_level_motifs(roles, allow_anchor_cycle=False)
    assert not any(m.type == MotifType.ANCHOR_DRIVEN_CYCLE for m in blocked)
    allowed = StandardMotifDetector._role_level_motifs(roles, allow_anchor_cycle=True)
    assert any(m.type == MotifType.ANCHOR_DRIVEN_CYCLE for m in allowed)


def test_no_duplicate_motif_types_in_report():
    engine = StructuralMatrix()
    for text in (
        "A B B C A B C C C A",
        "A A B A A B C C A A B",
        "X Y X Z Y X Y Y Z X Y Z",
    ):
        types = [m.type for m in engine.analyze(text).motifs.motifs]
        assert len(types) == len(set(types)), f"duplicate motif types for {text!r}"
