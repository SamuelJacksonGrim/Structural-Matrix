"""Motif detection (methodology §6).

Each detector inspects the intermediate state and emits zero or more Motifs with
a confidence in [0, 1]. Detectors are intentionally conservative: it is better to
emit Null than to hallucinate structure, because the classifier trusts motifs.
"""

from __future__ import annotations

from collections import defaultdict
from statistics import mean, pstdev
from typing import Dict, List, Tuple

from .types import (
    ANCHOR_ENTROPY_CEIL,
    BehaviourVector,
    CohesionVector,
    Motif,
    MotifSet,
    MotifType,
    RoleAssignment,
    Role,
    Sequence,
)


def _runs(symbols: Tuple[str, ...]) -> List[Tuple[str, int, int]]:
    """Maximal runs of identical symbols as (symbol, start, length)."""
    out: List[Tuple[str, int, int]] = []
    if not symbols:
        return out
    start = 0
    for i in range(1, len(symbols) + 1):
        if i == len(symbols) or symbols[i] != symbols[start]:
            out.append((symbols[start], start, i - start))
            start = i
    return out


def _repeated_ngrams(symbols: Tuple[str, ...], min_len: int = 2, max_len: int = 5):
    """Return {ngram: [start_indices]} for n-grams occurring 2+ times."""
    n = len(symbols)
    found: Dict[Tuple[str, ...], List[int]] = defaultdict(list)
    for L in range(min_len, min(max_len, n) + 1):
        for i in range(0, n - L + 1):
            found[symbols[i : i + L]].append(i)
    return {g: idx for g, idx in found.items() if len(idx) >= 2}


class StandardMotifDetector:
    """Default motif detector covering all methodology §6 motif types."""

    def __init__(self, cluster_min_run: int = 3):
        self.cluster_min_run = cluster_min_run

    def detect(
        self,
        sequence: Sequence,
        bv: BehaviourVector,
        scv: CohesionVector,
        roles: RoleAssignment,
    ) -> MotifSet:
        syms = sequence.symbols
        n = sequence.n
        motifs: List[Motif] = []
        if n == 0:
            return MotifSet(motifs=(Motif(MotifType.NULL, 1.0, detail="empty"),))

        tau_a = roles.thresholds.get("tau_A", 0.0)
        occ: Dict[str, List[int]] = defaultdict(list)
        for i, s in enumerate(syms):
            occ[s].append(i)

        # Role-level anchors use the adaptive threshold; a *cycle* anchor must be
        # genuinely near-deterministic, so it also respects the absolute ceiling
        # shared with the classifier. This keeps the motif list honest: we never
        # claim an Anchor-Driven Cycle on a merely-frequent, mid-entropy symbol.
        anchors = [s for s in sequence.alphabet if bv.symbol_entropy.get(s, 0.0) < tau_a]
        cycle_anchors = [
            s for s in anchors if bv.symbol_entropy.get(s, 0.0) <= ANCHOR_ENTROPY_CEIL
        ]

        # --- Anchor-Driven Cycle: low-entropy symbol at regular intervals. -----
        for a in cycle_anchors:
            pos = occ[a]
            if len(pos) >= 3:
                gaps = [j - i for i, j in zip(pos, pos[1:])]
                if mean(gaps) > 0:
                    cv = pstdev(gaps) / mean(gaps)
                    if cv <= 0.5:  # gaps are fairly regular
                        motifs.append(
                            Motif(
                                MotifType.ANCHOR_DRIVEN_CYCLE,
                                confidence=max(0.0, 1.0 - cv),
                                detail=f"anchor {a!r} every ~{mean(gaps):.1f}",
                            )
                        )

        # --- Floating Anchor Drift: frequent symbol, irregular spacing. --------
        for s in sequence.alphabet:
            pos = occ[s]
            if len(pos) >= 3 and s not in anchors:
                gaps = [j - i for i, j in zip(pos, pos[1:])]
                if mean(gaps) > 0 and pstdev(gaps) / mean(gaps) > 0.5:
                    freq = len(pos) / n
                    if freq >= 0.25:
                        motifs.append(
                            Motif(
                                MotifType.FLOATING_ANCHOR_DRIFT,
                                confidence=min(1.0, freq * 2),
                                detail=f"{s!r} frequent but irregular",
                            )
                        )

        # --- Cluster Burst: a run of identical symbols of length >= threshold. --
        for sym, start, length in _runs(syms):
            if length >= self.cluster_min_run:
                motifs.append(
                    Motif(
                        MotifType.CLUSTER_BURST,
                        confidence=min(1.0, length / n + 0.3),
                        span=(start, start + length - 1),
                        detail=f"run of {sym!r} x{length}",
                    )
                )

        # --- Modular Block: a multi-symbol template repeated at >=2 locations. --
        ngrams = _repeated_ngrams(syms)
        # Keep the longest, most-repeated non-trivial templates (not single runs).
        best_blocks = sorted(
            (
                (g, idx)
                for g, idx in ngrams.items()
                if len(set(g)) >= 2  # exclude pure runs like ('A','A')
            ),
            key=lambda kv: (len(kv[0]), len(kv[1])),
            reverse=True,
        )
        if best_blocks:
            g, idx = best_blocks[0]
            motifs.append(
                Motif(
                    MotifType.MODULAR_BLOCK,
                    confidence=min(1.0, 0.4 + 0.2 * len(idx)),
                    detail=f"template {''.join(g)} x{len(idx)}",
                )
            )

        # --- Boundary Frame: distinct framing symbols at the two ends. ----------
        if n >= 2 and syms[0] != syms[-1]:
            edge_unique = (len(occ[syms[0]]) <= 2) or (len(occ[syms[-1]]) <= 2)
            if edge_unique:
                motifs.append(
                    Motif(
                        MotifType.BOUNDARY_FRAME,
                        confidence=0.5,
                        span=(0, n - 1),
                        detail=f"{syms[0]!r}...{syms[-1]!r}",
                    )
                )

        # --- Terminator Lock: a low-entropy symbol that ends the sequence. ------
        last = syms[-1]
        if bv.symbol_entropy.get(last, 1.0) <= tau_a and Role.TERMINATOR in roles.roles:
            motifs.append(
                Motif(MotifType.TERMINATOR_LOCK, confidence=0.6, detail=f"ends on {last!r}")
            )

        # --- Entropy Cascade: a long monotonic run in the entropy series. -------
        cascade = self._entropy_cascade(bv.entropy)
        if cascade is not None:
            (a, b, direction) = cascade
            motifs.append(
                Motif(
                    MotifType.ENTROPY_CASCADE,
                    confidence=min(1.0, (b - a + 1) / n),
                    span=(a, b),
                    detail=f"entropy {direction}",
                )
            )

        # --- Entropy Cascade (regime split): first half vs second half (§5.7). --
        split = self._entropy_regime_split(bv.entropy)
        if split is not None:
            rel, direction = split
            motifs.append(
                Motif(
                    MotifType.ENTROPY_CASCADE,
                    confidence=min(1.0, rel),
                    span=(0, n - 1),
                    detail=direction,
                )
            )

        # --- Role-level motifs (spec §5): pattern-match the role string. --------
        # Gate the role-level anchor cycle on a genuine low-entropy anchor so the
        # honest-motif contract (C-8) holds regardless of detection path.
        motifs.extend(
            self._role_level_motifs(
                roles.roles, allow_anchor_cycle=bool(cycle_anchors)
            )
        )

        # Dedupe by type, keeping the highest-confidence evidence for each motif.
        best_by_type: Dict[MotifType, Motif] = {}
        for m in motifs:
            cur = best_by_type.get(m.type)
            if cur is None or m.confidence > cur.confidence:
                best_by_type[m.type] = m
        motifs = list(best_by_type.values())

        # --- Hybrid / Null bookkeeping. ----------------------------------------
        distinct_types = {m.type for m in motifs}
        if len(distinct_types) >= 2:
            motifs.append(
                Motif(
                    MotifType.HYBRID,
                    confidence=min(1.0, 0.3 + 0.15 * len(distinct_types)),
                    detail="+".join(sorted(t.value for t in distinct_types)),
                )
            )
        if not motifs:
            motifs.append(Motif(MotifType.NULL, confidence=1.0, detail="no structure"))

        return MotifSet(motifs=tuple(motifs))

    @staticmethod
    def _role_level_motifs(
        roles: Tuple[Role, ...], *, allow_anchor_cycle: bool = True
    ) -> List[Motif]:
        """Detect motifs as patterns over the role sequence (spec §5).

        Complementary to the symbol/entropy detectors; deduped by the caller.
        """
        out: List[Motif] = []
        n = len(roles)
        if n < 2:
            return out
        seq = [r.value for r in roles]

        # Terminator Lock: CONTENT -> TERMINATOR -> ANCHOR (segment hand-off).
        locks = sum(
            1
            for i in range(n - 2)
            if roles[i] == Role.CONTENT_BLOCK
            and roles[i + 1] == Role.TERMINATOR
            and roles[i + 2] == Role.ANCHOR
        )
        if locks == 0:  # relaxed form: TERMINATOR -> ANCHOR
            locks = sum(
                1
                for i in range(n - 1)
                if roles[i] == Role.TERMINATOR and roles[i + 1] == Role.ANCHOR
            )
        if locks:
            out.append(
                Motif(
                    MotifType.TERMINATOR_LOCK,
                    confidence=min(1.0, 0.5 + 0.2 * locks),
                    detail=f"role hand-off x{locks}",
                )
            )

        # Boundary Frame: FRAME ... (content) ... FRAME enclosing material.
        frame_idx = [i for i, r in enumerate(roles) if r == Role.FRAME]
        if len(frame_idx) >= 2:
            lo, hi = frame_idx[0], frame_idx[-1]
            if any(roles[k] != Role.FRAME for k in range(lo + 1, hi)):
                out.append(
                    Motif(
                        MotifType.BOUNDARY_FRAME,
                        confidence=0.6,
                        span=(lo, hi),
                        detail="frame-enclosed content",
                    )
                )

        # Modular Block: a repeated role n-gram (>=2 long, >=2 distinct roles).
        for L in range(min(5, n), 1, -1):
            seen: Dict[Tuple[str, ...], int] = defaultdict(int)
            for i in range(0, n - L + 1):
                seen[tuple(seq[i : i + L])] += 1
            repeated = [
                (g, c) for g, c in seen.items() if c >= 2 and len(set(g)) >= 2
            ]
            if repeated:
                g, c = max(repeated, key=lambda kv: kv[1])
                out.append(
                    Motif(
                        MotifType.MODULAR_BLOCK,
                        confidence=min(1.0, 0.4 + 0.15 * c),
                        detail=f"role template {'-'.join(g)} x{c}",
                    )
                )
                break

        # Anchor-Driven Cycle: identical role pattern between consecutive anchors.
        anchor_idx = [i for i, r in enumerate(roles) if r == Role.ANCHOR]
        if allow_anchor_cycle and len(anchor_idx) >= 3:
            segments = [
                tuple(seq[a:b]) for a, b in zip(anchor_idx, anchor_idx[1:])
            ]
            counts: Dict[Tuple[str, ...], int] = defaultdict(int)
            for s in segments:
                counts[s] += 1
            top, c = max(counts.items(), key=lambda kv: kv[1])
            if c >= 2:
                out.append(
                    Motif(
                        MotifType.ANCHOR_DRIVEN_CYCLE,
                        confidence=min(1.0, 0.5 + 0.15 * c),
                        detail=f"inter-anchor cycle x{c}",
                    )
                )
        return out

    @staticmethod
    def _entropy_regime_split(entropy: Tuple[float, ...], threshold: float = 0.35):
        """Compare mean entropy of the two halves (spec §5.7).

        Returns ``(rel_diff, direction)`` when the halves differ by at least
        ``threshold`` (relative), else None. Requires n >= 6 so a worked example
        (n = 10–12) needs a *strong* shift to register — guarding against spurious
        cascades on short, stationary sequences.
        """
        n = len(entropy)
        if n < 6:
            return None
        mid = n // 2
        first = sum(entropy[:mid]) / mid
        second = sum(entropy[mid:]) / (n - mid)
        hi = max(first, second)
        if hi <= 1e-9:
            return None
        rel = (hi - min(first, second)) / hi
        if rel >= threshold:
            return rel, ("structure->noise" if second > first else "noise->structure")
        return None

    @staticmethod
    def _entropy_cascade(entropy: Tuple[float, ...]):
        """Longest strictly monotonic run; require length >= 4 to count."""
        if len(entropy) < 4:
            return None
        best = (0, 0, "flat")
        for direction, cmp in (("rising", lambda a, b: b > a), ("falling", lambda a, b: b < a)):
            start = 0
            for i in range(1, len(entropy)):
                if not cmp(entropy[i - 1], entropy[i]):
                    if i - 1 - start > best[1] - best[0]:
                        best = (start, i - 1, direction)
                    start = i
            if len(entropy) - 1 - start > best[1] - best[0]:
                best = (start, len(entropy) - 1, direction)
        if best[1] - best[0] + 1 >= 4:
            return best
        return None
