"""Structural Matrix — Interfaces (the plug sockets).

Each stage of the pipeline is defined here as a Protocol so any concrete
implementation can be swapped out without touching the orchestrator. This is the
seam that lets the engine stay open for extension but closed for modification.
"""

from __future__ import annotations

from typing import Dict, Optional, Protocol, runtime_checkable

from .types import (
    BehaviourVector,
    Classification,
    CohesionVector,
    MotifSet,
    RoleAssignment,
    Sequence,
    SymbolVector,
)


@runtime_checkable
class SymbolMapper(Protocol):
    """f : Σ -> ℝ.  Turns a Sequence into a SymbolVector."""

    name: str

    def map(self, sequence: Sequence) -> SymbolVector: ...


@runtime_checkable
class BehaviourAnalyzer(Protocol):
    """Produces the Behaviour Vector (positional weight, transitions, entropy)."""

    def analyze(self, sequence: Sequence, sv: SymbolVector) -> BehaviourVector: ...


@runtime_checkable
class CohesionAnalyzer(Protocol):
    """Produces the Spatial Cohesion Vector from an optional proximity set."""

    def analyze(self, sequence: Sequence, proximity: Optional[list]) -> CohesionVector: ...


@runtime_checkable
class RoleAssigner(Protocol):
    """Assigns behavioural roles from BV + SCV using adaptive thresholds."""

    def assign(
        self,
        sequence: Sequence,
        bv: BehaviourVector,
        scv: CohesionVector,
    ) -> RoleAssignment: ...


@runtime_checkable
class MotifDetector(Protocol):
    """Detects structural motifs from the full intermediate state."""

    def detect(
        self,
        sequence: Sequence,
        bv: BehaviourVector,
        scv: CohesionVector,
        roles: RoleAssignment,
    ) -> MotifSet: ...


@runtime_checkable
class Classifier(Protocol):
    """Assigns the final structural class via argmax over a score vector."""

    def classify(
        self,
        sequence: Sequence,
        bv: BehaviourVector,
        scv: CohesionVector,
        roles: RoleAssignment,
        motifs: MotifSet,
    ) -> Classification: ...
