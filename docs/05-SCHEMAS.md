# 5 · Schemas — the conceptual map

> How do those things relate and change?

## Entity-relationship view

```
                 ┌──────────┐
                 │ Sequence │  symbols: (s₁…sₙ)   alphabet ⊆ Σ
                 └────┬─────┘
        ┌────────────┼───────────────┬───────────────┐
        ▼            ▼               ▼               ▼
 ┌────────────┐ ┌──────────────┐ ┌──────────────┐ (proximity P, optional)
 │SymbolVector│ │BehaviourVector│ │              │        │
 │ f:Σ→ℝ      │ │ pw, H, T, P   │ │              │        ▼
 └────────────┘ └──────┬───────┘ │              │ ┌──────────────┐
                       │         │              └▶│CohesionVector│
                       │         │                │ Cᵢ = Σ wᵢⱼ    │
                       ▼         ▼                └──────┬───────┘
                 ┌──────────────────┐                    │
                 │  RoleAssignment  │◀───────────────────┘
                 │ roles + τ_A,τ_T,τ_C
                 └────────┬─────────┘
                          ▼
                    ┌──────────┐        ┌───────────────┐
                    │ MotifSet │───────▶│ Classification│
                    └──────────┘        │ label+scores  │
                          │             └───────┬───────┘
                          └──────────┬──────────┘
                                     ▼
                              ┌──────────────┐
                              │ AnalysisReport│  (1 per run, owns all the above)
                              └──────────────┘
```

**Cardinality:** one `AnalysisReport` owns exactly one of each stage object; a
`MotifSet` owns 0..* `Motif`; a `Classification` owns one score per
`StructuralClass`.

## Transformation schema (how data changes shape)

| From → To | Operation | Invariant introduced |
|-----------|-----------|----------------------|
| `Sequence → SymbolVector` | apply `f : Σ → ℝ` | one value per position |
| `Sequence → BehaviourVector` | count transitions, normalise, entropy | `Σ_b P(a→b)=1`; `H` in bits |
| `Sequence,P → CohesionVector` | accumulate contact weights | `Cᵢ ≥ 0` |
| `BV,SCV → RoleAssignment` | adaptive threshold banding | one `Role` per position |
| `BV,SCV,Roles → MotifSet` | pattern detectors | ≥ 1 motif (Null floor) |
| `…all… → Classification` | feature scoring + argmax | scores finite; conf ∈ [0,1] |

## State / lifecycle

Objects are **immutable snapshots**, so there is no in-place mutation state
machine. The only "state transition" is *creation of the next stage object*:

```
(none) ──map──▶ SV ──analyze──▶ BV ──analyze──▶ SCV
   ──assign──▶ Roles ──detect──▶ Motifs ──classify──▶ Class ──bundle──▶ Report
```

Once created, an object is final. Re-running a stage produces a new object; it
never edits an existing one (contract **C-10**).

## JSON projection schema

`serialization.report_to_dict` flattens a report into a stable, JSON-safe tree:

```jsonc
{
  "sequence": ["A","B","B","C", …],
  "n": 10, "alphabet": ["A","B","C"],
  "symbol_vector": { "strategy": "ordinal", "mapping": {…}, "values": [...] },
  "behaviour": {
    "positional_weight": [...], "entropy": [...],
    "symbol_entropy": {…}, "transition_prob": {…}, "max_transition_prob": {…}
  },
  "cohesion": { "values": [...], "dominant": false },
  "roles": { "per_position": [...], "thresholds": {…}, "counts": {…} },
  "motifs": [ { "type": "...", "confidence": 0.89, "span": [a,b], "detail": "..." } ],
  "classification": { "label": "Engineered", "confidence": 0.52, "scores": {…} },
  "meta": { "mapping_strategy": "ordinal", "n": 10, "alphabet_size": 3 }
}
```

This shape is the **stable external contract** for downstream consumers — enum
values are strings, all numbers are JSON floats, no Python-specific objects leak.
