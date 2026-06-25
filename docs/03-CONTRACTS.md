# 3 · Contracts — the constitution

> What must *always* be true? What's promised?

These are invariants the engine guarantees regardless of input. Each is enforced
by a test (`tests/`) and/or the loop gate (`loop/check.py`). Breaking one is a
regression, not a judgement call.

## C-1 · Totality (the engine never crashes)

For **any** input sequence — empty, length 1, single-symbol alphabet, all
distinct, unicode, 5000 symbols — `analyze` returns a well-formed `AnalysisReport`.
It never raises on shape alone.

- *Enforced by:* `test_fuzz.py` (400 random + 7 adversarial shapes + smoke).

## C-2 · Well-formed report

Every `AnalysisReport` satisfies, with `n = sequence.n`:

- `len(roles.roles) == n` — exactly one role per position.
- `len(behaviour_vector.entropy) == n` and `len(positional_weight) == n`.
- `len(motifs.motifs) >= 1` — at least `Null Motif` is always present.
- every score in `classification.scores` is finite.
- `0.0 ≤ classification.confidence ≤ 1.0`.

- *Enforced by:* `_assert_valid_report` in `test_fuzz.py`; `roles_cover` invariant.

## C-3 · Determinism

Given a fixed mapper, the same input yields byte-identical results:
`analyze(x).classification.scores == analyze(x).classification.scores`. No
randomness, clocks, hashing-by-address, or global mutable state participates.

- *Enforced by:* `test_pipeline.test_pipeline_is_deterministic`; gate invariant
  `determinism`.

## C-4 · Mapping-agnostic classification

The structural **class** does not depend on which `f : Σ → ℝ` mapping is chosen
(ordinal vs frequency vs custom). Behaviour is computed from symbol *transitions*,
not from the numeric encoding (see decision **D-007**).

- *Enforced by:* `test_architecture.test_classification_is_mapping_agnostic`.

## C-5 · Probability normalisation

For every symbol `a` with outgoing transitions, `Σ_b P(a → b) == 1` (within float
tolerance). Local entropy uses `log₂`, so it is reported in **bits**.

- *Enforced by:* `test_foundation.test_transition_probabilities_sum_to_one`.

## C-6 · Worked-example fidelity (the headline promise)

The four canonical sequences from the methodology classify exactly as documented:

| Sequence | Class |
|----------|-------|
| `A B B C A B C C C A` | **Engineered** |
| `X Y X Z Y X Y Y Z X Y Z` | **Natural** |
| `Q W E R T Y U I O P` | **Random** |
| `A A B A A B C C A A B` | **Constructed** |

- *Enforced by:* `test_pipeline.test_worked_example_classifications`; gate
  invariants `classify[*]`.

## C-7 · Spatial override

When meaningful 3D proximity data is supplied (positive contact weights), the
verdict is `3D-Driven` — spatial cohesion dominates the symbolic signal.

- *Enforced by:* `test_pipeline.test_spatial_cohesion_forces_3d_class`; gate
  invariant `3d_override`.

## C-8 · Honest motifs

A reported `Anchor-Driven Cycle` is always backed by a genuinely low-entropy
(≤ `ANCHOR_ENTROPY_CEIL` = 0.5 bits) symbol. The motif list never contradicts the
classifier's anchor rule (decision **D-005**).

- *Enforced by:* `test_pipeline.test_anchor_cycle_motif_only_on_low_entropy_symbol`;
  gate invariant `honest_anchor_cycle`.

## C-9 · Eager input validation

Invalid *parameters* (as opposed to merely unusual data) fail fast and loudly:
out-of-range proximity indices → `IndexError`; negative weights → `ValueError`;
unknown mapping strategy → `ValueError`.

- *Enforced by:* `test_foundation` cohesion/mapping tests.

## C-10 · Immutability of results

All stage outputs are frozen dataclasses. A report can be passed across the
system without any stage mutating another's output.

- *Enforced by:* `@dataclass(frozen=True)` on every value object in `types.py`.

---

### Adaptive thresholds (promised behaviour, not fixed values)

`τ_A`, `τ_T`, `τ_C` are **derived per sequence** (methodology §5), so the contract
is about *how* they adapt, not their absolute value:

- `τ_A = e_min + 0.25·(e_max − e_min)` (low-entropy band)
- `τ_C = e_min + 0.75·(e_max − e_min)` (high-entropy band)
- `τ_T = max(0.5, mean dominant-transition prob among non-anchor symbols)`
- The absolute ceiling `ANCHOR_ENTROPY_CEIL = 0.5` bits gates *engineered* anchors
  and anchor-cycle motifs, independent of the adaptive band.
