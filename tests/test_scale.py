"""Scale & ingestion tests — the engine as a standalone instrument for ID streams.

A captured stream from another program (e.g. token / stable IDs) is a long
sequence of integer-like tokens with a large, often *growing* alphabet. These
tests prove the universal instrument ingests that shape without coupling, stays
total, and runs fast.
"""

import random
import time

import pytest

from structural_matrix import analyze_file, analyze_sequence
from structural_matrix.types import StructuralClass


def test_large_growing_id_stream_is_total_and_fast():
    # 20k tokens over a vocabulary that grows as "new IDs are born" — emulating a
    # symbolic ecology where stable_ids accumulate over time.
    rng = random.Random(2026)
    stream = []
    next_id = 0
    live = []
    for step in range(20_000):
        # occasionally birth a new ID; mostly reuse a recent live one
        if not live or rng.random() < 0.03:
            live.append(next_id)
            next_id += 1
            if len(live) > 500:  # bound the working set ("reaping")
                live.pop(0)
        stream.append(str(rng.choice(live)))

    t0 = time.perf_counter()
    result = analyze_sequence(stream)
    elapsed = time.perf_counter() - t0

    assert result["symbols"][:1]  # non-empty
    assert result["classification"] in {
        "NATURAL",
        "ENGINEERED",
        "CONSTRUCTED",
        "RANDOM",
    }
    assert len(result["role_sequence"]) == 20_000
    assert elapsed < 10.0, f"too slow on 20k stream: {elapsed:.2f}s"


def test_huge_distinct_alphabet_does_not_force_random():
    # A structured stream with MANY distinct IDs but a clear repeating template
    # must not be swamped into RANDOM by the large-alphabet entropy normalisation.
    # Template: anchor 'A0' then two unique content IDs, repeated.
    tokens = []
    for k in range(300):
        tokens += ["A0", f"c{2*k}", f"c{2*k+1}"]
    label = analyze_sequence(tokens)["classification"]
    # The recurring 'A0' anchor at a regular period should read as structured,
    # not RANDOM.
    assert label != "RANDOM"


def test_periodic_marker_gets_anchor_role():
    # A symbol on a perfectly regular beat, with unique churning neighbours, must
    # be reported as an ANCHOR — not CONTENT — so the per-symbol roles agree with
    # the (ENGINEERED) verdict.
    tokens = []
    for k in range(300):
        tokens += ["A0", f"c{2*k}", f"c{2*k+1}"]
    r = analyze_sequence(tokens)
    assert r["roles"]["A0"] == "ANCHOR"
    assert r["classification"] == "ENGINEERED"


def test_analyze_file_reads_whitespace_and_newline_streams(tmp_path):
    p = tmp_path / "stream.txt"
    # one token per line (a typical captured log shape)
    p.write_text("\n".join(["A", "B", "B", "C", "A", "B", "C", "C", "C", "A"]))
    result = analyze_file(str(p))
    assert result["classification"] == "ENGINEERED"
    assert result["symbols"] == ["A", "B", "B", "C", "A", "B", "C", "C", "C", "A"]


def test_analyze_file_matches_inline(tmp_path):
    text = "A A B A A B C C A A B"
    p = tmp_path / "s.txt"
    p.write_text(text)
    assert analyze_file(str(p)) == analyze_sequence(text)
