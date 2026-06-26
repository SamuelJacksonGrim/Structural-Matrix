"""Command-line front door for the Structural Matrix engine.

Examples::

    python -m structural_matrix --text "A B B C A B C C C A"
    echo "AABAABCCAAB" | python -m structural_matrix --chars
    python -m structural_matrix --text "ACGTACGT" --json
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional, Tuple

from .analyzer import (
    analyze_sequence,
    analyze_windows,
    measure,
    to_json_safe,
)
from .mapping import get_mapper
from .pipeline import StructuralMatrix
from .serialization import report_to_dict
from .significance import structure_significance
from .stability import verdict_stability
from .types import Sequence


def _parse_proximity(spec: Optional[str]) -> Optional[List[Tuple[int, int, float]]]:
    if not spec:
        return None
    triples: List[Tuple[int, int, float]] = []
    for chunk in spec.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        i, j, w = chunk.split(",")
        triples.append((int(i), int(j), float(w)))
    return triples


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="structural_matrix",
        description="Behaviour-first structural analysis of symbolic sequences.",
    )
    src = p.add_mutually_exclusive_group()
    src.add_argument("--text", help="sequence as a string (read stdin if omitted)")
    src.add_argument(
        "--file",
        help="read the sequence from a file (a captured token/ID stream); "
        "the read-only tap for measuring another program's output",
    )
    p.add_argument(
        "--chars",
        action="store_true",
        help="treat each character as a symbol (default: split on whitespace)",
    )
    p.add_argument("--sep", default=None, help="custom token separator")
    p.add_argument(
        "--mapping",
        default="ordinal",
        choices=["ordinal", "frequency"],
        help="symbol-vector mapping strategy",
    )
    p.add_argument(
        "--proximity",
        help='3D proximity triples "i,j,w;i,j,w" (0-based indices)',
    )
    p.add_argument("--json", action="store_true", help="emit JSON output")

    # Output modes (default: the engine report). These compose with the input
    # flags above; --measure folds in the others as opt-in sections.
    mode = p.add_argument_group("output modes")
    mode.add_argument("--spec", action="store_true", help="emit the spec-conformant dict")
    mode.add_argument(
        "--measure",
        action="store_true",
        help="emit the full instrument readout (verdict + opt-in analyses)",
    )
    mode.add_argument("--windows", type=int, metavar="N", help="emit a windowed regime timeline")
    mode.add_argument(
        "--significance",
        type=int,
        metavar="TRIALS",
        help="emit a permutation significance test with TRIALS shuffles",
    )
    mode.add_argument("--stability", action="store_true", help="emit the verdict stability metric")
    return p


def _render_human(report) -> str:
    c = report.classification
    lines = [
        f"Sequence    : {' '.join(report.sequence.symbols)}",
        f"Length n    : {report.sequence.n}   Alphabet: {len(report.sequence.alphabet)}",
        f"Mapping     : {report.symbol_vector.strategy}",
        "",
        f"CLASS       : {c.label.value}   (confidence {c.confidence:.2f})",
        "Scores      : "
        + ", ".join(f"{k.value}={v:.2f}" for k, v in sorted(
            c.scores.items(), key=lambda kv: -kv[1]
        )),
        "",
        "Roles       : "
        + ", ".join(
            f"{r.value}×{n}" for r, n in report.roles.counts().items() if n
        ),
        "Motifs      : "
        + (
            ", ".join(f"{m.type.value}({m.confidence:.2f})" for m in report.motifs.motifs)
            or "none"
        ),
    ]
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    if args.file is not None:
        with open(args.file, "r", encoding="utf-8") as fh:
            raw = fh.read()
    elif args.text is not None:
        raw = args.text
    else:
        raw = sys.stdin.read()
    sep = "" if args.chars else args.sep
    seq = Sequence.from_text(raw, sep=sep)

    # Output modes (precedence: measure > windows > significance > stability > spec
    # > default report). The analysis helpers all emit JSON-able dicts.
    if args.measure:
        out = measure(
            seq,
            significance_trials=args.significance or 0,
            stability=args.stability,
            window=args.windows,
        )
        print(json.dumps(out, indent=2))
        return 0
    if args.windows is not None:
        print(json.dumps(analyze_windows(seq, args.windows), indent=2))
        return 0
    if args.significance is not None:
        print(json.dumps(structure_significance(seq, trials=args.significance), indent=2))
        return 0
    if args.stability:
        print(json.dumps(verdict_stability(seq), indent=2))
        return 0
    if args.spec:
        print(json.dumps(analyze_sequence(seq, json_safe=True), indent=2))
        return 0

    engine = StructuralMatrix(mapper=get_mapper(args.mapping))
    report = engine.analyze(seq, proximity=_parse_proximity(args.proximity))
    if args.json:
        print(json.dumps(report_to_dict(report), indent=2))
    else:
        print(_render_human(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
