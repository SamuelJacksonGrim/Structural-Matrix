"""Serialisation helpers — turn an AnalysisReport into plain JSON-able dicts.

Kept separate from :mod:`types` so the value objects stay free of presentation
concerns (dependency rule: types depend on nothing).
"""

from __future__ import annotations

from typing import Any, Dict

from .types import AnalysisReport


def report_to_dict(report: AnalysisReport) -> Dict[str, Any]:
    bv = report.behaviour_vector
    return {
        "sequence": list(report.sequence.symbols),
        "n": report.sequence.n,
        "alphabet": list(report.sequence.alphabet),
        "symbol_vector": {
            "strategy": report.symbol_vector.strategy,
            "mapping": report.symbol_vector.mapping,
            "values": list(report.symbol_vector.values),
        },
        "behaviour": {
            "positional_weight": list(bv.positional_weight),
            "entropy": list(bv.entropy),
            "symbol_entropy": bv.symbol_entropy,
            "transition_prob": bv.transition_prob,
            "max_transition_prob": bv.max_transition_prob,
        },
        "cohesion": {
            "values": list(report.cohesion_vector.cohesion),
            "dominant": report.cohesion_vector.dominant,
        },
        "roles": {
            "per_position": [r.value for r in report.roles.roles],
            "thresholds": report.roles.thresholds,
            "counts": {r.value: c for r, c in report.roles.counts().items() if c},
        },
        "motifs": [
            {
                "type": m.type.value,
                "confidence": round(m.confidence, 4),
                "span": list(m.span) if m.span else None,
                "detail": m.detail,
            }
            for m in report.motifs.motifs
        ],
        "classification": {
            "label": report.classification.label.value,
            "confidence": round(report.classification.confidence, 4),
            "scores": {
                k.value: round(v, 4) for k, v in report.classification.scores.items()
            },
        },
        "meta": report.meta,
    }
