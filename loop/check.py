#!/usr/bin/env python3
"""Autonomous-loop quality gate.

One command that the working loop runs every iteration. It executes three tiers
of checks and prints a structured, machine- and human-readable verdict:

    1. IMPORT   — the package imports cleanly.
    2. TESTS    — the pytest suite passes.
    3. INVARIANTS — behavioural invariants hold on the canonical examples
                    (these are the "contracts" the engine must never break).

Exit code 0 iff every tier passes, so the loop can branch on success/failure.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Callable, List, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, SRC)


def _import_tier() -> Tuple[bool, str]:
    try:
        import structural_matrix  # noqa: F401

        return True, f"structural_matrix {structural_matrix.__version__} imports"
    except Exception as exc:  # pragma: no cover - failure path
        return False, f"import failed: {exc!r}"


def _pytest_cmd() -> List[str]:
    """Prefer ``python -m pytest`` but fall back to a standalone pytest binary
    (e.g. a uv-managed tool install) when the base interpreter lacks pytest."""
    try:
        import pytest  # noqa: F401

        return [sys.executable, "-m", "pytest", "-q"]
    except Exception:
        import shutil

        binary = shutil.which("pytest")
        return [binary, "-q"] if binary else [sys.executable, "-m", "pytest", "-q"]


def _tests_tier() -> Tuple[bool, str]:
    proc = subprocess.run(
        _pytest_cmd(),
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    tail = (proc.stdout or proc.stderr).strip().splitlines()
    summary = tail[-1] if tail else "no output"
    return proc.returncode == 0, summary


def _invariants_tier() -> Tuple[bool, str]:
    from structural_matrix import StructuralMatrix
    from structural_matrix.types import MotifType, StructuralClass

    engine = StructuralMatrix()
    checks: List[Tuple[str, Callable[[], bool]]] = []

    cases = {
        "A B B C A B C C C A": StructuralClass.ENGINEERED,
        "X Y X Z Y X Y Y Z X Y Z": StructuralClass.NATURAL,
        "Q W E R T Y U I O P": StructuralClass.RANDOM,
        "A A B A A B C C A A B": StructuralClass.CONSTRUCTED,
    }
    reports = {t: engine.analyze(t) for t in cases}

    for text, expected in cases.items():
        checks.append(
            (
                f"classify[{expected.value}]",
                lambda r=reports[text], e=expected: r.classification.label == e,
            )
        )

    # Invariant: roles must cover every position.
    for text, r in reports.items():
        checks.append(
            (f"roles_cover[{text[:7]}…]", lambda r=r: len(r.roles.roles) == r.sequence.n)
        )

    # Invariant: determinism.
    a, b = engine.analyze("A B C A B C"), engine.analyze("A B C A B C")
    checks.append(("determinism", lambda: a.classification.scores == b.classification.scores))

    # Invariant: 3D proximity forces 3D class.
    prox = engine.analyze("X Y X Z Y X", proximity=[(0, 5, 9.0), (1, 4, 9.0)])
    checks.append(
        ("3d_override", lambda: prox.classification.label == StructuralClass.THREE_D_DRIVEN)
    )

    # Invariant: a reported Anchor-Driven Cycle must rest on a low-entropy symbol.
    eng = reports["A B B C A B C C C A"]
    def _honest_cycle(r=eng):
        if not r.motifs.has(MotifType.ANCHOR_DRIVEN_CYCLE):
            return True
        return any(v <= 0.5 for v in r.behaviour_vector.symbol_entropy.values())
    checks.append(("honest_anchor_cycle", _honest_cycle))

    failed = [name for name, fn in checks if not fn()]
    ok = not failed
    msg = "all invariants hold" if ok else f"failed: {', '.join(failed)}"
    return ok, f"{len(checks) - len(failed)}/{len(checks)} — {msg}"


def main() -> int:
    tiers = [("IMPORT", _import_tier), ("TESTS", _tests_tier), ("INVARIANTS", _invariants_tier)]
    results = []
    all_ok = True
    for name, fn in tiers:
        ok, detail = fn()
        all_ok = all_ok and ok
        results.append({"tier": name, "ok": ok, "detail": detail})
        flag = "PASS" if ok else "FAIL"
        print(f"[{flag}] {name:<10} {detail}")
        if not ok and name in ("IMPORT", "TESTS"):
            break  # don't run later tiers on a broken build

    print(json.dumps({"ok": all_ok, "tiers": results}))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
