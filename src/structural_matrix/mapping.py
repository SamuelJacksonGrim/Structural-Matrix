"""Symbol Vector construction — f : Σ -> ℝ (methodology §2).

The Structural Matrix is mapping-agnostic. Each strategy here is a SymbolMapper.
All mappings are deterministic given a fixed alphabet ordering.
"""

from __future__ import annotations

from collections import Counter
from typing import Callable, Dict

from .types import Sequence, SymbolVector


class OrdinalMapper:
    """Assign 1, 2, 3, ... in first-appearance order. Deterministic, stable."""

    name = "ordinal"

    def map(self, sequence: Sequence) -> SymbolVector:
        mapping: Dict[str, float] = {
            sym: float(i + 1) for i, sym in enumerate(sequence.alphabet)
        }
        values = tuple(mapping[s] for s in sequence.symbols)
        return SymbolVector(values=values, mapping=mapping, strategy=self.name)


class FrequencyMapper:
    """Map each symbol to its frequency rank (most frequent -> 1).

    Ties are broken by first-appearance order to remain deterministic.
    """

    name = "frequency"

    def map(self, sequence: Sequence) -> SymbolVector:
        counts = Counter(sequence.symbols)
        order = {sym: i for i, sym in enumerate(sequence.alphabet)}
        ranked = sorted(
            sequence.alphabet, key=lambda s: (-counts[s], order[s])
        )
        mapping: Dict[str, float] = {
            sym: float(rank + 1) for rank, sym in enumerate(ranked)
        }
        values = tuple(mapping[s] for s in sequence.symbols)
        return SymbolVector(values=values, mapping=mapping, strategy=self.name)


class CustomMapper:
    """Use a caller-provided dict. Unknown symbols fall back to ordinal position."""

    name = "custom"

    def __init__(self, mapping: Dict[str, float]):
        self._base = dict(mapping)

    def map(self, sequence: Sequence) -> SymbolVector:
        mapping = dict(self._base)
        next_val = (max(mapping.values()) + 1.0) if mapping else 1.0
        for sym in sequence.alphabet:
            if sym not in mapping:
                mapping[sym] = next_val
                next_val += 1.0
        values = tuple(mapping[s] for s in sequence.symbols)
        return SymbolVector(values=values, mapping=mapping, strategy=self.name)


class CallableMapper:
    """Wrap an arbitrary f : str -> float as a SymbolMapper."""

    name = "callable"

    def __init__(self, fn: Callable[[str], float], name: str = "callable"):
        self._fn = fn
        self.name = name

    def map(self, sequence: Sequence) -> SymbolVector:
        mapping: Dict[str, float] = {s: float(self._fn(s)) for s in sequence.alphabet}
        values = tuple(mapping[s] for s in sequence.symbols)
        return SymbolVector(values=values, mapping=mapping, strategy=self.name)


_REGISTRY = {
    "ordinal": OrdinalMapper,
    "frequency": FrequencyMapper,
}


def get_mapper(strategy: str = "ordinal"):
    """Factory for the built-in, zero-argument mappers."""
    try:
        return _REGISTRY[strategy]()
    except KeyError:
        raise ValueError(
            f"Unknown mapping strategy {strategy!r}; "
            f"available: {sorted(_REGISTRY)}"
        ) from None
