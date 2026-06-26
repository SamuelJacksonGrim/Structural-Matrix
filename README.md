# Structural Matrix

> A behaviour-first engine that extracts **universal structure** from symbolic
> systems — by ignoring meaning and measuring how symbols *behave*.

The Structural Matrix reads any sequence of symbols (DNA, a conlang, a cipher, an
AI-generated script, abstract tokens) and reports the **structural class** it
belongs to — `Natural`, `Engineered`, `Constructed`, `Random`, or `3D-Driven` —
together with the roles, motifs, entropy and transition behaviour that justify the
verdict. It treats all information as mechanical structure.

```text
   S ──▶ SV ──▶ BV ──▶ SCV ──▶ Roles ──▶ Motifs ──▶ Classification
 symbols  map  behaviour spatial  roles    motifs      the verdict
```

## Quick start

```bash
# No dependencies — pure Python standard library (3.9+).
python -m structural_matrix --text "A B B C A B C C C A"
```

```text
CLASS       : Engineered   (confidence 0.52)
Scores      : Engineered=1.46, Natural=0.20, Constructed=0.15, 3D-Driven=0.00, Random=-0.44
Roles       : Anchor×3, Transition×3, Content Block×4
Motifs      : Anchor-Driven Cycle(0.89), Cluster Burst(0.60), Modular Block(0.80), Hybrid Motif(0.90)
```

As a library:

```python
from structural_matrix import StructuralMatrix

engine = StructuralMatrix()
report = engine.analyze("A A B A A B C C A A B")
print(report.classification.label)          # StructuralClass.CONSTRUCTED
print(report.classification.scores)          # full, inspectable score vector
```

Or via the spec-conformant facade (`docs/DEVELOPER_SPEC.md`), which returns a
plain dict — symbol→role, role-level transition matrix, scalar entropies and an
UPPERCASE class label:

```python
from structural_matrix import analyze_sequence
result = analyze_sequence("A B B C A B C C C A")
result["classification"]   # "ENGINEERED"
result["roles"]            # {"A": "ANCHOR", "B": "TRANSITION", "C": "CONTENT"}
```

### Measuring another program's output (the read-only tap)

The engine is a **universal instrument** — it ingests *any* symbol stream and
never adapts to its source. To measure another system, capture its emitted token /
ID stream to a file and point the tap at it (no coupling, read-only):

```bash
python -m structural_matrix --file captured_stream.txt   # one token per line, or whitespace-separated
```

```python
from structural_matrix import analyze_file
analyze_file("captured_stream.txt")["classification"]    # regime of the stream
```

It scales to long, growing-vocabulary ID streams (20k tokens in well under a
second) and recognises periodic structural markers even when their neighbours
churn — so a rhythmic "anchor" amid high local entropy reads as structure, not
noise. See [`docs/MEASUREMENT.md`](docs/MEASUREMENT.md) for the full guide.

### Don't just trust the verdict — interrogate it

```python
from structural_matrix import structure_significance, verdict_stability, measure

structure_significance("A B C A B C A B C")["significant"]   # True  (not chance)
verdict_stability("Q W E R T Y U I O P")["stability"]         # "robust"/"marginal"/"fragile"
measure(stream, significance_trials=500, stability=True, window=1000)  # one full readout
```

| Capability | Function | CLI |
|---|---|---|
| Structural verdict | `analyze_sequence` | `--spec` |
| Significance (vs chance) | `structure_significance` | `--significance N` |
| Verdict robustness | `verdict_stability` | `--stability` |
| Regime timeline | `analyze_windows` | `--windows N` |
| Everything at once | `measure` | `--measure` |

With 3D folding data (proximity contacts override the symbolic signal):

```bash
python -m structural_matrix --text "ACGTACGTACGT" --chars \
  --proximity "0,11,9; 1,10,9; 2,9,9"
```

## Why it exists

Most analysis tools ask *what does this mean?* The Structural Matrix asks *how
does this behave?* — a **consilient structure filter** that finds the same
invariants across writing systems, biology, cryptography and engineered data by
isolating pure behaviour. See [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) for the
full formal model.

## How it works (the pipeline)

| Stage | Module | Produces |
|------|--------|----------|
| Symbol Vector | `mapping.py` | `f : Σ → ℝ` numeric encoding |
| Behaviour Vector | `behaviour.py` | positional weight, transition matrix, local entropy |
| Spatial Cohesion | `cohesion.py` | per-position 3D contact scores |
| Roles | `roles.py` | Anchor / Frame / Transition / Content / Terminator |
| Motifs | `motifs.py` | cycles, bursts, modular blocks, cascades, … |
| Classification | `classification.py` | argmax over an explainable score vector |

Every stage is an injectable interface — swap the classifier, the mapper, the
motif detector without touching the orchestrator.

## Project map

```
src/structural_matrix/   the engine (one module per pipeline stage)
tests/                   45 tests: stage units, worked examples, fuzz, architecture
loop/                    the autonomous build loop: check.py (gate) + DEVLOG.md
docs/                    the 10 architecture artifacts (read 10 → 1)
```

## Documentation — the 10 artifacts

Read them top-down (structure → behaviour → guarantees → vocabulary → wiring):

1. [Architecture](docs/01-ARCHITECTURE.md) — the city map
2. [Flows](docs/02-FLOWS.md) — the movie
3. [Contracts](docs/03-CONTRACTS.md) — the constitution
4. [Types](docs/04-TYPES.md) — the vocabulary
5. [Schemas](docs/05-SCHEMAS.md) — the conceptual map
6. [Interfaces](docs/06-INTERFACES.md) — the plug sockets
7. [Dependencies](docs/07-DEPENDENCIES.md) — the wiring rules
8. [Modules](docs/08-MODULES.md) — the org chart
9. [Decision Log](docs/09-DECISION-LOG.md) — the diary
10. This README — the front door

## Development

```bash
pip install -e ".[dev]"     # optional: editable install + pytest
python loop/check.py        # the quality gate: import + tests + invariants
pytest -q                   # the test suite alone
```

The build is driven by an autonomous loop (OBSERVE → HYPOTHESIZE → IMPLEMENT →
TEST → MARK → REFINE); its diary is [`loop/DEVLOG.md`](loop/DEVLOG.md).

## License

MIT.
