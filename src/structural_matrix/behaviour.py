"""Behaviour Vector construction (methodology §3).

Captures positional behaviour, symbol-type transitions and local entropy:

    pw_i          = i / n                          (positional weight)
    T(a, b)       = count of transitions a -> b
    P(a -> b)     = T(a, b) / Σ_k T(a, k)          (normalised)
    H(a)          = -Σ_b P(a -> b) log2 P(a -> b)  (outgoing entropy of symbol a)
    entropy[i]    = H(symbol at position i)

Entropy is computed per symbol *type* (over its outgoing transition
distribution) and projected back onto positions. Using log base 2 gives entropy
in bits, which keeps thresholds interpretable.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Dict

from .types import BehaviourVector, Sequence, SymbolVector


def _positional_weights(n: int) -> tuple:
    if n == 0:
        return ()
    # i in 1..n  ->  i/n  (so the first position is 1/n, the last is 1.0).
    return tuple((i + 1) / n for i in range(n))


def _transition_counts(sequence: Sequence) -> Dict[str, Dict[str, int]]:
    counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    syms = sequence.symbols
    for a, b in zip(syms, syms[1:]):
        counts[a][b] += 1
    # Freeze into plain dicts for a clean, hashable-friendly structure.
    return {a: dict(row) for a, row in counts.items()}


def _normalise(counts: Dict[str, Dict[str, int]]) -> Dict[str, Dict[str, float]]:
    prob: Dict[str, Dict[str, float]] = {}
    for a, row in counts.items():
        total = sum(row.values())
        if total == 0:
            prob[a] = {}
        else:
            prob[a] = {b: c / total for b, c in row.items()}
    return prob


def _entropy(dist: Dict[str, float]) -> float:
    h = 0.0
    for p in dist.values():
        if p > 0.0:
            h -= p * math.log2(p)
    return h


class StandardBehaviourAnalyzer:
    """Default Behaviour Vector implementation."""

    def analyze(self, sequence: Sequence, sv: SymbolVector) -> BehaviourVector:
        n = sequence.n
        pw = _positional_weights(n)
        counts = _transition_counts(sequence)
        prob = _normalise(counts)

        symbol_entropy: Dict[str, float] = {
            sym: _entropy(prob.get(sym, {})) for sym in sequence.alphabet
        }
        max_tp: Dict[str, float] = {
            sym: (max(prob[sym].values()) if prob.get(sym) else 0.0)
            for sym in sequence.alphabet
        }

        entropy = tuple(symbol_entropy.get(s, 0.0) for s in sequence.symbols)

        return BehaviourVector(
            positional_weight=pw,
            entropy=entropy,
            transition_counts=counts,
            transition_prob=prob,
            symbol_entropy=symbol_entropy,
            max_transition_prob=max_tp,
        )
