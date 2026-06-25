# 1 · Architecture — the city map

> What are the big pieces, and how are they laid out?

## The shape in one picture

The Structural Matrix is a **linear pipeline of injectable stages** wrapped by a
single orchestrator. Data flows in one direction; each stage adds a layer of
interpretation and never reaches back.

```
                       ┌───────────────────────────────────────────┐
   input text / list   │              StructuralMatrix              │
        │              │              (pipeline.py)                 │
        ▼              │                                            │
   ┌─────────┐         │   ┌────────┐  ┌────────┐  ┌────────────┐   │
   │ Sequence│────────▶│──▶│ Mapper │─▶│Behaviour│─▶│  Cohesion  │  │
   └─────────┘         │   └────────┘  └────────┘  └────────────┘   │
                       │        │SV         │BV          │SCV       │
                       │        └─────┬─────┴──────┬─────┘          │
                       │              ▼            ▼                │
                       │        ┌──────────┐  ┌──────────┐          │
                       │        │  Roles   │─▶│  Motifs  │          │
                       │        └──────────┘  └──────────┘          │
                       │              │            │                │
                       │              ▼            ▼                │
                       │          ┌────────────────────┐           │
                       │          │   Classification   │           │
                       │          └────────────────────┘           │
                       │                    │                       │
                       └────────────────────┼───────────────────────┘
                                            ▼
                                    AnalysisReport ──▶ serialization (JSON) / CLI
```

## The big pieces (districts of the city)

| District | Files | Responsibility |
|----------|-------|----------------|
| **Vocabulary** | `types.py` | Immutable value objects + shared constants. Depends on nothing. |
| **Seams** | `interfaces.py` | One `Protocol` per stage — the swappable plug sockets. |
| **Stages** | `mapping, behaviour, cohesion, roles, motifs, classification` | The six analysis steps. Each implements one seam. |
| **Orchestrator** | `pipeline.py` | Wires the stages in order. Owns *no* analysis logic. |
| **Edges** | `serialization.py`, `cli.py`, `__main__.py` | Turn a report into JSON / text; the command-line front door. |
| **Harness** | `loop/check.py` | The autonomous quality gate (import + tests + invariants). |

## Layering rule

The system is built in strata; **higher strata may use lower, never the reverse**:

```
   edges (cli, serialization)          ── may use everything below
   orchestrator (pipeline)             ── wires stages via interfaces
   stages (mapping … classification)   ── may use types + interfaces
   seams (interfaces)                  ── may use types
   vocabulary (types)                  ── depends on nothing
```

This is what keeps the city from tangling; the enforceable form lives in
[07 · Dependencies](07-DEPENDENCIES.md).

## Key architectural properties

- **Deterministic.** Given a fixed mapping, the same input always yields the same
  report (no randomness, no clocks, no global state).
- **Pure standard library.** Zero third-party runtime dependencies — portable to
  any Python ≥ 3.9 environment, including locked-down CI/web sandboxes.
- **Open/Closed at every stage.** Each stage is selected by dependency injection
  in `StructuralMatrix.__init__`; behaviour is extended by substitution, not edits.
- **Explainable output.** The verdict ships with the full score vector, the roles,
  the motifs and the thresholds used — nothing is a black box.

## What this architecture deliberately is *not*

- Not a plugin-discovery framework — stages are passed in by the caller, not
  auto-loaded. Simplicity over magic (see decision **D-002**).
- Not concurrent — the pipeline is sequential by design; determinism and
  readability beat parallelism for the data sizes involved (**D-006**).
