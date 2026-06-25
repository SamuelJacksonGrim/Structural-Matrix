# 4 · Types — the vocabulary

> What are the "things" the system talks about?

All types live in `src/structural_matrix/types.py`. Every one is a **frozen
dataclass** (immutable, hashable-friendly, safe to share). They form the nouns of
the pipeline; each stage consumes one and produces the next.

## Closed vocabularies (enums)

### `Role` — what a position is doing
`ANCHOR` · `FRAME` · `TRANSITION` · `CONTENT_BLOCK` · `TERMINATOR` · `UNASSIGNED`

### `MotifType` — recurring structural shapes
`ANCHOR_DRIVEN_CYCLE` · `FLOATING_ANCHOR_DRIFT` · `CLUSTER_BURST` ·
`MODULAR_BLOCK` · `BOUNDARY_FRAME` · `TERMINATOR_LOCK` · `ENTROPY_CASCADE` ·
`NULL` · `HYBRID`

### `StructuralClass` — the final verdict
`NATURAL` · `ENGINEERED` · `CONSTRUCTED` · `RANDOM` · `THREE_D_DRIVEN`

## Value objects (one per pipeline stage)

| Type | Stage | Key fields |
|------|-------|-----------|
| `Sequence` | 0 · input | `symbols: tuple[str,…]`; props `n`, `alphabet`, ctor `from_text` |
| `SymbolVector` | 1 · SV | `values: tuple[float,…]`, `mapping: dict[str,float]`, `strategy: str` |
| `BehaviourVector` | 2 · BV | `positional_weight`, `entropy`, `transition_counts`, `transition_prob`, `symbol_entropy`, `max_transition_prob` |
| `CohesionVector` | 3 · SCV | `cohesion: tuple[float,…]`, `pairs`, prop `dominant` |
| `RoleAssignment` | 4 · Roles | `roles: tuple[Role,…]`, `thresholds: dict[str,float]`, `counts()` |
| `Motif` / `MotifSet` | 5 · Motifs | `Motif(type, confidence, span, detail)`; `MotifSet.has(type)`, `types()` |
| `Classification` | 6 · Class | `label: StructuralClass`, `scores: dict`, `confidence: float` |
| `AnalysisReport` | result | bundles all of the above + `meta` |

## The shared constant

`ANCHOR_ENTROPY_CEIL = 0.5` (bits) — the single source of truth for "what counts
as a genuine anchor", imported by both `motifs.py` and `classification.py` so they
can never drift apart (see **C-8 / D-005**).

## Illustrative shapes

```python
Sequence(symbols=("A", "B", "B", "C"))
# .n -> 4 ; .alphabet -> ("A", "B", "C")

SymbolVector(values=(1.0, 2.0, 2.0, 3.0),
             mapping={"A": 1.0, "B": 2.0, "C": 3.0},
             strategy="ordinal")

Motif(type=MotifType.CLUSTER_BURST, confidence=0.6, span=(6, 8),
      detail="run of 'C' x3")

Classification(label=StructuralClass.ENGINEERED,
               scores={StructuralClass.ENGINEERED: 1.46, ...},
               confidence=0.52)
```

## Conventions

- **Tuples, not lists**, for sequence data — immutability is enforced, not hoped for.
- **`str`-valued enums** (`class Role(str, Enum)`) so values serialise to readable
  JSON (`"Anchor"`) without custom encoders.
- **Entropy is always in bits** (`log₂`) across every type and stage.
- Construction helpers (`Sequence.from_text`) live *on the type*; analysis logic
  never does — types are data, stages are behaviour.

See [05 · Schemas](05-SCHEMAS.md) for how these relate and transform, and
[serialization.py] for their JSON projection.
