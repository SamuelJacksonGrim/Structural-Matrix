"""Verdict stability — how robust is the classification?

A regime gauge is only trustworthy if its verdict does not hinge on a single
token or a hair-thin score margin. This module reports both:

  * **score margin** — the gap between the top and runner-up class scores.
  * **jackknife stability** — drop one token at a time and measure the fraction of
    perturbations that keep the same label (sampled on long streams).

Together they label a verdict ``robust`` / ``marginal`` / ``fragile`` — the
honest counterweight to a confident-looking but brittle classification.
"""

from __future__ import annotations

import random
from typing import Dict, Union, Sequence as TSequence

from .pipeline import StructuralMatrix
from .types import Sequence


def verdict_stability(
    sequence: Union[str, TSequence[str]],
    *,
    max_perturbations: int = 50,
    seed: int = 0,
) -> Dict[str, object]:
    """Assess how robust the classification is to small perturbations."""
    if isinstance(sequence, Sequence):
        seq = sequence
    elif isinstance(sequence, str):
        seq = Sequence.from_text(sequence)
    else:
        seq = Sequence(tuple(str(s) for s in sequence))

    engine = StructuralMatrix()
    report = engine.analyze(seq)
    top = report.classification.label
    ranked = sorted(report.classification.scores.values(), reverse=True)
    margin = (ranked[0] - ranked[1]) if len(ranked) > 1 else ranked[0]

    n = seq.n
    if n <= 2:
        jackknife = 1.0
        sampled = 0
    else:
        idxs = list(range(n))
        rng = random.Random(seed)
        rng.shuffle(idxs)
        sample = idxs[:max_perturbations]
        same = 0
        for i in sample:
            perturbed = seq.symbols[:i] + seq.symbols[i + 1 :]
            if engine.analyze(Sequence(perturbed)).classification.label == top:
                same += 1
        sampled = len(sample)
        jackknife = same / sampled if sampled else 1.0

    if margin >= 0.5 and jackknife >= 0.9:
        label = "robust"
    elif margin < 0.15 or jackknife < 0.6:
        label = "fragile"
    else:
        label = "marginal"

    return {
        "classification": top.name,
        "score_margin": round(margin, 4),
        "jackknife_stability": round(jackknife, 4),
        "perturbations_tested": sampled,
        "stability": label,
    }
