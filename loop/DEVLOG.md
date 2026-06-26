# Autonomous Development Loop — DEVLOG

This is the running diary of the self-driving build loop. Each iteration follows
the same cycle and is recorded below verbatim, newest at the bottom.

```
   ┌─────────────────────────────────────────────────────────────┐
   │  OBSERVE   run loop/check.py → read PASS/FAIL + real output   │
   │     ↓                                                         │
   │  HYPOTHESIZE  predict what will fail next and why             │
   │     ↓                                                         │
   │  IMPLEMENT  make the smallest change that tests the hypothesis│
   │     ↓                                                         │
   │  TEST       add/adjust tests; run the quality gate            │
   │     ↓                                                         │
   │  MARK       record result: hypothesis confirmed / refuted     │
   │     ↓                                                         │
   │  REFINE     keep the green, feed the surprise into next loop  │
   └─────────────────────────────────────────────────────────────┘
```

**Gate** = `python loop/check.py`: IMPORT ✓ → TESTS ✓ → INVARIANTS ✓, exit 0 iff all green.

---

## Iteration 1 — Baseline build

- **Hypothesis:** A pure-stdlib pipeline (`S→SV→BV→SCV→Roles→Motifs→Class`) can
  reproduce all four worked-example classifications deterministically.
- **Implemented:** full package (`types, interfaces, mapping, behaviour, cohesion,
  roles, motifs, classification, pipeline, serialization, cli`) + 30 tests.
- **Test:** gate green — IMPORT ✓, TESTS 30/30 ✓, INVARIANTS 11/11 ✓.
- **Marked:** ✅ Confirmed. All four examples classify correctly
  (Engineered / Natural / Random / Constructed); 3D proximity overrides to 3D-Driven.
- **Surprise → next loop:** observing real CLI output revealed two honesty gaps:
  1. Example 2 emits an `Anchor-Driven Cycle` motif on `X` (entropy 0.811), but the
     classifier only treats entropy ≤ 0.5 as a true anchor — the **motif list is
     inconsistent with the verdict**.
  2. Examples 3 & 4 collapse *every* position to `Transition` because uniform
     entropy makes the adaptive bands degenerate — **roles become uninformative**.

---

## Iteration 2 — Honest anchor-cycle motif

- **Hypothesis:** Aligning the motif detector's anchor test with the classifier's
  absolute entropy ceiling (≤ 0.5 bits) will drop the false `Anchor-Driven Cycle`
  on Example 2 *without* changing any of the four classifications (the classifier
  already used the strict rule, so only the reported motif list should change).
- **Predicted failures if wrong:** Example 1 loses its (correct) anchor cycle, or a
  classification flips.
- **Implemented:** hoisted `ANCHOR_ENTROPY_CEIL` to `types.py` (single source of
  truth) and gated the motif's `cycle_anchors` on it; added a regression test.
- **Test:** gate green — TESTS 31/31 ✓, INVARIANTS 11/11 ✓.
- **Marked:** ✅ Confirmed. Example 2 motifs went `Anchor-Driven Cycle + Modular
  Block + Hybrid` → just `Modular Block`. Example 1 keeps its real cycle. No
  classification changed. Hypothesis held exactly as predicted.

---

## Iteration 3 — De-collapse roles under uniform entropy

- **Hypothesis:** When entropy is uniform (spread ≈ 0) the adaptive bands can't
  separate roles, so every position becomes `Transition` (seen on Examples 3 & 4).
  Adding a degenerate-case fallback that ranks by *frequency, cluster membership
  and edge position* will recover the methodology's intended roles for Example 4
  (A=Anchor/Frame, B=Transition, C=Content) without touching Examples 1 & 2
  (whose entropy is non-uniform) or any classification.
- **Predicted failures if wrong:** Example 1/2 roles shift, or a class flips
  because role-derived signals leak into the classifier.
- **Implemented:** `_assign_degenerate` fallback (Frame→Anchor→Content→Transition
  by frequency/cluster/edge) triggered only when entropy spread ≈ 0; regression test.
- **Test:** gate green — TESTS 32/32 ✓, INVARIANTS 11/11 ✓.
- **Marked:** ✅ Confirmed. Example 4 roles: `Transition×11` →
  `Anchor×5, Frame×2, Transition×2, Content Block×2`. Examples 1 & 2 unchanged;
  no classification changed (the classifier recomputes features independently of
  role labels, as the dependency rules require).

---

## Iteration 4 — Fuzz the invariants

- **Hypothesis:** The pipeline never crashes and always emits *valid* output
  (finite scores, confidence ∈ [0,1], one role per position, ≥1 motif) for
  arbitrary inputs — including adversarial shapes: length 0/1, single-symbol
  alphabets, all-distinct sequences, unicode tokens, very long sequences.
- **Predicted failures if wrong:** div-by-zero when alphabet size is 1
  (`log2(1)=0`), empty transition rows, or `statistics.pstdev` on length-1 gap
  lists in motif detection.
- **Implemented:** `tests/test_fuzz.py` — 7 adversarial shapes + 400 randomised
  sequences + 5000-symbol smoke + random-DNA case, all asserting `_valid_report`.
- **Test:** gate green — TESTS 43/43 ✓, INVARIANTS 11/11 ✓.
- **Marked:** ✅ Confirmed, hypothesis held. The predicted div-by-zero paths did
  **not** fire: the `max_possible = … else 1.0` guard and the `len(pos) >= 3`
  pre-checks (so gap lists always have ≥ 2 elements for `pstdev`) already cover
  them. No code change was needed — the fuzz suite converts that reasoning into a
  standing contract.

---

## Iteration 5 & 6 — Prove the architecture claims

- **Hypotheses:** H5 classification is mapping-agnostic; H6 stages are swappable
  via the `interfaces` seam.
- **Implemented:** `tests/test_architecture.py` — ordinal-vs-frequency invariance
  across all four examples; an injected `_AlwaysRandom` stub classifier.
- **Test:** gate green — TESTS 45/45 ✓, INVARIANTS 11/11 ✓.
- **Marked:** ✅ Both confirmed. **Honest finding:** classification is
  mapping-agnostic because the numeric Symbol Vector is *not consumed* downstream
  — behaviour is built from symbol *transitions* (counts over `Σ`), so the
  ordinal/frequency map only affects the reported `SV`, not the verdict. The SV is
  therefore informational today and a seam for future embedding-based behaviour.
  Recorded as decision **D-007** in `docs/09-DECISION-LOG.md`.

---

## Checkpoint after iteration 6 — STABLE GREEN (build phase)

6 iterations, gate green at every commit point. Headline behaviour (all four
worked examples + 3D override) is locked by both `tests/` and `loop/check.py`
invariants. (Resumed below at iteration 7 after the developer spec and the
external-stream measurement use-case were introduced.)

---

## Iteration 7 — Spec-conformant facade (`analyze_sequence`)

Context: `docs/DEVELOPER_SPEC.md` (Mark's spec) pins an exact public API and output
contract. Goal is to satisfy it *additively* — a facade over the existing engine —
without disturbing the proven internals, and to keep the engine a **standalone
universal instrument** (no source coupling; pure measurement).

- **Hypothesis:** A thin `StructuralMatrixAnalyzer` + `analyze_sequence()` can emit
  the spec's exact dict (symbol→role, role_sequence, role-level transition matrix,
  scalar `symbol_entropy`/`transition_entropy`, `cluster_stats`, UPPERCASE 4-class
  label) by *reshaping* an `AnalysisReport` — changing no stage logic and flipping
  no existing test.
- **Predicted failures if wrong:** symbol→role aggregation is ambiguous when a
  symbol plays two roles across positions (resolve by dominant behaviour, per spec
  §3.2); `THREE_D_DRIVEN` leaking into a 4-class contract (facade passes no
  proximity, so it cannot fire — assert it).
- **Implemented:** `analyzer.py` (`StructuralMatrixAnalyzer` + `analyze_sequence`);
  `docs/DEVELOPER_SPEC.md` added as source of truth; `tests/test_spec_api.py`.
- **Test:** gate green — TESTS 60/60 ✓, INVARIANTS 11/11 ✓.
- **Marked:** ✅ Confirmed exactly as predicted. Output dict matches the spec field
  for field; `roles` = `{A:ANCHOR, B:TRANSITION, C:CONTENT}` reproduces the
  methodology's Example 1 by hand; the role-transition matrix surfaces the
  `ANCHOR→TRANSITION→CONTENT→ANCHOR` cycle. No internal logic touched; no existing
  test changed.

---

## Iteration 8 — Scale to ID streams + a read-only file tap

Context: the engine must be a *standalone universal instrument*. To measure another
program it should ingest that program's emitted stream directly —
a long sequence of token/stable IDs — with no coupling, just a way to read a file.

- **Hypothesis:** The pipeline stays total and fast (sub-second) on a 20k-token
  stream with a large, *growing* integer-ID alphabet (births/reaps over time), and
  a `--file` / `analyze_file` tap can read such a captured stream straight in.
- **Predicted failures if wrong:** O(n·L) n-gram/template scans blow up on large n;
  or a huge distinct-ID count makes `max_possible = log2|Σ|` normalisation
  swamp the entropy features (everything reads as RANDOM regardless of structure).
- **Implemented:** `analyze_file` + CLI `--file` (the read-only tap); `test_scale.py`
  (20k growing-ID stream + huge-alphabet structured stream + file ingestion).
- **Test:** 20k stream analysed in **< 0.5 s** — performance hypothesis ✅.
- **Marked:** ⚠️ Refuted-in-part — the **semantic** failure mode fired exactly as
  predicted: a symbol recurring at a *perfectly regular period* but with churning
  successors (a periodic marker amid churn) classified RANDOM,
  because the engine only recognised anchors via transition-determinism, never pure
  positional periodicity. **Fix:** added a strictly-gated `periodic_anchor_strength`
  feature (regularity × span, CV/0.3 gate) that counts as structure (lowers RANDOM)
  and reinforces ENGINEERED. Worked examples held (Example 2's drifting X has CV 0.27
  → contributes ~0.08, far below the flip threshold); the big-alphabet stream now
  reads ENGINEERED. Performance unaffected.

---

## Iteration 9 — Periodic anchors get the ANCHOR *role* (honest roles)

- **Hypothesis:** After iter 8 the *classifier* honours periodicity but the *role
  assigner* still calls a periodic-but-high-entropy symbol `CONTENT` — so the
  per-symbol roles contradict the verdict (same class of bug as D-005). Teaching
  the role assigner to label a strongly-periodic recurring symbol (count ≥ 3,
  CV ≤ 0.15, span ≥ 0.5) as `ANCHOR` will fix the contradiction *without* moving
  any worked-example role (Example 2's X is already an anchor by entropy; Examples
  1/3/4 have no strongly-periodic high-entropy symbol).
- **Predicted failures if wrong:** Example 4 (degenerate/uniform path) or Example 1
  roles shift, breaking the role-coverage / diversity tests.
- **Implemented:** `_periodic_anchor_symbols` (CV ≤ 0.15, span ≥ 0.5, count ≥ 3) and
  a periodicity clause in the role precedence; regression test.
- **Test:** gate green — TESTS 65/65 ✓, INVARIANTS 11/11 ✓.
- **Marked:** ✅ Confirmed exactly as predicted. `A0` now reports role `ANCHOR`
  (was `CONTENT`), consistent with the ENGINEERED verdict; no worked-example role
  moved (the strict CV gate excludes Example 2's drifting X at CV 0.27).

---

## Iteration 10 — Role-level motif matching (spec §5)

- **Hypothesis:** Detecting motifs as patterns over the *role* sequence
  (`CONTENT→TERMINATOR→ANCHOR` = Terminator Lock, `FRAME…FRAME` = Boundary Frame,
  repeated role n-grams = Modular Block, repeated inter-anchor role segments =
  Anchor-Driven Cycle) will enrich and corroborate the symbol/entropy-based
  detectors. Deduping by motif type (keep max confidence) means no existing
  motif assertion breaks.
- **Predicted failures if wrong:** duplicate motif types double-counted; HYBRID
  bookkeeping miscounts after the merge; a worked-example motif assertion flips.
- **Implemented:** `_role_level_motifs` (terminator lock, boundary frame, modular
  role block, inter-anchor cycle), merged + deduped by type; anchor-cycle gated on
  a genuine low-entropy anchor to preserve C-8; `test_role_motifs.py`.
- **Test:** gate green — TESTS 70/70 ✓, INVARIANTS 11/11 ✓; no duplicate motif
  types in any report.
- **Marked:** ✅ Confirmed. Role-level detectors corroborate the entropy detectors
  without breaking a single existing motif assertion; honesty gate verified by test.

---

## Iteration 11 — Entropy Cascade as a half-vs-half regime split (spec §5.7)

- **Hypothesis:** Comparing mean entropy of the first vs second half of the stream
  detects a "structure → noise" (or noise → structure) regime shift that the
  existing monotonic-run cascade misses on long streams — a natural health signal.
  Deduping with the monotonic detector keeps one `ENTROPY_CASCADE` motif.
- **Predicted failures if wrong:** a worked example (n=10–12) trips the split and
  gains a spurious cascade; threshold too low → false positives on noisy-but-
  stationary streams.
- **Implemented:** `_entropy_regime_split` (half-vs-half, rel ≥ 0.35, n ≥ 6),
  deduped into one `ENTROPY_CASCADE`; `test_regime_split.py`.
- **Test:** gate green — TESTS 74/74 ✓, INVARIANTS 11/11 ✓; structure→noise stream
  fires, stationary stream does not, worked examples unchanged.
- **Marked:** ✅ Confirmed exactly as predicted.

---

## Iteration 12 — Windowed regime timeline

- **Hypothesis:** A long live stream is better measured as a *timeline* of regimes
  than one global verdict. `analyze_windows(seq, window, step)` will classify each
  window and report where the regime shifts — composing cleanly with §5.7 and
  giving live/long-stream measurement a per-window health trace.
- **Predicted failures if wrong:** off-by-one window spans at the tail; a final
  short window destabilising the classifier; empty input.
- **Implemented:** `analyze_windows(seq, window, step)` → per-window class +
  `change_points` + dominant regime; `test_windows.py`.
- **Test:** gate green — TESTS 80/80 ✓, INVARIANTS 11/11 ✓.
- **Marked:** ✅ Confirmed. Windows tile the stream with no gaps, the tail window
  is handled, and a structure→noise stream surfaces a regime change point.

> **Cycle 1 shipped** (iterations 10–12) → PR #3 → merged. Autonomous loop:
> 3 iterations per PR, gate green at every step.

---

## Iteration 13 — JSON-safe spec output

- **Hypothesis:** The spec dict's `transitions` uses `(from, to)` tuple keys, which
  `json.dumps` rejects. A `json_safe=True` mode (and a `to_json_safe` helper) that
  renders those keys as `"FROM->TO"` strings makes the facade serialisable without
  disturbing the default (spec-literal) shape.
- **Predicted failures if wrong:** the existing `test_role_level_transition_matrix`
  (expects tuple keys) breaks if I change the default; round-trip mismatch.
- **Implemented:** `to_json_safe` + `analyze_sequence(json_safe=True)` (stringify
  transition keys as `"FROM->TO"`); `test_json_safe.py`.
- **Test:** gate green — TESTS 84/84 ✓, INVARIANTS 11/11 ✓; default keeps tuple
  keys (spec-literal), `json.dumps` succeeds with the flag.
- **Marked:** ✅ Confirmed; no existing test disturbed (default unchanged).

---

## Iteration 14 — Permutation null-model significance

- **Hypothesis:** A permutation test — shuffle the stream (preserving symbol
  frequencies, destroying order), recompute an order-sensitive *structuredness*
  scalar, and compare — yields a p-value that is **small for genuinely structured
  streams** (Example 1) and **~1 for order-free ones** (Example 3, all distinct).
  This separates real structure from chance — the discipline any fragile gauge needs.
- **Predicted failures if wrong:** structuredness scalar is order-invariant (then
  shuffling changes nothing and everything reads non-significant); Example 3's
  all-distinct stream has 0 structure in both real and shuffled → p-value
  degenerate (handle the "no structure either way" case explicitly).
- **Implemented:** `significance.py` (`structure_significance`, permutation test on
  an order-sensitive structuredness scalar, add-one-smoothed p-value);
  `test_significance.py`.
- **Test:** gate green — TESTS 88/88 ✓, INVARIANTS 11/11 ✓; structured stream
  p < 0.05 & significant, all-distinct stream not significant, deterministic by seed.
- **Marked:** ✅ Confirmed exactly as predicted, including the order-free guard.

---

## Iteration 15 — Verdict stability metric

- **Hypothesis:** A verdict's robustness can be read two cheap ways: the *margin*
  between the top two class scores, and a *jackknife* (drop one token at a time;
  what fraction keep the same label). A clear engineered/random case will be
  "robust"; a near-tie will be "fragile". This is the direct readout wanted for
  a seed-fragile gauge.
- **Predicted failures if wrong:** jackknife too expensive on long streams (sample
  it); n ≤ 2 has no meaningful perturbation (special-case to robust).
- **Implemented:** `stability.py` (`verdict_stability`: score margin + sampled
  jackknife → robust/marginal/fragile); `test_stability.py`.
- **Test:** gate green — TESTS 93/93 ✓, INVARIANTS 11/11 ✓.
- **Marked:** ✅ Confirmed; deterministic by seed, short-sequence convention holds.

> **Cycle 2 shipped** (iterations 13–15) → PR #4 → merged. The instrument now also
> reports *whether to trust its own verdict* (significance + stability) — the
> interpretation discipline a fragile gauge needs.

---

## Iteration 16 — `measure()`: one full instrument readout

- **Hypothesis:** A single `measure(stream)` that bundles the verdict + confidence
  + roles + motifs + entropy + (opt-in) significance / stability / windowed
  timeline into one JSON-safe dict makes the instrument usable in one call —
  reusing a single engine run for the base so it isn't wasteful.
- **Predicted failures if wrong:** double-running the pipeline for the base dict;
  non-JSON values leaking (tuple transition keys) into the bundled output.
- **Implemented:** `measure()` (single engine run for the base; opt-in
  significance/stability/timeline); `test_measure.py`.
- **Test:** gate green — TESTS 97/97 ✓, INVARIANTS 11/11 ✓; base readout is
  JSON-safe, opt-ins attach correctly.
- **Marked:** ✅ Confirmed as predicted.

---

## Iteration 17 — CLI surface for the full instrument

- **Hypothesis:** Adding `--spec`, `--measure`, `--windows N`, `--significance N`,
  `--stability` output modes (composing with `--file`/`--text`/stdin) exposes every
  capability from the command line without disturbing the default report mode.
- **Predicted failures if wrong:** flag precedence ambiguity; the default
  `--json`/human path regresses; argv parsing breaks an existing invocation.
- **Implemented:** `--spec/--measure/--windows/--significance/--stability` output
  modes; `test_cli.py` exercising each via `main(argv)`.
- **Test:** gate green — TESTS 105/105 ✓, INVARIANTS 11/11 ✓; default report path
  unchanged.
- **Marked:** ✅ Confirmed; every capability is reachable from the command line.

---

## Iteration 18 — Documentation capstone

- **Hypothesis:** A `docs/MEASUREMENT.md` guide (how to point the instrument at
  another program's stream, interpret significance/stability/timeline) plus README
  and module-doc updates makes the full instrument discoverable. Verified by the
  gate staying green and the docs reflecting the shipped API.
- **Predicted failures if wrong:** docs drift from the actual API surface.
- **Implemented:** `docs/MEASUREMENT.md`; README capability table + interrogation
  examples; module-doc rows for `significance.py` / `stability.py` / `analyzer.py`.
- **Test:** gate green — TESTS 105/105 ✓, INVARIANTS 11/11 ✓.
- **Marked:** ✅ Confirmed; docs match the shipped surface.

> **Cycle 3 shipped** (iterations 16–18) → PR #5 → merged.

---

## Loop status: STABLE GREEN — three autonomous PR cycles complete

18 iterations total, gate green at every commit point, **105 tests + 11
invariants**. Across three merged PR cycles the engine went from a methodology
document to a **spec-conformant, self-interrogating, universal measurement
instrument**:

- builds (1–6): the pipeline, honest motifs, robust roles, fuzzed invariants,
  proven architecture seams.
- measurement (7–9): spec facade, ID-stream scale, periodic-anchor recognition.
- enrichment (10–12): role-level motifs, regime split, windowed timeline.
- discipline (13–15): JSON-safe output, permutation significance, verdict stability.
- usability (16–18): `measure()`, full CLI surface, measurement guide.

Still **zero coupling** to any source system (D-008): it measures, it never reaches
in. Next candidate hypotheses: streaming/incremental window updates; a `compare()`
for two streams (regime A/B test); confidence calibration against labelled corpora.

---

## Loop status: STABLE GREEN (measurement phase)

9 iterations, gate green at every commit point. The engine is now a
**spec-conformant, standalone universal instrument**: `analyze_sequence()` emits
Mark's exact dict; `analyze_file()` / `--file` taps a captured stream from any
source; it ingests 20k-token growing-ID streams in < 0.5 s and recognises periodic
structure (periodic markers) that pure transition entropy misses — all
with **zero coupling** to any source (pure measurement, per the agreed boundary).

Next candidate hypotheses, when work resumes:

- H10: role-level motif matching (the spec's `A→T→C→X→A` cycle / `C→X→A` terminator
  lock as role-string patterns), augmenting the entropy-based detectors.
- H11: an `Entropy Cascade` first-half-vs-second-half regime split (spec §5.7) — a
  natural health signal for a stream that degrades from structure into noise.
- H12: a streaming/incremental mode so a long live stream can be measured in
  windows rather than all at once.

---

## Iteration 19 — Real-data validation on the Voynich manuscript (Phase 2)

First test on a real, large, externally-sourced corpus: the full Takahashi/EVA
transliteration of the Voynich manuscript (40,377 words / 191,020 glyphs, 22
glyphs), pulled from voynich.nu (LSI IVTFF). The manuscript is the project's
founding use-case and a known-structured text (established scholarship).

- **Hypothesis:** the instrument will confirm the manuscript is structured
  (significant, non-random).
- **Result — FAILED at scale (the important finding):** on the full glyph stream
  the significance test reported **not significant (p=0.36)**, with observed
  structuredness (0.029) *below* its own shuffled baseline (0.094) — i.e. it
  could not tell real Voynich from random noise (random-glyph control: obs 0.006).
- **Diagnosis:** the structuredness scalar was `max(modular, cluster, anchor_cycle,
  periodic)` — all blind to **transition / which-follows-which structure**, which
  is exactly where Voynich's (and natural language's) structure lives. The earlier
  encouraging 244-char result was a small-n artifact (periodicity firing by chance).
- **Fix:** add the order-sensitive `predictability` term (mean dominant-transition
  probability) to the structuredness scalar. Shuffling destroys it, so the
  permutation test stays valid. Regression test added (`test_markov_...`).
- **Confirmation (recorded, 20k-glyph sample, 200 trials):**

  | stream | significant | p | observed | shuffled |
  |---|---|---|---|---|
  | Voynich glyphs | **True** | **0.0050** | 0.445 | 0.196 |
  | Voynich words | False | 0.44 | 0.805 | 0.826 |
  | random control | False | 0.91 | 0.059 | 0.060 |

- **Marked:** ✅ Fixed and validated. The instrument now independently confirms
  Voynich is structured (p=0.005) with a *computed* p-value, correctly rejects the
  random control (p=0.91), and finds word-*order* insignificant — consistent with
  the structure being morphological (sub-word), the core of Mark's method.
- **Measured cadence reality-check** (turns asserted numbers into real ones):
  37.8% of words end `-y`, 16.4% `-dy`, 10.1% `-edy`, 9.3% `-aiin`, 3.3% `-daiin`;
  top words `n`(1232), `daiin`(849), `ol`(659), `chedy`(554), `aiin`(544). Massive,
  unambiguous suffix regularity — the structure is real and now detectable.
- **Surprise → next:** the *classifier label* still mislabels Voynich glyphs as
  `NATURAL` (the label, unlike significance, has no transition term yet) — Phase 2.2.
  Word-order significance is weak (distinct-ratio) — also 2.2.

