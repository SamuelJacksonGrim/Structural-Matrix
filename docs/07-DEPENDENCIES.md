# 7 · Dependencies — the wiring rules

> What's allowed to rely on what? (so it doesn't tangle)

## The one rule

**Dependencies point downward only.** A module may import from a *lower* layer,
never from a *higher* one and never sideways between stages.

```
  LAYER 4  cli.py · __main__.py            (edges / entry points)
  LAYER 3  pipeline.py · serialization.py  (orchestration / output)
  LAYER 2  mapping behaviour cohesion roles motifs classification  (stages)
  LAYER 1  interfaces.py                   (seams / protocols)
  LAYER 0  types.py                        (vocabulary — depends on nothing)

         imports may only go DOWN ↓ the layers
```

## Allowed import matrix

| Module | May import |
|--------|-----------|
| `types.py` | *stdlib only* (`dataclasses`, `enum`, `typing`) |
| `interfaces.py` | `types` |
| `mapping`, `behaviour`, `cohesion` | `types` |
| `roles`, `motifs`, `classification` | `types` (+ shared `ANCHOR_ENTROPY_CEIL`) |
| `pipeline.py` | `interfaces`, `types`, and the concrete stage modules (for defaults only) |
| `serialization.py` | `types` |
| `cli.py` | `pipeline`, `mapping`, `serialization`, `types` |

## Critical constraints (these prevent tangle)

1. **Stages never import each other.** `roles` does not import `motifs`;
   `classification` does not import `motifs`. They communicate only through the
   value objects passed in by the orchestrator. This is what makes any single
   stage swappable.
2. **`types` is a sink.** It imports nothing from the package. Shared constants
   (e.g. `ANCHOR_ENTROPY_CEIL`) live here precisely so two stages can agree
   without depending on one another (resolves the near-miss in decision **D-005**).
3. **The orchestrator is the only place that knows concrete defaults.**
   `pipeline.py` imports the `Standard*` classes to supply fallbacks; everywhere
   else the dependency is on the `interfaces` Protocol, not the class.
4. **Edges depend inward, never the reverse.** `cli.py` imports `pipeline`;
   `pipeline` knows nothing about the CLI.

## External dependencies

| Scope | Dependencies |
|-------|--------------|
| Runtime | **none** — Python ≥ 3.9 standard library only |
| Dev/test | `pytest` (optional extra `[dev]`) |
| Build | `setuptools` (PEP 517) |

Zero runtime dependencies is a deliberate, defended choice (**D-001**): it makes
the engine drop-in portable to sandboxed CI/web environments and removes supply-
chain surface.

## Enforcement

- The import matrix is small enough to review by eye in any PR.
- `loop/check.py` tier 1 (`IMPORT`) fails the build instantly if a cycle or a bad
  import is introduced (a cycle makes `import structural_matrix` raise).
- Because stages share no imports, a violating sideways import is visually obvious
  in review and would show up as a new line in a stage's import block.
