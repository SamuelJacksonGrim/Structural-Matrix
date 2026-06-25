"""Spatial Cohesion Vector construction (methodology §4).

For an optional 3D proximity set P = { (i, j, w_ij) }:

    SCV_ij = w_ij
    C_i    = Σ_j w_ij           (total cohesion incident on position i)
    SCV    = (C_1, ..., C_n)

When no proximity data is supplied the cohesion vector is all zeros, signalling
a purely symbolic (non-spatial) analysis.
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

from .types import CohesionVector, Sequence

ProximityTriple = Tuple[int, int, float]


class StandardCohesionAnalyzer:
    """Default Spatial Cohesion Vector implementation."""

    def analyze(
        self,
        sequence: Sequence,
        proximity: Optional[Iterable[ProximityTriple]],
    ) -> CohesionVector:
        n = sequence.n
        cohesion: List[float] = [0.0] * n
        pairs: List[ProximityTriple] = []

        if proximity:
            for i, j, w in proximity:
                if not (0 <= i < n and 0 <= j < n):
                    raise IndexError(
                        f"proximity index out of range for n={n}: ({i}, {j})"
                    )
                if w < 0:
                    raise ValueError(f"cohesion weight must be >= 0, got {w}")
                cohesion[i] += w
                cohesion[j] += w  # undirected contact: both endpoints gain.
                pairs.append((i, j, float(w)))

        return CohesionVector(cohesion=tuple(cohesion), pairs=tuple(pairs))
