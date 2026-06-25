# 2 · Flows — the movie

> What actually *happens*, step by step, when it runs?

## Main flow: `analyze(sequence)`

This is the one path that matters. Every public entry point funnels into it.

```
CALLER                pipeline.StructuralMatrix            stages
  │  analyze("A B B C A B C C C A")
  ├───────────────────────────────────▶│
  │                                     │ _coerce(...) ─▶ Sequence(symbols=…)
  │                                     │
  │                                     │ 1. mapper.map(seq) ───────────▶ SymbolVector
  │                                     │      f:Σ→ℝ, e.g. A=1 B=2 C=3
  │                                     │
  │                                     │ 2. behaviour.analyze(seq, sv) ▶ BehaviourVector
  │                                     │      pw_i=i/n ; T(a,b) counts ;
  │                                     │      P(a→b)=T/ΣT ; H(a)=−ΣP·log₂P
  │                                     │
  │                                     │ 3. cohesion.analyze(seq, prox) ▶ CohesionVector
  │                                     │      C_i = Σ_j w_ij  (0 if no 3D data)
  │                                     │
  │                                     │ 4. roles.assign(seq, bv, scv) ▶ RoleAssignment
  │                                     │      adaptive τ_A, τ_T, τ_C →
  │                                     │      Anchor/Transition/Content/Frame/Terminator
  │                                     │
  │                                     │ 5. motifs.detect(seq,bv,scv,roles) ▶ MotifSet
  │                                     │      cycles, bursts, modular blocks,
  │                                     │      cascades, frames, hybrid/null
  │                                     │
  │                                     │ 6. classifier.classify(…) ────▶ Classification
  │                                     │      features → scores → argmax
  │                                     │
  │   ◀──────────── AnalysisReport ─────┤  (bundles every intermediate result)
```

Step order is fixed because each step consumes the previous one's output:
`SV → BV → SCV → Roles → Motifs → Class`. The orchestrator never branches; it
only forwards.

## Decision sub-flow: how a class is chosen (step 6 in detail)

```
compute_features(seq, bv, scv, motifs)
  ├─ distinct_ratio   = |Σ| / n           reuse = 1 − distinct_ratio
  ├─ mean_entropy_norm, entropy_var_norm   (normalised by log₂|Σ|)
  ├─ predictability   = mean(max P(a→·))
  ├─ anchor_cycle_conf  (low-entropy ≤0.5 symbol at regular intervals)
  ├─ modular_strength   (best repeated multi-symbol template × coverage)
  ├─ cluster_strength   (positions inside runs of length ≥ 3)
  └─ scv_signal         (1 if spatial cohesion present)
        │
        ▼
   score each class  ──▶  RANDOM      = 1.5·distinct_ratio − structure
                         ENGINEERED  = 1.2·cycle + 0.6·(pred·reuse) + 0.3·cluster
                         CONSTRUCTED = 1.3·modular + 0.4·reuse + 0.4·(1−var) − 0.7·cycle
                         NATURAL     = mean_entropy + 0.5·reuse − 0.8·modular − 0.5·cycle
                         3D-DRIVEN   = 2.0·scv_signal
        │
        ▼
   label = argmax(scores) ; confidence = softmax(scores)[label]
```

The full derivation (and why each weight is what it is) is in
[03 · Contracts](03-CONTRACTS.md) and validated by the four worked examples in
`tests/test_pipeline.py`.

## Role-assignment sub-flow (step 4 in detail)

```
_thresholds(bv):  τ_A = e_min + 0.25·spread   τ_C = e_min + 0.75·spread
                  τ_T = max(0.5, mean dominant-transition prob of non-anchors)

if spread ≈ 0  ──▶  _assign_degenerate(...)        # uniform entropy fallback
                     Frame(edge) > Anchor(most frequent) > Content(cluster) > Transition
else           ──▶  per position, by precedence:
                     Terminator → Anchor(H<τ_A) → Transition(maxP≥τ_T)
                     → Content(H>τ_C) → Frame(edge) → Unassigned
```

## CLI flow

```
argv ─▶ build_parser() ─▶ read --text or stdin ─▶ Sequence.from_text(sep)
     ─▶ StructuralMatrix(mapper=…).analyze(seq, proximity) ─▶ AnalysisReport
     ─▶ --json ? report_to_dict→json.dumps : _render_human ─▶ stdout, exit 0
```

## Error & edge flows (what happens when input is weird)

| Input | What happens | Where |
|-------|--------------|-------|
| Empty string | `n=0`, `Null Motif` emitted, no crash | `motifs.detect` early return |
| Single symbol | one role, valid report | role/behaviour guards |
| Single-symbol alphabet | `max_possible=1.0` guard avoids ÷0 | `classification.compute_features` |
| Proximity index out of range | `IndexError` raised eagerly | `cohesion.analyze` |
| Negative proximity weight | `ValueError` raised eagerly | `cohesion.analyze` |
| Unknown mapping name | `ValueError` from `get_mapper` | `mapping.get_mapper` |

These are pinned by `tests/test_fuzz.py` (400 randomised + 7 adversarial shapes).
