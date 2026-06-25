"""Classification (methodology §7).

The final class is the argmax over a transparent score vector. Each class score is
a linear combination of behaviour-derived features in [0, 1], so the verdict is
explainable: callers can read ``Classification.scores`` to see why.

Discriminators (validated against the methodology's four worked examples):

    Random      symbols barely reuse (high distinct ratio), no repeated structure
    Engineered  a near-deterministic anchor recurs at regular intervals (a cycle)
    Constructed a multi-symbol template tiles much of the sequence (modular block)
    Natural     symbols reuse with moderate/high entropy but no cycle or template
    3D-Driven   spatial cohesion dominates the symbolic signal
"""

from __future__ import annotations

import math
from collections import defaultdict
from statistics import pstdev
from typing import Dict, List, Tuple

from .types import (
    ANCHOR_ENTROPY_CEIL,
    BehaviourVector,
    Classification,
    CohesionVector,
    MotifSet,
    MotifType,
    RoleAssignment,
    Sequence,
    StructuralClass,
)


class Features:
    """Computed, inspectable feature signals in [0, 1] (mostly)."""

    __slots__ = (
        "distinct_ratio",
        "reuse",
        "mean_entropy_norm",
        "entropy_var_norm",
        "predictability",
        "anchor_cycle_conf",
        "periodic_anchor_strength",
        "modular_strength",
        "cluster_strength",
        "scv_signal",
    )

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k, 0.0))

    def as_dict(self) -> Dict[str, float]:
        return {k: getattr(self, k) for k in self.__slots__}


def _occ(symbols) -> Dict[str, List[int]]:
    d: Dict[str, List[int]] = defaultdict(list)
    for i, s in enumerate(symbols):
        d[s].append(i)
    return d


def _best_template_coverage(symbols: Tuple[str, ...]) -> Tuple[float, int]:
    """Best repeated multi-symbol template: (coverage_fraction, template_len).

    Coverage is the fraction of positions covered by all occurrences of the
    strongest repeated n-gram (length >= 2, at least two distinct symbols).
    """
    n = len(symbols)
    if n < 4:
        return 0.0, 0
    best_cov, best_len = 0.0, 0
    for L in range(2, min(6, n) + 1):
        seen: Dict[Tuple[str, ...], List[int]] = defaultdict(list)
        for i in range(0, n - L + 1):
            seen[symbols[i : i + L]].append(i)
        for gram, starts in seen.items():
            if len(starts) < 2 or len(set(gram)) < 2:
                continue
            covered = set()
            for s in starts:
                covered.update(range(s, s + L))
            cov = len(covered) / n
            # Prefer longer templates; break ties by coverage.
            if (L, cov) > (best_len, best_cov):
                best_cov, best_len = cov, L
    return best_cov, best_len


def compute_features(
    sequence: Sequence,
    bv: BehaviourVector,
    scv: CohesionVector,
    motifs: MotifSet,
) -> Features:
    n = max(1, sequence.n)
    alphabet = sequence.alphabet
    occ = _occ(sequence.symbols)

    distinct_ratio = len(alphabet) / n
    reuse = 1.0 - distinct_ratio

    max_possible = math.log2(len(alphabet)) if len(alphabet) > 1 else 1.0
    mean_entropy = sum(bv.entropy) / n if bv.entropy else 0.0
    mean_entropy_norm = min(1.0, mean_entropy / max_possible) if max_possible else 0.0
    ent_std = pstdev(bv.entropy) if len(bv.entropy) > 1 else 0.0
    entropy_var_norm = min(1.0, ent_std / max_possible) if max_possible else 0.0

    mtp = list(bv.max_transition_prob.values())
    predictability = (sum(mtp) / len(mtp)) if mtp else 0.0

    # Engineered anchor cycle: near-deterministic symbol at regular intervals.
    anchor_cycle_conf = 0.0
    for s in alphabet:
        if bv.symbol_entropy.get(s, 1.0) <= ANCHOR_ENTROPY_CEIL and len(occ[s]) >= 3:
            gaps = [b - a for a, b in zip(occ[s], occ[s][1:])]
            m = sum(gaps) / len(gaps)
            if m > 0:
                cv = pstdev(gaps) / m
                if cv <= 0.5:
                    anchor_cycle_conf = max(anchor_cycle_conf, 1.0 - cv)

    # Periodic anchor: a symbol that recurs at a near-constant interval is
    # structure even when its successors churn (high transition entropy). The
    # transition-determinism anchor above misses this; periodicity catches it.
    # Gated strictly (CV/0.3) so a regular beat counts but a drifting/floating
    # anchor (irregular spacing) does not.
    periodic_anchor_strength = 0.0
    if n > 1:
        for s in alphabet:
            pos = occ[s]
            if len(pos) >= 3:
                gaps = [b - a for a, b in zip(pos, pos[1:])]
                m = sum(gaps) / len(gaps)
                if m > 0:
                    cv = pstdev(gaps) / m
                    regularity = max(0.0, 1.0 - cv / 0.3)
                    span = (pos[-1] - pos[0]) / (n - 1)
                    periodic_anchor_strength = max(
                        periodic_anchor_strength, regularity * span
                    )

    cov, tlen = _best_template_coverage(sequence.symbols)
    modular_strength = cov * (1.0 if tlen >= 3 else 0.4)

    # Cluster strength: positions inside identical runs of length >= 3.
    cluster_positions = 0
    run_start = 0
    syms = sequence.symbols
    for i in range(1, n + 1):
        if i == n or syms[i] != syms[run_start]:
            if i - run_start >= 3:
                cluster_positions += i - run_start
            run_start = i
    cluster_strength = cluster_positions / n

    total_cohesion = sum(scv.cohesion)
    scv_signal = 1.0 if (scv.dominant and total_cohesion > 0) else 0.0

    return Features(
        distinct_ratio=distinct_ratio,
        reuse=reuse,
        mean_entropy_norm=mean_entropy_norm,
        entropy_var_norm=entropy_var_norm,
        predictability=predictability,
        anchor_cycle_conf=anchor_cycle_conf,
        periodic_anchor_strength=periodic_anchor_strength,
        modular_strength=modular_strength,
        cluster_strength=cluster_strength,
        scv_signal=scv_signal,
    )


class StandardClassifier:
    """Default classifier: linear scoring + argmax (methodology §7)."""

    def classify(
        self,
        sequence: Sequence,
        bv: BehaviourVector,
        scv: CohesionVector,
        roles: RoleAssignment,
        motifs: MotifSet,
    ) -> Classification:
        f = compute_features(sequence, bv, scv, motifs)
        structure = max(
            f.modular_strength,
            f.cluster_strength,
            f.anchor_cycle_conf,
            f.periodic_anchor_strength,
        )

        scores: Dict[StructuralClass, float] = {
            StructuralClass.RANDOM: 1.5 * f.distinct_ratio - structure,
            StructuralClass.ENGINEERED: (
                1.2 * f.anchor_cycle_conf
                + 0.8 * f.periodic_anchor_strength
                + 0.6 * (f.predictability * f.reuse)
                + 0.3 * f.cluster_strength
            ),
            StructuralClass.CONSTRUCTED: (
                1.3 * f.modular_strength
                + 0.4 * f.reuse
                + 0.4 * (1.0 - f.entropy_var_norm)
                - 0.7 * f.anchor_cycle_conf
            ),
            StructuralClass.NATURAL: (
                1.0 * f.mean_entropy_norm
                + 0.5 * f.reuse
                - 0.8 * f.modular_strength
                - 0.5 * f.anchor_cycle_conf
            ),
            StructuralClass.THREE_D_DRIVEN: 2.0 * f.scv_signal,
        }

        label = max(scores, key=scores.get)
        confidence = self._confidence(scores, label)
        return Classification(label=label, scores=scores, confidence=confidence)

    @staticmethod
    def _confidence(scores: Dict[StructuralClass, float], label: StructuralClass) -> float:
        """Softmax probability of the winning class (margin-sensitive in [0, 1])."""
        vals = list(scores.values())
        m = max(vals)
        exps = {k: math.exp(v - m) for k, v in scores.items()}
        total = sum(exps.values())
        return exps[label] / total if total else 0.0
