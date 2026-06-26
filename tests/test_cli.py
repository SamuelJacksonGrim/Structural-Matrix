"""CLI output modes."""

import json

from structural_matrix.cli import main


def _run(capsys, argv):
    rc = main(argv)
    out = capsys.readouterr().out
    return rc, out


def test_default_human_report(capsys):
    rc, out = _run(capsys, ["--text", "A B B C A B C C C A"])
    assert rc == 0
    assert "CLASS" in out and "Engineered" in out


def test_json_report(capsys):
    rc, out = _run(capsys, ["--text", "A B B C A B C C C A", "--json"])
    d = json.loads(out)
    assert d["classification"]["label"] == "Engineered"


def test_spec_mode_is_json(capsys):
    rc, out = _run(capsys, ["--text", "A B B C A B C C C A", "--spec"])
    d = json.loads(out)
    assert d["classification"] == "ENGINEERED"
    assert all("->" in k for k in d["transitions"])  # json-safe keys


def test_measure_mode(capsys):
    rc, out = _run(
        capsys, ["--text", "A B C A B C A B C", "--measure", "--stability", "--significance", "40"]
    )
    d = json.loads(out)
    assert d["significance"] is not None and d["stability"] is not None


def test_windows_mode(capsys):
    rc, out = _run(capsys, ["--text", " ".join(["A", "B"] * 30), "--windows", "10"])
    d = json.loads(out)
    assert d["n_windows"] >= 1


def test_significance_mode(capsys):
    rc, out = _run(capsys, ["--text", "A B C A B C A B C A B C", "--significance", "50"])
    d = json.loads(out)
    assert "p_value" in d


def test_stability_mode(capsys):
    rc, out = _run(capsys, ["--text", "Q W E R T Y U I O P", "--stability"])
    d = json.loads(out)
    assert d["stability"] in {"robust", "marginal", "fragile"}


def test_chars_flag(capsys):
    rc, out = _run(capsys, ["--text", "AABBC", "--chars", "--spec"])
    d = json.loads(out)
    assert d["symbols"] == ["A", "A", "B", "B", "C"]
