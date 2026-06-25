"""Role assignment (methodology §5).

Roles emerge from behaviour, not meaning. Each position is assigned a single
primary role by precedence, using adaptive thresholds derived from the sequence's
own entropy and transition distributions:

    Anchor       H_i < τ_A                  low entropy, stable
    Transition   max_j P(s_i -> s_j) ≥ τ_T  strong directional connector
    Content      H_i > τ_C                  high-entropy cluster
    Frame        boundary position          segments / encloses
    Terminator   H ~ 0 and end-localised    reliable end-marker

Thresholds τ_A, τ_T, τ_C are adaptive (derived per sequence), as required by the
methodology. Precedence resolves positions that satisfy more than one rule.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple

from .types import BehaviourVector, CohesionVector, Role, RoleAssignment, Sequence


def _interp(values: List[float], frac: float) -> float:
    """Linear-interpolated quantile of a sorted-able list (frac in [0, 1])."""
    if not values:
        return 0.0
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    pos = frac * (len(s) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def _occurrence_index(sequence: Sequence) -> Dict[str, List[int]]:
    idx: Dict[str, List[int]] = defaultdict(list)
    for i, s in enumerate(sequence.symbols):
        idx[s].append(i)
    return idx


class StandardRoleAssigner:
    """Default role assigner with adaptive, sequence-derived thresholds."""

    def __init__(self, frame_fraction: float = 0.1):
        # Positions within this fraction of either edge are frame candidates.
        self.frame_fraction = frame_fraction

    def _thresholds(self, bv: BehaviourVector) -> Dict[str, float]:
        ent = list(bv.entropy)
        e_min, e_max = (min(ent), max(ent)) if ent else (0.0, 0.0)
        spread = e_max - e_min

        if spread <= 1e-12:
            # Degenerate: all positions share one entropy value. Bands collapse;
            # nudge so comparisons stay well-defined.
            tau_a = e_min - 1e-9
            tau_c = e_max + 1e-9
        else:
            tau_a = e_min + 0.25 * spread
            tau_c = e_min + 0.75 * spread

        # τ_T: a connector reliably prefers one successor. Adaptive baseline is
        # the mean dominant-transition strength among non-anchor symbols, floored
        # at 0.5 ("more likely than not"), so toy and real sequences both behave.
        non_anchor_mtp = [
            mtp
            for sym, mtp in bv.max_transition_prob.items()
            if bv.symbol_entropy.get(sym, 0.0) > tau_a
        ]
        mean_mtp = sum(non_anchor_mtp) / len(non_anchor_mtp) if non_anchor_mtp else 0.5
        tau_t = max(0.5, mean_mtp)

        return {"tau_A": tau_a, "tau_T": tau_t, "tau_C": tau_c}

    def assign(
        self,
        sequence: Sequence,
        bv: BehaviourVector,
        scv: CohesionVector,
    ) -> RoleAssignment:
        n = sequence.n
        thr = self._thresholds(bv)
        tau_a, tau_t, tau_c = thr["tau_A"], thr["tau_T"], thr["tau_C"]

        occ = _occurrence_index(sequence)
        first_zone = max(1, int(self.frame_fraction * n))
        last_zone = n - first_zone

        # Degenerate case: entropy is uniform, so the bands cannot separate roles.
        # Fall back to structural signals (frequency, clusters, edges) instead of
        # collapsing every position to a single role.
        ent = list(bv.entropy)
        if n >= 2 and (max(ent) - min(ent) if ent else 0.0) <= 1e-12:
            return self._assign_degenerate(sequence, occ, first_zone, last_zone, thr)

        roles: List[Role] = []
        for i, sym in enumerate(sequence.symbols):
            h = bv.entropy[i]
            mtp = bv.max_transition_prob.get(sym, 0.0)

            # 1. Terminator: end-localised, near-zero entropy dedicated marker.
            occs = occ[sym]
            end_localised = occs and min(occs) >= last_zone
            if end_localised and h <= tau_a and i >= last_zone:
                roles.append(Role.TERMINATOR)
                continue

            # 2. Anchor: low entropy, stable.
            if h < tau_a:
                roles.append(Role.ANCHOR)
                continue

            # 3. Transition: dominant directional successor.
            if mtp >= tau_t:
                roles.append(Role.TRANSITION)
                continue

            # 4. Content block: high entropy.
            if h > tau_c:
                roles.append(Role.CONTENT_BLOCK)
                continue

            # 5. Frame: boundary position that is none of the above.
            if i < first_zone or i >= last_zone:
                roles.append(Role.FRAME)
                continue

            roles.append(Role.UNASSIGNED)

        return RoleAssignment(roles=tuple(roles), thresholds=thr)

    def _assign_degenerate(
        self,
        sequence: Sequence,
        occ: Dict[str, List[int]],
        first_zone: int,
        last_zone: int,
        thr: Dict[str, float],
    ) -> RoleAssignment:
        """Role assignment when entropy carries no signal (uniform distribution).

        Precedence: Frame (edges) > Anchor (the dominant recurring symbol) >
        Content (inside a same-symbol cluster) > Transition (everything else).
        """
        syms = sequence.symbols
        n = sequence.n

        # The single most frequent symbol that genuinely recurs is the anchor.
        counts = {s: len(p) for s, p in occ.items()}
        top_count = max(counts.values())
        anchor_syms = (
            {s for s, c in counts.items() if c == top_count} if top_count >= 2 else set()
        )

        # Positions that sit inside a run of length >= 2 (a cluster).
        in_cluster = [False] * n
        run_start = 0
        for i in range(1, n + 1):
            if i == n or syms[i] != syms[run_start]:
                if i - run_start >= 2:
                    for k in range(run_start, i):
                        in_cluster[k] = True
                run_start = i

        roles: List[Role] = []
        for i, sym in enumerate(syms):
            if i < first_zone or i >= last_zone:
                roles.append(Role.FRAME)
            elif sym in anchor_syms:
                roles.append(Role.ANCHOR)
            elif in_cluster[i]:
                roles.append(Role.CONTENT_BLOCK)
            else:
                roles.append(Role.TRANSITION)

        return RoleAssignment(roles=tuple(roles), thresholds=thr)
