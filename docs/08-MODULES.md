# 8 · Modules — the org chart

> What are the pieces, and who's responsible for what?

Each module has **one job** and a single reason to change. If a change touches
more than one module, that's a signal the responsibility boundary is being
crossed.

## The org chart

```
                        StructuralMatrix (pipeline.py)
                        "the manager — wires, owns no logic"
        ┌──────────┬──────────┬──────────┬──────────┬──────────────┐
        ▼          ▼          ▼          ▼          ▼              ▼
     mapping   behaviour   cohesion    roles      motifs     classification
       SV         BV         SCV      role tags   patterns      verdict
        └──────────┴──────────┴────┬─────┴──────────┴──────────────┘
                                   ▼
                        types.py  (the vocabulary everyone speaks)
                        interfaces.py  (the contracts everyone signs)
```

## Responsibilities

| Module | Owns | Changes when… | Key exports |
|--------|------|---------------|-------------|
| `types.py` | the data vocabulary + shared constants | a new field/enum value is needed | `Sequence`, `BehaviourVector`, …, `ANCHOR_ENTROPY_CEIL` |
| `interfaces.py` | the stage contracts | a stage's signature changes | `SymbolMapper`, …, `Classifier` |
| `mapping.py` | `f : Σ → ℝ` strategies | a new encoding is added | `OrdinalMapper`, `FrequencyMapper`, `CustomMapper`, `get_mapper` |
| `behaviour.py` | positional weight, transitions, entropy | the BV math changes | `StandardBehaviourAnalyzer` |
| `cohesion.py` | 3D contact accumulation | spatial model changes | `StandardCohesionAnalyzer` |
| `roles.py` | adaptive role banding + degenerate fallback | role rules change | `StandardRoleAssigner` |
| `motifs.py` | pattern detectors | a motif is added/tuned | `StandardMotifDetector` |
| `classification.py` | features → scores → argmax | the verdict logic changes | `StandardClassifier`, `compute_features`, `Features` |
| `pipeline.py` | stage wiring + defaults | the stage *order* changes | `StructuralMatrix` |
| `analyzer.py` | spec-conformant facade + read-only stream tap | the spec's output contract changes | `StructuralMatrixAnalyzer`, `analyze_sequence`, `analyze_file` |
| `serialization.py` | report → JSON-able dict | the external JSON shape changes | `report_to_dict` |
| `cli.py` / `__main__.py` | argument parsing + rendering | the CLI surface changes | `main`, `build_parser` |

## Sizing & cohesion

- Each stage module is **one class + small helpers**, typically 60–160 lines.
- Helpers are private (`_underscore`) and live next to their only caller.
- No module reaches across a sibling stage; collaboration is via `types` objects
  passed by the manager (see [07 · Dependencies](07-DEPENDENCIES.md)).

## Test modules (who verifies whom)

| Test module | Covers |
|-------------|--------|
| `test_foundation.py` | `Sequence`, mapping, behaviour, cohesion (stage units) |
| `test_pipeline.py` | end-to-end + the four worked examples + roles/motifs |
| `test_fuzz.py` | totality & well-formedness over random/adversarial input |
| `test_architecture.py` | mapping-agnosticism + the swappable-stage seam |

## The harness (outside the package)

| File | Job |
|------|-----|
| `loop/check.py` | the quality gate: IMPORT → TESTS → INVARIANTS, exit 0 iff green |
| `loop/DEVLOG.md` | the autonomous loop's diary (hypothesis → result per iteration) |
