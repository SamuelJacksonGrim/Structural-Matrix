"""Windowed regime timeline (analyze_windows)."""

import pytest

from structural_matrix import analyze_windows


def test_windows_cover_the_stream_without_gaps():
    seq = list("ABCDEFGHIJ")  # 10 tokens
    r = analyze_windows(seq, window=4)
    spans = [w["span"] for w in r["windows"]]
    assert spans[0] == [0, 3]
    # Non-overlapping windows tile the stream; last window covers the tail.
    assert spans[-1][1] == 9
    assert r["n_windows"] == 3  # [0-3], [4-7], [8-9]


def test_regime_change_point_detected():
    # Structured first, random second -> at least one regime change across windows.
    structured = ["A", "B"] * 20
    noisy = list("QWERTYUIOPASDFGHJKLZ" * 2)
    r = analyze_windows(structured + noisy, window=10)
    labels = [w["classification"] for w in r["windows"]]
    assert len(set(labels)) >= 2
    assert r["regime_summary"]["change_points"]  # non-empty


def test_overlapping_step():
    r = analyze_windows(list("A" * 20), window=8, step=4)
    assert r["step"] == 4
    assert r["windows"][0]["span"] == [0, 7]
    assert r["windows"][1]["span"][0] == 4


def test_dominant_regime_reported():
    r = analyze_windows(["A", "B"] * 40, window=8)
    assert r["regime_summary"]["dominant"] in {
        "ENGINEERED",
        "CONSTRUCTED",
        "NATURAL",
        "RANDOM",
    }


def test_invalid_window_raises():
    with pytest.raises(ValueError):
        analyze_windows("A B C", window=0)


def test_empty_stream_yields_no_windows():
    r = analyze_windows("", window=5)
    assert r["n_windows"] == 0
    assert r["regime_summary"]["dominant"] is None
