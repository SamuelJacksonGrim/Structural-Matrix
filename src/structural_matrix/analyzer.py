"""Spec-conformant facade — `analyze_sequence` and `StructuralMatrixAnalyzer`.

`docs/DEVELOPER_SPEC.md` pins an exact public API and output dict. This module
satisfies it *additively*: it reshapes an `AnalysisReport` from the core engine
into the specified contract. It owns **no analysis logic** — every number here is
derived from the engine's output, so the two can never disagree.

    from structural_matrix import analyze_sequence
    result = analyze_sequence("A B B C A B C C C A")
    result["classification"]            # -> "ENGINEERED"
    result["roles"]                     # -> {"A": "ANCHOR", "B": "TRANSITION", ...}
    result["transitions"]               # -> {("ANCHOR","TRANSITION"): 3, ...}

The engine is a **universal instrument**: it consumes any symbol stream and never
adapts to a particular source. To measure another program (e.g. a captured stream
of token IDs), feed that stream straight in — no coupling required.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Dict, List, Sequence as TSequence, Tuple, Union

from .pipeline import StructuralMatrix
from .types import AnalysisReport, Role, Sequence

# Map the engine's richer role vocabulary onto the spec's five role names.
# CONTENT_BLOCK -> CONTENT; UNASSIGNED is kept verbatim (honest: it means "no
# dominant behaviour"), since collapsing it would invent a role the data lacks.
_ROLE_TO_SPEC: Dict[Role, str] = {
    Role.ANCHOR: "ANCHOR",
    Role.FRAME: "FRAME",
    Role.TRANSITION: "TRANSITION",
    Role.CONTENT_BLOCK: "CONTENT",
    Role.TERMINATOR: "TERMINATOR",
    Role.UNASSIGNED: "UNASSIGNED",
}


def _shannon(counts: TSequence[int]) -> float:
    """Shannon entropy (bits) of a multiset given its raw counts."""
    total = sum(counts)
    if total <= 0:
        return 0.0
    h = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            h -= p * math.log2(p)
    return h


class StructuralMatrixAnalyzer:
    """Spec-shaped wrapper around the core :class:`StructuralMatrix` engine.

    Mirrors the method layout suggested in the spec while delegating all real
    work to the validated pipeline.
    """

    def __init__(self, sequence: Union[str, TSequence[str]]):
        self.raw_sequence = sequence
        self._engine = StructuralMatrix()
        self._report: AnalysisReport | None = None

    # -- pipeline (delegates to the engine in one shot) --------------------- #
    def analyze(self) -> Dict[str, object]:
        seq = self._coerce(self.raw_sequence)
        self._report = self._engine.analyze(seq)
        return self._build_result(self._report)

    # -- result shaping ----------------------------------------------------- #
    def _build_result(self, report: AnalysisReport) -> Dict[str, object]:
        symbols = list(report.sequence.symbols)
        role_sequence = [_ROLE_TO_SPEC[r] for r in report.roles.roles]

        return {
            "symbols": symbols,
            "mapping": {k: int(v) for k, v in report.symbol_vector.mapping.items()},
            "numeric_sequence": [int(v) for v in report.symbol_vector.values],
            "roles": self._symbol_roles(symbols, report.roles.roles),
            "role_sequence": role_sequence,
            "transitions": self._role_transitions(report.roles.roles),
            "motifs": [m.type.value for m in report.motifs.motifs],
            "entropy": {
                "symbol_entropy": self._symbol_entropy(symbols),
                "transition_entropy": self._transition_entropy(report.roles.roles),
                "cluster_stats": self._cluster_stats(symbols),
            },
            "classification": report.classification.label.name,  # UPPERCASE
        }

    @staticmethod
    def _symbol_roles(
        symbols: List[str], roles: Tuple[Role, ...]
    ) -> Dict[str, str]:
        """Aggregate per-position roles into one role per symbol.

        Spec §3.2: when a symbol plays several roles across positions, pick the
        dominant behaviour (most frequent role). Ties break by first appearance.
        """
        per_symbol: Dict[str, Counter] = defaultdict(Counter)
        for sym, role in zip(symbols, roles):
            per_symbol[sym][role] += 1
        out: Dict[str, str] = {}
        for sym in dict.fromkeys(symbols):  # first-appearance order
            dominant = max(per_symbol[sym].items(), key=lambda kv: kv[1])[0]
            out[sym] = _ROLE_TO_SPEC[dominant]
        return out

    @staticmethod
    def _role_transitions(roles: Tuple[Role, ...]) -> Dict[Tuple[str, str], int]:
        counts: Dict[Tuple[str, str], int] = defaultdict(int)
        spec_roles = [_ROLE_TO_SPEC[r] for r in roles]
        for a, b in zip(spec_roles, spec_roles[1:]):
            counts[(a, b)] += 1
        return dict(counts)

    @staticmethod
    def _symbol_entropy(symbols: List[str]) -> float:
        return _shannon(list(Counter(symbols).values()))

    @classmethod
    def _transition_entropy(cls, roles: Tuple[Role, ...]) -> float:
        trans = cls._role_transitions(roles)
        return _shannon(list(trans.values()))

    @staticmethod
    def _cluster_stats(symbols: List[str]) -> Dict[str, object]:
        """Runs of identical symbols (spec §4.1)."""
        runs: List[Tuple[str, int]] = []
        if symbols:
            start = 0
            for i in range(1, len(symbols) + 1):
                if i == len(symbols) or symbols[i] != symbols[start]:
                    runs.append((symbols[start], i - start))
                    start = i
        clusters = [(s, length) for s, length in runs if length >= 2]
        lengths = [length for _, length in clusters]
        dominant = Counter(s for s, _ in clusters)
        return {
            "cluster_count": len(clusters),
            "avg_cluster_length": (sum(lengths) / len(lengths)) if lengths else 0.0,
            "max_cluster_length": max(lengths) if lengths else 0,
            "dominant_symbols": [s for s, _ in dominant.most_common()],
        }

    @staticmethod
    def _coerce(sequence: Union[str, TSequence[str]]) -> Sequence:
        if isinstance(sequence, Sequence):
            return sequence
        if isinstance(sequence, str):
            return Sequence.from_text(sequence)
        return Sequence(tuple(str(s) for s in sequence))


def analyze_sequence(sequence: Union[str, TSequence[str]]) -> Dict[str, object]:
    """Spec entry point: analyse a symbolic sequence, return the structured dict."""
    return StructuralMatrixAnalyzer(sequence).analyze()


def analyze_file(path: str, *, sep: str | None = None) -> Dict[str, object]:
    """Read a captured token stream from ``path`` and analyse it.

    This is the **read-only tap** for pointing the instrument at another program's
    output (e.g. a logged stream of stable/token IDs). It does not couple to any
    source — it just reads tokens. ``sep=None`` splits on any whitespace/newlines
    (so one-token-per-line or space-separated logs both work); ``sep=""`` treats
    each character as a token; any other value splits on that delimiter.
    """
    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read()
    seq = Sequence.from_text(raw, sep=sep)
    return StructuralMatrixAnalyzer(seq).analyze()
