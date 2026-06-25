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
RFE-Core2 measurement use-case were introduced.)

---

## Iteration 7 — Spec-conformant facade (`analyze_sequence`)

Context: `docs/DEVELOPER_SPEC.md` (Mark's spec) pins an exact public API and output
contract. Goal is to satisfy it *additively* — a facade over the existing engine —
without disturbing the proven internals, and to keep the engine a **standalone
universal instrument** (no RFE-Core2 coupling; pure measurement).

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
program (e.g. RFE-Core2) it should ingest that program's emitted stream directly —
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
  successors (an RFE-style periodic sacred-anchor amid reaping) classified RANDOM,
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

## Loop status: STABLE GREEN (measurement phase)

9 iterations, gate green at every commit point. The engine is now a
**spec-conformant, standalone universal instrument**: `analyze_sequence()` emits
Mark's exact dict; `analyze_file()` / `--file` taps a captured stream from any
source; it ingests 20k-token growing-ID streams in < 0.5 s and recognises periodic
structure (sacred-anchor-style markers) that pure transition entropy misses — all
with **zero coupling** to RFE-Core2 (pure measurement, per the agreed boundary).

Next candidate hypotheses, when work resumes:

- H10: role-level motif matching (the spec's `A→T→C→X→A` cycle / `C→X→A` terminator
  lock as role-string patterns), augmenting the entropy-based detectors.
- H11: an `Entropy Cascade` first-half-vs-second-half regime split (spec §5.7) — a
  natural health signal for a stream that degrades from structure into noise.
- H12: a streaming/incremental mode so a long live stream can be measured in
  windows rather than all at once.

