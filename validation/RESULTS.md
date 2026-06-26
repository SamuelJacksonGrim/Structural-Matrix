# Validation results

Reproducible runs of the instrument against real, externally-sourced corpora.
Run: `python validation/voynich_validation.py`.

## Voynich manuscript (Takahashi/EVA, LSI IVTFF — voynich.nu) — 2026-06-26

**Corpus:** 40,377 words · 191,020 glyphs · 7,871 unique words · 22 distinct glyphs.
A known-structured text (established scholarship), used here as ground truth.

**Permutation significance test** (20,000-token sample, 200 trials):

| stream | significant | p | observed | shuffled |
|---|---|---|---|---|
| Voynich glyphs | **True** | **0.0050** | 0.445 | 0.196 |
| Voynich words (order) | False | 0.44 | 0.805 | 0.826 |
| random control (same alphabet/length) | False | 0.91 | 0.059 | 0.060 |

**Reading:**
- The glyph stream is **significantly structured** (p = 0.005) — the instrument
  independently confirms the manuscript is not random, with a *computed* p-value.
- The random control is correctly **not significant** (p = 0.91) — no false positive.
- Word *order* is not significant — consistent with Voynich's structure being
  **morphological (sub-word)** rather than in word sequence.

**Measured suffix regularity** (the structure made concrete):
37.8% of words end `-y`, 16.4% `-dy`, 10.1% `-edy`, 9.3% `-aiin`, 3.3% `-daiin`;
most common words `n` (1232), `daiin` (849), `ol` (659), `chedy` (554), `aiin` (544).

**Note (honest):** this result required a fix found *by this very test* — the
original structuredness scalar was blind to transition structure and rated real
Voynich (0.029) no higher than random noise (0.006). See DEVLOG iteration 19.

**Known limitation:** the 5-way *classification label* still calls the glyph
stream `NATURAL` (the label has no transition term yet); significance is the
trustworthy signal. Tracked as roadmap Phase 2.2.
