# 9 · Decision Log — the diary

> What choices were made, and *why*? (so nobody re-argues them)

Newest decisions at the bottom. Each entry: the decision, the context, the
alternatives weighed, and the consequence. Referenced by ID from the other docs.

---

## D-001 · Zero runtime dependencies (pure standard library)

- **Context:** The engine does entropy, transition counting and small-vector math.
- **Decision:** Implement everything on the Python ≥ 3.9 standard library; no
  `numpy`/`scipy`.
- **Alternatives:** `numpy` for vector ops (faster, familiar).
- **Why:** Portability to locked-down CI/web sandboxes, instant install, no
  supply-chain surface. Data sizes are small enough that pure Python is ample.
- **Consequence:** Trivial to run anywhere; a future hot path could add an
  optional accelerated backend behind the existing interfaces if ever needed.

## D-002 · Injection over plugin discovery

- **Context:** Stages need to be swappable.
- **Decision:** Pass implementations into `StructuralMatrix.__init__`; no entry-
  point/registry auto-loading.
- **Alternatives:** A plugin registry that discovers stages by name.
- **Why:** Explicit, debuggable, no import-time magic; the caller sees exactly
  what runs.
- **Consequence:** Extension = construct-and-pass. Documented in
  [06 · Interfaces](06-INTERFACES.md).

## D-003 · `typing.Protocol` instead of abstract base classes

- **Decision:** Stage contracts are `@runtime_checkable` Protocols.
- **Alternatives:** `abc.ABC` with `@abstractmethod`.
- **Why:** Structural typing means a custom stage needs no import of ours and no
  subclassing — zero coupling — while `isinstance` still works where handy.
- **Consequence:** Third-party stages are plain classes with the right method.

## D-004 · Entropy in bits (`log₂`), adaptive thresholds

- **Decision:** Local entropy uses base-2 logs; `τ_A`, `τ_T`, `τ_C` are derived
  per sequence from its own entropy spread (methodology §5).
- **Alternatives:** Natural log; fixed global thresholds.
- **Why:** Bits are interpretable (a fair coin = 1 bit); adaptive thresholds let
  one engine work across wildly different alphabets without tuning.
- **Consequence:** The contract is about *how* thresholds adapt, not fixed values
  (see [03 · Contracts](03-CONTRACTS.md)).

## D-005 · Single source of truth for the anchor entropy ceiling

- **Context (loop iteration 2):** The motif detector and the classifier each had
  their own notion of "low entropy", and Example 2 emitted a false
  `Anchor-Driven Cycle` that the classifier (correctly, with a stricter rule) did
  not act on — an inconsistent, dishonest report.
- **Decision:** Hoist `ANCHOR_ENTROPY_CEIL = 0.5` into `types.py` and have both
  `motifs.py` and `classification.py` import it.
- **Alternatives:** Make `classification` import the constant from `motifs`.
- **Why:** Putting the shared constant in the dependency *sink* (`types`) lets two
  stages agree without depending on each other, preserving the no-sideways-import
  rule (**D-007**/[07 · Dependencies](07-DEPENDENCIES.md)).
- **Consequence:** Motifs can never contradict the verdict (contract **C-8**).

## D-006 · Sequential, deterministic pipeline (no concurrency)

- **Decision:** Run stages strictly in order; no threads/async.
- **Why:** Determinism (contract **C-3**) and readability matter more than speed
  at these data sizes; a 5000-symbol sequence analyses in milliseconds.
- **Consequence:** Reasoning about the system is trivial; reproducibility is free.

## D-007 · Behaviour is computed from symbol transitions, not the numeric SV

- **Context (loop iterations 5–6):** Proving the "mapping-agnostic" claim (C-4)
  revealed that the numeric `SymbolVector` is *not consumed* by any downstream
  stage — `behaviour.py` builds the transition matrix from the raw symbols (`Σ`),
  so ordinal vs frequency vs custom maps change only the reported SV.
- **Decision:** Keep it that way — and name it. The SV is **informational today**
  and a deliberate **seam for future embedding-based behaviour** (where the
  numeric encoding *would* feed a distance/clustering analyzer).
- **Alternatives:** Remove the SV entirely (smaller surface); or wire SV values
  into behaviour now (premature — no current need).
- **Why:** Removing it would discard the methodology's §2 stage and a real
  extension point; wiring it in now would invent behaviour with no validating
  example. Documenting the truth beats hiding a vestige.
- **Consequence:** C-4 holds by construction; the path to embedding-based
  analysis is a new `BehaviourAnalyzer` that reads `SymbolVector.values`.

## D-008 · The engine is a standalone universal instrument (no source coupling)

- **Context:** The engine may be pointed at the output of other programs. The
  tempting move was to build an adapter that couples it to a specific source.
- **Decision:** Keep the engine **domain-agnostic and uncoupled**. To measure
  another program, capture its emitted stream and feed it in read-only
  (`analyze_file` / `--file`). No write-back, no knowledge of the source.
- **Alternatives:** A bidirectional integration wired to a particular source now.
- **Why:** Universality is the whole premise — it eats any symbol sequence and
  ignores meaning. Measurement-as-a-separate-program is the least-foreclosing path:
  the instrument and any source stay independent, nothing is over-committed, and a
  future closed loop remains fully optional. Freezing an integration contract now
  would spend optionality we can't yet justify.
- **Consequence:** The only integration surface is a read-only tap. Any future
  control loop (verdict acting back on a source) is a separate, opt-in seam designed
  against that source's real inputs when known — not inferred today.

## D-009 · Anchors are recognised by periodicity, not only transition-determinism

- **Context (loop iteration 8):** A symbol recurring at a perfectly regular period
  but with churning successors (a periodic sacred-marker amid reaping) was
  classified RANDOM, because the engine only saw anchors via low transition
  entropy.
- **Decision:** Add a strictly-gated `periodic_anchor_strength` feature (regularity
  × span) to both the classifier and the role assigner, so positional periodicity
  counts as structure independent of transition entropy.
- **Why:** The methodology itself defines anchors as symbols that "repeat at
  relatively regular intervals" (§3.1) — pure periodicity was a real gap, and it is
  exactly the shape a rhythmic structural marker takes in a live ID stream.
- **Consequence:** Periodic markers read as ANCHOR (role) and pull the verdict
  toward ENGINEERED (structured), not RANDOM. The strict CV gate (≤ 0.15 for roles,
  CV/0.3 weighting for the score) keeps drifting/floating anchors out, so no
  worked-example classification or role moved.

---

### How decisions get made here

Decisions emerge from the autonomous loop (`loop/DEVLOG.md`): a hypothesis is
tested, a surprise is observed, and if it changes a durable choice it is recorded
here with an ID so it is not silently re-litigated. D-005 and D-007 came directly
from loop iterations 2 and 5–6 respectively.
