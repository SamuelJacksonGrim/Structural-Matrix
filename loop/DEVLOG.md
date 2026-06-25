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

## Loop status: STABLE GREEN

6 iterations, gate green at every commit point. Headline behaviour (all four
worked examples + 3D override) is locked by both `tests/` and `loop/check.py`
invariants. Next candidate hypotheses, when work resumes:

- H5: frequency-mapping vs ordinal-mapping should not change *classification*
  (mapping-agnostic claim, methodology §2) — assert invariance across mappers.
- H6: an injected custom `Classifier` swaps cleanly via the `interfaces` seam
  (prove the Open/Closed boundary with a stub).
- H7: entropy-cascade detection on a hand-built monotonic ramp.

