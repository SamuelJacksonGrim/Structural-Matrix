"""Permutation null-model significance.

Is the structure the engine reports *real*, or what you'd expect by chance? This
module answers with a permutation test: shuffle the stream many times (which
preserves symbol frequencies but destroys order/transition/positional structure),
recompute an order-sensitive structuredness scalar each time, and measure how
often chance matches or beats the real stream.

A small p-value ⇒ the observed structure is unlikely under random ordering. This
is the interpretation discipline a fragile regime gauge needs: it refuses to call
noise "structured".
"""

from __future__ import annotations

import random
from typing import Dict, List, Union, Sequence as TSequence

from .classification import compute_features
from .pipeline import StructuralMatrix
from .types import AnalysisReport, Sequence


def _structuredness(report: AnalysisReport) -> float:
    """An order-sensitive scalar in [0, 1]: how much non-random structure is present.

    Built from the order-dependent features only (modular template, clustering,
    anchor cycle, periodicity) — symbol frequency alone cannot move it, which is
    exactly what makes the permutation test meaningful.
    """
    f = compute_features(
        report.sequence,
        report.behaviour_vector,
        report.cohesion_vector,
        report.motifs,
    )
    # `predictability` (mean dominant-transition probability) captures Markov /
    # which-follows-which structure — the signature of natural language and of the
    # Voynich glyph stream. It is order-sensitive (shuffling destroys it), so the
    # permutation test stays valid: a random control's predictability is unchanged
    # by shuffling and reads as non-significant, while real transition structure
    # reads as significant. Without this term the scalar only saw repeated
    # templates / clustering / periodicity and was blind to transition structure.
    return max(
        f.modular_strength,
        f.cluster_strength,
        f.anchor_cycle_conf,
        f.periodic_anchor_strength,
        f.predictability,
    )


def structure_significance(
    sequence: Union[str, TSequence[str]],
    *,
    trials: int = 200,
    seed: int = 0,
) -> Dict[str, object]:
    """Permutation test for structural significance.

    Returns the observed structuredness, the shuffled baseline, and a p-value
    (fraction of shuffles whose structuredness ≥ the observed, with add-one
    smoothing). ``significant`` is True when p < 0.05 *and* the stream actually
    carries structure (observed > 0), so an order-free stream is reported as
    "not significant" rather than spuriously flagged.
    """
    if isinstance(sequence, Sequence):
        seq = sequence
    elif isinstance(sequence, str):
        seq = Sequence.from_text(sequence)
    else:
        seq = Sequence(tuple(str(s) for s in sequence))

    engine = StructuralMatrix()
    observed = _structuredness(engine.analyze(seq))

    rng = random.Random(seed)
    syms = list(seq.symbols)
    baseline: List[float] = []
    ge = 0
    for _ in range(max(1, trials)):
        rng.shuffle(syms)
        sc = _structuredness(engine.analyze(Sequence(tuple(syms))))
        baseline.append(sc)
        if sc >= observed:
            ge += 1

    p_value = (ge + 1) / (trials + 1)
    mean_baseline = sum(baseline) / len(baseline) if baseline else 0.0
    return {
        "observed_structuredness": round(observed, 4),
        "mean_shuffled_structuredness": round(mean_baseline, 4),
        "p_value": round(p_value, 4),
        "trials": trials,
        "significant": bool(p_value < 0.05 and observed > 0.0),
    }
