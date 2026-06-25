"""Structural Matrix — Types (the vocabulary).

These are the immutable "things" the system talks about. Every value object here
is frozen so that a pipeline run is reproducible and safe to pass between stages.

The data flow is:

    Sequence -> SymbolVector -> BehaviourVector -> CohesionVector
             -> RoleAssignment -> MotifSet -> Classification -> AnalysisReport
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


# --------------------------------------------------------------------------- #
# Shared tuning constants (single source of truth across stages).
# --------------------------------------------------------------------------- #
# Absolute outgoing-entropy ceiling, in bits, below which a recurring symbol is a
# genuine (near-deterministic) anchor. Used by both the motif detector and the
# classifier so a reported Anchor-Driven Cycle always backs the verdict.
ANCHOR_ENTROPY_CEIL = 0.5


# --------------------------------------------------------------------------- #
# Enumerations — the closed vocabularies of the domain.
# --------------------------------------------------------------------------- #
class Role(str, Enum):
    """Behavioural roles a position can play (methodology §5)."""

    ANCHOR = "Anchor"
    FRAME = "Frame"
    TRANSITION = "Transition"
    CONTENT_BLOCK = "Content Block"
    TERMINATOR = "Terminator"
    UNASSIGNED = "Unassigned"


class MotifType(str, Enum):
    """Structural motifs (methodology §6)."""

    ANCHOR_DRIVEN_CYCLE = "Anchor-Driven Cycle"
    FLOATING_ANCHOR_DRIFT = "Floating Anchor Drift"
    CLUSTER_BURST = "Cluster Burst"
    MODULAR_BLOCK = "Modular Block"
    BOUNDARY_FRAME = "Boundary Frame"
    TERMINATOR_LOCK = "Terminator Lock"
    ENTROPY_CASCADE = "Entropy Cascade"
    NULL = "Null Motif"
    HYBRID = "Hybrid Motif"


class StructuralClass(str, Enum):
    """Final classification labels (methodology §7)."""

    NATURAL = "Natural"
    ENGINEERED = "Engineered"
    CONSTRUCTED = "Constructed"
    RANDOM = "Random"
    THREE_D_DRIVEN = "3D-Driven"


# --------------------------------------------------------------------------- #
# Stage value objects.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Sequence:
    """Stage 0 — the raw symbolic sequence S = (s1, ..., sn)."""

    symbols: Tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.symbols, tuple):
            object.__setattr__(self, "symbols", tuple(self.symbols))

    @property
    def n(self) -> int:
        return len(self.symbols)

    @property
    def alphabet(self) -> Tuple[str, ...]:
        """Distinct symbols in first-appearance order (stable, deterministic)."""
        seen: Dict[str, None] = {}
        for s in self.symbols:
            seen.setdefault(s, None)
        return tuple(seen.keys())

    @classmethod
    def from_text(cls, text: str, *, sep: Optional[str] = None) -> "Sequence":
        """Parse a string into a Sequence.

        ``sep=None`` splits on whitespace; ``sep=""`` treats each character as a
        symbol; any other separator splits on it.
        """
        if sep is None:
            tokens = text.split()
        elif sep == "":
            tokens = list(text.strip())
        else:
            tokens = [t for t in text.split(sep)]
        return cls(tuple(t for t in tokens if t != ""))


@dataclass(frozen=True)
class SymbolVector:
    """Stage 1 — SV = (f(s1), ..., f(sn)) plus the mapping that produced it."""

    values: Tuple[float, ...]
    mapping: Dict[str, float]
    strategy: str

    @property
    def n(self) -> int:
        return len(self.values)


@dataclass(frozen=True)
class BehaviourVector:
    """Stage 2 — positional behaviour, transitions and local entropy.

    ``positional_weight[i]`` = i/n ; ``entropy[i]`` = entropy of the outgoing
    transition distribution of the symbol at position i ; ``transition_prob`` is
    the normalised symbol-type transition matrix P(a -> b).
    """

    positional_weight: Tuple[float, ...]
    entropy: Tuple[float, ...]
    transition_counts: Dict[str, Dict[str, int]]
    transition_prob: Dict[str, Dict[str, float]]
    symbol_entropy: Dict[str, float]
    max_transition_prob: Dict[str, float]

    @property
    def n(self) -> int:
        return len(self.positional_weight)


@dataclass(frozen=True)
class CohesionVector:
    """Stage 3 — SCV = (C1, ..., Cn), per-position spatial cohesion scores."""

    cohesion: Tuple[float, ...]
    pairs: Tuple[Tuple[int, int, float], ...] = ()

    @property
    def dominant(self) -> bool:
        """True when spatial cohesion carries meaningful signal."""
        return any(c > 0 for c in self.cohesion)


@dataclass(frozen=True)
class RoleAssignment:
    """Stage 4 — per-position roles plus the adaptive thresholds used."""

    roles: Tuple[Role, ...]
    thresholds: Dict[str, float]

    def counts(self) -> Dict[Role, int]:
        out: Dict[Role, int] = {r: 0 for r in Role}
        for r in self.roles:
            out[r] += 1
        return out


@dataclass(frozen=True)
class Motif:
    """A single detected motif with supporting evidence."""

    type: MotifType
    confidence: float
    span: Optional[Tuple[int, int]] = None
    detail: str = ""


@dataclass(frozen=True)
class MotifSet:
    """Stage 5 — all motifs detected in the sequence."""

    motifs: Tuple[Motif, ...]

    def types(self) -> Tuple[MotifType, ...]:
        return tuple(m.type for m in self.motifs)

    def has(self, motif_type: MotifType) -> bool:
        return any(m.type == motif_type for m in self.motifs)


@dataclass(frozen=True)
class Classification:
    """Stage 6 — final class plus the full score vector (argmax is the winner)."""

    label: StructuralClass
    scores: Dict[StructuralClass, float]
    confidence: float


@dataclass(frozen=True)
class AnalysisReport:
    """The complete, serialisable result of one pipeline run."""

    sequence: Sequence
    symbol_vector: SymbolVector
    behaviour_vector: BehaviourVector
    cohesion_vector: CohesionVector
    roles: RoleAssignment
    motifs: MotifSet
    classification: Classification
    meta: Dict[str, object] = field(default_factory=dict)
