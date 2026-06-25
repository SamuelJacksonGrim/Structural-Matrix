# The Autonomous Working Loop

This directory is the engine's **self-driving development harness**. It turns
"build, test, refine" into a repeatable, recorded cycle so progress is auditable
and never depends on remembering what was tried.

## The loop

```
        ┌──────────────────────────────────────────────────────────┐
        │                                                          │
        ▼                                                          │
   ① OBSERVE ──▶ ② HYPOTHESIZE ──▶ ③ IMPLEMENT ──▶ ④ TEST ──▶ ⑤ MARK ──▶ ⑥ REFINE
   run the      predict the next   smallest change  run the    confirmed/  feed the
   gate; read   failure & why      that tests the   gate;      refuted +   surprise
   real output                     hypothesis       add tests  evidence    into ①
```

1. **OBSERVE** — run `python loop/check.py` and read both PASS/FAIL *and* real CLI
   output. Surprises in real output (not just red tests) are first-class signals.
2. **HYPOTHESIZE** — write down what will fail next and *why*, before changing code.
   A hypothesis with a predicted failure mode is falsifiable; a vague intention is not.
3. **IMPLEMENT** — make the smallest change that exercises the hypothesis. No
   drive-by edits — one idea per iteration keeps cause and effect legible.
4. **TEST** — add or adjust tests to capture the new behaviour, then run the gate.
5. **MARK** — record the result in `DEVLOG.md`: hypothesis **confirmed** or
   **refuted**, with the evidence (numbers, before/after). Refuted is not failure;
   it's information.
6. **REFINE** — keep the green, and turn any surprise into the next iteration's
   hypothesis. Durable choices graduate to `docs/09-DECISION-LOG.md`.

## The quality gate — `check.py`

One command, three tiers, short-circuits on a broken build:

| Tier | Checks | Fails the build when… |
|------|--------|-----------------------|
| `IMPORT` | the package imports | a syntax error or import cycle exists |
| `TESTS` | the full `pytest` suite | any unit/integration test fails |
| `INVARIANTS` | behavioural contracts on canonical inputs | a [Contract](../docs/03-CONTRACTS.md) is violated |

Exit code is `0` **iff** every tier is green, so a wrapping loop (CI, a watch
script, or an agent) can branch on success. The invariants tier is the safety net
that catches regressions a narrowly-scoped unit test might miss — e.g. a
classification flip, a collapsed role set, or a dishonest motif.

## The diary — `DEVLOG.md`

Append-only record of every iteration. It is the *why* behind the current state:
read it to understand how the engine got here without re-deriving it. The first
six iterations (baseline build → honest motifs → de-collapsed roles → fuzzing →
architecture proofs) are documented there, ending at **STABLE GREEN** with a
queue of next hypotheses (H5–H7, two already executed).

## Running it

```bash
python loop/check.py        # full gate (import + tests + invariants)
pytest -q                   # tests only, fastest inner loop
python -m structural_matrix --text "…"   # OBSERVE real behaviour
```

## Why a loop instead of a checklist

A checklist assumes you know the failures in advance. This engine's behaviour is
emergent (adaptive thresholds, heuristic scoring), so the *interesting* problems
surface only by running it and being surprised. The loop institutionalises being
surprised: observe → predict → test → record → repeat.
