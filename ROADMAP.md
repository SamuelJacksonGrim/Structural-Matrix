# Structural Matrix — Roadmap

A behaviour-first structural analysis engine: read any symbol stream, report its
structure (and whether to trust that report), ignoring meaning.

**Methodology & developer spec:** Mark Thomas ("Rogue Android Architect") — see
[`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) and [`docs/DEVELOPER_SPEC.md`](docs/DEVELOPER_SPEC.md).
**Sibling system:** RFE-Core2 (the symbolic ecology this can measure).

Status legend: ✅ done · 🔜 next · 🔭 planned · 💭 idea

---

## Phase 0 — Foundation ✅
The methodology turned into a real program.

- ✅ Pipeline `S → SV → BV → SCV → Roles → Motifs → Classification` (pure stdlib).
- ✅ Injectable stages behind `Protocol` interfaces; deterministic; zero deps.
- ✅ The 10 architecture artifacts (`docs/01–09` + README) and the autonomous loop.

## Phase 1 — Measurement instrument ✅
Made it a standalone, spec-conformant, self-interrogating instrument.

- ✅ Spec facade `analyze_sequence` (Mark's exact output contract) + `analyze_file` tap.
- ✅ Scales to 20k-token growing-ID streams; periodic-anchor recognition.
- ✅ Role-level motifs, entropy-cascade regime split, windowed regime timeline.
- ✅ **Significance** (permutation null model) and **verdict stability** — the
  discipline layer that says when *not* to trust the label.
- ✅ `measure()` one-shot readout + full CLI surface + `docs/MEASUREMENT.md`.

## Phase 2 — Empirical validation & calibration 🔜 (we are here)
The real-data battery exposed the headline gap: **the 5-way label is miscalibrated,
while the significance test is the trustworthy signal.** This phase fixes that.

- 🔜 **Reframe the headline output**: lead with significance + structuredness;
  demote the 5-way label to advisory. (Small change; the data already justifies it.)
- 🔜 **Fix the label artifacts** found in testing:
  - distinct-ratio dominance → short high-vocabulary text mislabelled `RANDOM`
    (normalise for length / vocabulary growth).
  - periodic-anchor over-firing → ordinary text mislabelled `ENGINEERED`.
  - long-period structure missed → Fibonacci mod 10 (period 60) read `NATURAL`
    (detect repeated templates longer than the current n-gram cap).
- 🔜 **Calibrate against ground truth**: a validation corpus with known labels —
  real genomes (FASTA), full natural-language books, music (MIDI note streams),
  system/network logs, and known-random baselines. Track accuracy as a metric.
- 🔭 Close the significance blind spot for self-similar binary structure
  (Thue–Morse survived shuffling statistically).

## Phase 3 — RFE-Core2 measurement 🔭
The actual target: point the read-only tap at RFE-Core2's emitted stream.

- 🔭 Ingest a captured stable-ID / token-class stream; report the regime timeline.
- 🔭 Map emergent roles (anchor/terminator/content) against RFE-Core2's *declared*
  classes — surface mismatches as signals.
- 💭 Optional, opt-in closed loop later (verdict → reaper guidance). Stays
  decoupled by default (decision D-008): the instrument measures, never reaches in.

## Phase 4 — Access & UX 🔭
Make it usable by non-developers (per the project vision).

- 🔭 A simple UI/UX: upload a file or paste data → get the readout (regime,
  significance, stability, role map, timeline).
- 💭 Packaged/contained distribution so it "just runs" for an end user.

## Phase 5 — Hardening & release 💭
- 💭 Performance pass for very large streams; optional accelerated backend behind
  the existing interfaces.
- 💭 Versioned output schema + changelog; published package.

---

## Guiding principles (don't re-litigate — see `docs/09-DECISION-LOG.md`)
1. **Universal & uncoupled** — measures any stream, adapts to no source (D-008).
2. **Honest over impressive** — report states; never call noise "structured" (the
   significance/stability layer exists for this).
3. **Deterministic & dependency-free** — reproducible anywhere.
4. **Open at every seam** — extend by substitution, not edits.

## Credits
- **Mark Thomas** — Rogue Android Architect; originator of the Structural Matrix
  methodology and the developer specification; architect of RFE-Core2.
- Project lead: Sam (SolarynVeyr).
- Implementation: built with Claude Code under the autonomous build/test/refine loop.
