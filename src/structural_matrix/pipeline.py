"""The pipeline orchestrator (methodology §8).

    S -> SV -> BV -> SCV -> Roles -> Motifs -> Classification

The orchestrator owns no analysis logic of its own — it only wires the stages
together. Every stage is an injectable interface, so any implementation can be
swapped without touching this file. Deterministic given a fixed mapping.
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

from .behaviour import StandardBehaviourAnalyzer
from .classification import StandardClassifier
from .cohesion import StandardCohesionAnalyzer
from .interfaces import (
    BehaviourAnalyzer,
    Classifier,
    CohesionAnalyzer,
    MotifDetector,
    RoleAssigner,
    SymbolMapper,
)
from .mapping import OrdinalMapper
from .motifs import StandardMotifDetector
from .roles import StandardRoleAssigner
from .types import AnalysisReport, Sequence


class StructuralMatrix:
    """End-to-end engine. Construct once, call :meth:`analyze` many times."""

    def __init__(
        self,
        mapper: Optional[SymbolMapper] = None,
        behaviour: Optional[BehaviourAnalyzer] = None,
        cohesion: Optional[CohesionAnalyzer] = None,
        role_assigner: Optional[RoleAssigner] = None,
        motif_detector: Optional[MotifDetector] = None,
        classifier: Optional[Classifier] = None,
    ):
        self.mapper = mapper or OrdinalMapper()
        self.behaviour = behaviour or StandardBehaviourAnalyzer()
        self.cohesion = cohesion or StandardCohesionAnalyzer()
        self.role_assigner = role_assigner or StandardRoleAssigner()
        self.motif_detector = motif_detector or StandardMotifDetector()
        self.classifier = classifier or StandardClassifier()

    def analyze(
        self,
        sequence: Sequence | str | Iterable[str],
        proximity: Optional[List[Tuple[int, int, float]]] = None,
    ) -> AnalysisReport:
        seq = self._coerce(sequence)

        sv = self.mapper.map(seq)
        bv = self.behaviour.analyze(seq, sv)
        scv = self.cohesion.analyze(seq, proximity)
        roles = self.role_assigner.assign(seq, bv, scv)
        motifs = self.motif_detector.detect(seq, bv, scv, roles)
        classification = self.classifier.classify(seq, bv, scv, roles, motifs)

        return AnalysisReport(
            sequence=seq,
            symbol_vector=sv,
            behaviour_vector=bv,
            cohesion_vector=scv,
            roles=roles,
            motifs=motifs,
            classification=classification,
            meta={
                "mapping_strategy": sv.strategy,
                "n": seq.n,
                "alphabet_size": len(seq.alphabet),
            },
        )

    @staticmethod
    def _coerce(sequence: Sequence | str | Iterable[str]) -> Sequence:
        if isinstance(sequence, Sequence):
            return sequence
        if isinstance(sequence, str):
            return Sequence.from_text(sequence)
        return Sequence(tuple(str(s) for s in sequence))
