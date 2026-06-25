"""Structural Matrix — a behaviour-first symbolic structural analysis engine.

Public API::

    from structural_matrix import StructuralMatrix, Sequence

    engine = StructuralMatrix()
    report = engine.analyze("A B B C A B C C C A")
    print(report.classification.label)        # StructuralClass.ENGINEERED

See ``docs/`` for the architecture, flows, contracts and decision log.
"""

from __future__ import annotations

from .pipeline import StructuralMatrix
from .serialization import report_to_dict
from .types import (
    AnalysisReport,
    BehaviourVector,
    Classification,
    CohesionVector,
    Motif,
    MotifSet,
    MotifType,
    Role,
    RoleAssignment,
    Sequence,
    StructuralClass,
    SymbolVector,
)

__version__ = "0.1.0"

__all__ = [
    "StructuralMatrix",
    "report_to_dict",
    "Sequence",
    "SymbolVector",
    "BehaviourVector",
    "CohesionVector",
    "RoleAssignment",
    "Role",
    "Motif",
    "MotifSet",
    "MotifType",
    "Classification",
    "StructuralClass",
    "AnalysisReport",
    "__version__",
]
