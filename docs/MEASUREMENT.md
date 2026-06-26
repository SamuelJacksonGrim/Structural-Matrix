# Measuring another program with the Structural Matrix

The engine is a **universal instrument**: it ingests any symbol stream and reports
its structure, ignoring meaning. To measure another system you do **not** adapt
the engine — you capture that system's emitted stream and feed it in, read-only.
There is no coupling in this direction (see decision **D-008**).

## 1. Capture a stream

Export whatever symbolic sequence the target program emits — token IDs, stable
IDs, glyphs, classes, opcodes — to a file, one token per line or whitespace
separated:

```
17
17
42
17
93
...
```

## 2. Point the tap at it

```bash
python -m structural_matrix --file captured_stream.txt            # human report
python -m structural_matrix --file captured_stream.txt --spec     # spec dict (JSON)
python -m structural_matrix --file captured_stream.txt --measure  # full readout
```

Or in Python:

```python
from structural_matrix import analyze_file, measure

analyze_file("captured_stream.txt")["classification"]   # NATURAL / ENGINEERED / ...
measure(open("captured_stream.txt").read().split())     # full readout dict
```

## 3. Read the regime — and decide whether to trust it

A single label is not enough for a fragile signal. The instrument ships its own
interpretation discipline:

| Question | Call | What it tells you |
|----------|------|-------------------|
| What regime is this stream? | `analyze_sequence` / `--spec` | `NATURAL` / `ENGINEERED` / `CONSTRUCTED` / `RANDOM` |
| Is the structure *real* or chance? | `structure_significance` / `--significance N` | permutation p-value (small ⇒ real) |
| Can I trust this verdict? | `verdict_stability` / `--stability` | `robust` / `marginal` / `fragile` |
| Does the regime change over time? | `analyze_windows` / `--windows N` | per-window timeline + `change_points` |
| Everything at once | `measure` / `--measure` | one JSON-safe readout |

```python
from structural_matrix import structure_significance, verdict_stability

structure_significance(stream, trials=500)["significant"]   # True ⇒ not noise
verdict_stability(stream)["stability"]                       # "robust" ⇒ trust it
```

## 4. Reading a live/long stream as a timeline

For an evolving stream (e.g. a system that births and reaps symbols over time),
measure it in windows to see *where* the regime shifts:

```python
from structural_matrix import analyze_windows
tl = analyze_windows(stream, window=1000)
tl["regime_summary"]["change_points"]   # window indices where structure flips
tl["regime_summary"]["dominant"]        # the prevailing regime
```

This is the "structure → noise" health trace: a healthy emergent stream tends to
hold or build structure; a degrading one cascades toward `RANDOM`.

## What the roles mean for a stream of identities

The per-symbol roles (`analyze_sequence(...)["roles"]`) describe how each token
*behaves*, independent of any class its source assigned it:

- **ANCHOR** — a stable, recurring or rhythmically periodic marker (a structural
  beat). Recognised by low transition entropy *or* strong positional periodicity
  (decision **D-009**), so a marker that recurs on a regular cadence amid churn
  still reads as an anchor.
- **TERMINATOR** — an end-localised, transition-collapsing marker.
- **CONTENT** — high-entropy, clustering material.
- **TRANSITION** — a directional connector between roles.
- **FRAME** — a boundary marker.

A mismatch between a token's declared class (in the source system) and its
emergent role here is itself a signal worth investigating.

## Boundary

This is **measurement only** — a read-only observation. Any future control loop
(letting a verdict act back on the source system) is a separate, opt-in design,
not part of the instrument. The instrument never reaches into what it measures.
