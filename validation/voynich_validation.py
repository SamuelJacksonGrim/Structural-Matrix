#!/usr/bin/env python3
"""Validate the Structural Matrix on the real Voynich manuscript.

Fetches the Takahashi/EVA transliteration (LSI IVTFF, voynich.nu), parses the
complete `;H` transcription, and runs the instrument's significance test on the
glyph stream, the word stream, and a random control.

    python validation/voynich_validation.py [--sample 20000] [--trials 200]

This is reproducible, externally-sourced ground truth: the Voynich text is a
known-structured corpus, so a correct instrument must find the glyph stream
significant and the random control not.
"""
from __future__ import annotations

import argparse
import os
import re
import random
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from structural_matrix import structure_significance  # noqa: E402

SOURCE = "http://www.voynich.nu/data/beta/LSI_ivtff_0d.txt"
CACHE = os.path.join(os.path.dirname(__file__), "voynich_raw.txt")


def load_raw() -> str:
    if not os.path.exists(CACHE):
        print(f"fetching {SOURCE} ...")
        with urllib.request.urlopen(SOURCE) as r:  # respects HTTP(S)_PROXY env
            open(CACHE, "wb").write(r.read())
    return open(CACHE, encoding="utf-8", errors="ignore").read()


def parse_words(raw: str) -> list[str]:
    """Takahashi (;H) lines only; strip IVTFF markup; drop unreadable tokens."""
    words: list[str] = []
    for line in raw.splitlines():
        if ";H>" not in line:
            continue
        text = line.split(">", 1)[1]
        text = re.sub(r"\{[^}]*\}", "", text)
        text = re.sub(r"<[^>]*>", "", text)
        text = text.replace("!", ".").replace(",", ".")
        for tok in text.strip().split("."):
            tok = tok.strip()
            if tok and not re.search(r"[?*%@\d]", tok):
                words.append(tok)
    return words


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=20000, help="tokens for the permutation test")
    ap.add_argument("--trials", type=int, default=200)
    args = ap.parse_args()

    words = parse_words(load_raw())
    glyphs = list("".join(words))
    rng = random.Random(42)
    alpha = sorted(set(glyphs))
    control = [rng.choice(alpha) for _ in range(len(glyphs))]

    print(f"Corpus: {len(words):,} words | {len(glyphs):,} glyphs | "
          f"{len(set(words)):,} unique words | {len(alpha)} glyphs")
    print(f"Permutation test: sample={args.sample:,} trials={args.trials}\n")
    print(f"{'stream':22} {'significant':11} {'p':>7} {'observed':>9} {'shuffled':>9}")
    for name, seq in [("Voynich glyphs", glyphs), ("Voynich words", words),
                      ("random control", control)]:
        s = structure_significance(seq[:args.sample], trials=args.trials)
        print(f"{name:22} {str(s['significant']):11} {s['p_value']:>7.4f} "
              f"{s['observed_structuredness']:>9.3f} {s['mean_shuffled_structuredness']:>9.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
