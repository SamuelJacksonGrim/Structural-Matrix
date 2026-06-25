# 6 · Interfaces — the plug sockets

> How do the pieces connect so one can be swapped out?

Every pipeline stage is defined as a `typing.Protocol` in
`src/structural_matrix/interfaces.py`. The orchestrator depends only on these
shapes, never on concrete classes — so any implementation that satisfies the
socket can be plugged in. All protocols are `@runtime_checkable`, so
`isinstance(obj, SymbolMapper)` works for duck-typed checks.

## The six sockets

| Protocol | Method | In → Out |
|----------|--------|----------|
| `SymbolMapper` | `map(sequence)` | `Sequence → SymbolVector` |
| `BehaviourAnalyzer` | `analyze(sequence, sv)` | `… → BehaviourVector` |
| `CohesionAnalyzer` | `analyze(sequence, proximity)` | `… → CohesionVector` |
| `RoleAssigner` | `assign(sequence, bv, scv)` | `… → RoleAssignment` |
| `MotifDetector` | `detect(sequence, bv, scv, roles)` | `… → MotifSet` |
| `Classifier` | `classify(sequence, bv, scv, roles, motifs)` | `… → Classification` |

```python
@runtime_checkable
class Classifier(Protocol):
    def classify(self, sequence, bv, scv, roles, motifs) -> Classification: ...
```

## How they're wired (dependency injection)

`StructuralMatrix.__init__` takes one optional implementation per socket and
falls back to the `Standard*` default:

```python
StructuralMatrix(
    mapper=None,          # default OrdinalMapper
    behaviour=None,       # default StandardBehaviourAnalyzer
    cohesion=None,        # default StandardCohesionAnalyzer
    role_assigner=None,   # default StandardRoleAssigner
    motif_detector=None,  # default StandardMotifDetector
    classifier=None,      # default StandardClassifier
)
```

## Swapping a stage (the whole point)

Replace the verdict logic without touching the engine — proven by
`tests/test_architecture.py`:

```python
class WeightedClassifier:
    def __init__(self, weights): self.weights = weights
    def classify(self, sequence, bv, scv, roles, motifs):
        ...  # return a Classification
        return Classification(label, scores, confidence)

engine = StructuralMatrix(classifier=WeightedClassifier(my_weights))
report = engine.analyze("A B B C A B C C C A")   # upstream stages unchanged
```

Or change the encoding strategy:

```python
from structural_matrix.mapping import FrequencyMapper
engine = StructuralMatrix(mapper=FrequencyMapper())
# Per contract C-4 this does NOT change the class — only the reported SV.
```

## Built-in implementations behind each socket

| Socket | Defaults available |
|--------|--------------------|
| `SymbolMapper` | `OrdinalMapper`, `FrequencyMapper`, `CustomMapper(dict)`, `CallableMapper(fn)` |
| `BehaviourAnalyzer` | `StandardBehaviourAnalyzer` |
| `CohesionAnalyzer` | `StandardCohesionAnalyzer` |
| `RoleAssigner` | `StandardRoleAssigner(frame_fraction=0.1)` |
| `MotifDetector` | `StandardMotifDetector(cluster_min_run=3)` |
| `Classifier` | `StandardClassifier` |

## Why Protocols (not abstract base classes)

- **Structural typing** — an implementation need not import or subclass anything;
  it just needs the right method. This keeps third-party extensions zero-coupling.
- **No inheritance tax** — defaults are plain classes; tests use tiny stubs.
- **Runtime-checkable** — `isinstance` still works where a guard is useful.

See decision **D-003** for the Protocol-vs-ABC rationale.
