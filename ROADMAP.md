# Structural Matrix — Roadmap

A behaviour-first structural analysis engine: read any symbol stream, report its
structure — *and how much to trust that report* — while ignoring meaning.

- **Methodology & developer spec:** Mark Thomas ("Rogue Architect") — see
  [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) and [`docs/DEVELOPER_SPEC.md`](docs/DEVELOPER_SPEC.md).
- **Sibling system:** RFE-Core2 (a symbolic ecology — a natural source of streams
  to measure; we work from *exported snapshots*, never by cloning the repo).

**Where we are today:** `v0.1` — mechanically complete (105 tests, 11 invariants),
empirically *uncalibrated*. Real-data testing showed the verdict label needs work
and that the significance signal is the most trustworthy output. Phase 2 fixes that.

Status legend: ✅ done · 🔜 next · 🔭 planned · 💭 idea

---

## Phase 0 — Foundation ✅
- Pipeline `S → SV → BV → SCV → Roles → Motifs → Classification` (pure stdlib).
- Injectable stages behind `Protocol` seams; deterministic; zero dependencies.
- The 10 architecture artifacts (`docs/01–09` + README) and the autonomous loop.

## Phase 1 — Measurement instrument ✅
- Spec facade `analyze_sequence` (Mark's exact output contract) + `analyze_file` tap.
- Scales to 20k-token growing-ID streams; periodic-anchor recognition.
- Role-level motifs, entropy-cascade regime split, windowed regime timeline.
- **Significance** (permutation null model) + **verdict stability** — the discipline
  layer that says when *not* to trust the label.
- `measure()` one-shot readout + full CLI surface + `docs/MEASUREMENT.md`.

---

## Phase 2 — Validation & calibration 🔜 **(we are here)**
*Goal: make the headline verdict trustworthy on real data, with measured accuracy
instead of vibes.*

**2.1 Reframe the headline output** 🔜
- Lead `measure()` with **significance + structuredness + stability**; demote the
  5-way label to advisory with an honesty flag ("label unreliable — not significant").
- *Acceptance:* on the real-data battery, the headline never confidently asserts
  structure where significance says p≈1 (random digits, constant token).

**2.2 Fix the label artifacts found in testing** 🔜
- Distinct-ratio dominance → short high-vocabulary text mislabelled `RANDOM`
  (length/vocabulary-aware normalisation).
- Periodic-anchor over-firing → ordinary text mislabelled `ENGINEERED`.
- Long-period blindness → Fibonacci mod 10 (period 60) read `NATURAL`
  (detect repeated templates beyond the current n-gram cap, e.g. via suffix
  structure / autocorrelation).
- *Acceptance:* each previously-wrong battery case lands in a defensible class,
  with worked-example invariants still green.

**2.3 Calibrate against ground truth** 🔜
- Build a small labelled validation corpus + an accuracy harness in the loop:
  real genomes (FASTA), full natural-language books (Gutenberg), music (MIDI note
  streams), system/network logs, ciphers, and known-random baselines.
- Track **accuracy / confusion matrix** as a tracked metric in `loop/check.py`.
- *Acceptance:* a published baseline accuracy number we can improve against.

**2.4 Close the significance blind spot** 🔭
- Thue–Morse (self-similar binary) survived shuffling statistically. Add a
  structure measure that catches self-similarity (e.g. autocorrelation or
  compression-ratio proxy) into the structuredness scalar.

## Phase 3 — Measuring real sources (bring-your-own-stream) 🔭
*Goal: measure RFE-Core2 (and anything else) without ever importing it.*

- **Export contract**: a tiny, documented format for a captured stream — one token
  (stable ID / token class / glyph) per line, optional `step,token` columns. The
  source program writes it; we read it. No coupling (decision **D-008**).
- `analyze_file` / windowed timeline already consume this; add a `--report` that
  emits a shareable summary for a captured snapshot.
- **Role vs declared-class diff**: when the source tags tokens (e.g. RFE-Core2's
  TokenClass), compare emergent role ↔ declared class and surface mismatches.
- 💭 *Opt-in, much later:* a closed loop (verdict → source guidance). Off by
  default; the instrument measures, never reaches in.

## Phase 4 — Access & Experience 🔭
*Goal: a stranger drops in data and gets an honest, understandable read in seconds —
no install, no jargon wall, and it feels good to use.*

**Design principles**
- **Zero friction.** Runs in the browser. Paste text, drag-and-drop a file, or
  click a built-in sample. No account, no setup, nothing uploaded to a server.
- **Plain language first.** Lead with one human sentence:
  *"This looks engineered — clearly structured, and very unlikely to be chance."*
  Confidence as a friendly band (rock-solid / likely / shaky), not a raw float.
- **Show, don't tell.** Visuals that make structure visible at a glance:
  - an **entropy sparkline** across the stream,
  - a **role ribbon** colouring each token by its role (anchor/frame/…),
  - a **regime timeline** bar marking where the structure shifts,
  - a **significance gauge** — your result against the shuffled "chance" cloud.
- **Honesty up front.** When significance is low it says so plainly:
  *"We can't tell this apart from random."* Stability shown beside the verdict.
- **Progressive depth.** "Show the details" expands to motifs, scores, role map,
  the raw `measure()` JSON — for the people who want the math.
- **Inviting onboarding.** Pre-loaded samples (DNA, English, a cipher, random) so a
  first-timer gets the "aha" in one click; gentle empty-state copy.
- **Shareable.** Export the report as an image / JSON, or a link.

**Tech direction (recommended)**
- Static single-page app running the *existing* pure-Python engine in-browser via
  **Pyodide** — no backend, fully private, deployable to GitHub Pages for free.
  (Pure-stdlib + deterministic, decision D-001, is exactly what makes this viable.)
- Fallback: a thin FastAPI service if in-browser proves too heavy for big files.

**Milestones**
- 4.1 — paste/upload → plain-language verdict + significance + stability.
- 4.2 — the four visualisations (sparkline, role ribbon, regime timeline, gauge).
- 4.3 — samples, progressive disclosure, export/share, mobile-friendly layout.
- *Acceptance:* a non-technical person analyses a file and can explain the result
  without reading any docs.

## Phase 5 — Hardening & release 💭
- Performance pass for very large streams (optional accelerated backend behind the
  existing interfaces — no API change).
- Versioned output schema + `CHANGELOG`; published package (PyPI) and the hosted app.
- Optional packaged/contained build so it "just runs" for an end user.

---

## Success metrics (so "is it good?" stops being a vibe)
- **Accuracy** on the labelled validation corpus (Phase 2.3) — tracked over time.
- **Calibration**: when the tool says "significant", it is, ≥ X% of the time.
- **Speed**: < 1 s for 20k tokens (already met); target streaming for 1M+.
- **Usability** (Phase 4): first-time user succeeds unaided.

## Risks & open questions
- The 5-way label may be inherently fuzzy on real data; the significance-first
  reframe (2.1) hedges this.
- Ground-truth labels for "natural vs constructed" are themselves debatable — the
  corpus needs clear, defensible cases.
- Pyodide payload size / big-file performance in-browser (Phase 4 fallback covers it).

## Guiding principles (don't re-litigate — see `docs/09-DECISION-LOG.md`)
1. **Universal & uncoupled** — measures any stream, adapts to no source (D-008).
2. **Honest over impressive** — never call noise "structured".
3. **Deterministic & dependency-free** — reproducible anywhere (and runnable in a browser).
4. **Open at every seam** — extend by substitution, not edits.

## Credits
- **Mark Thomas** — Rogue Architect; originator of the Structural Matrix methodology
  and the developer specification; architect of RFE-Core2.
- Project lead: Sam (SolarynVeyr).
- Implementation: built with Claude Code via the autonomous build/test/refine loop.
