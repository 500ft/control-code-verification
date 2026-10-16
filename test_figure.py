"""The core-qualification figure shows only stored traces, and its words live in the caption.

These checks need matplotlib, which CI does not install; they skip there and
run wherever the figure can be generated: ``venv/bin/python -m pytest``.
"""
import csv
import hashlib
import json
from pathlib import Path

import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")
from matplotlib.text import Text  # noqa: E402

import figure_style as style  # noqa: E402
import plot  # noqa: E402

ROOT = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def built():
    data, spec = plot.load()
    fig = plot.figure(data, spec)
    fig.canvas.draw()
    yield data, spec, fig
    matplotlib.pyplot.close(fig)


def stored(variant, trace, field):
    """One column of the committed trace CSV, read independently of plot.load."""
    return [float(r[field]) for r in csv.DictReader(plot.SOURCE.open())
            if r["variant"] == variant and r["trace"] == trace]


def test_lines_carry_stored_traces(built):
    _, spec, fig = built
    for col, variant in enumerate(spec["variants"]):
        top, bottom = fig.axes[col], fig.axes[2 + col]
        intent, c, clamp = top.lines
        assert list(intent.get_xdata()) == stored(variant, "reversal", "time_s")
        assert list(intent.get_ydata()) == stored(variant, "reversal", "intent_rad_s")
        assert list(c.get_ydata()) == stored(variant, "reversal", "c_rad_s")
        assert c.get_marker() == "o" and clamp.get_marker() == "x"
        flagged = [r for r in csv.DictReader(plot.SOURCE.open())
                   if r["variant"] == variant and r["trace"] == "reversal" and r["branch_issue"] == "True"]
        assert list(clamp.get_xdata()) == [float(r["time_s"]) for r in flagged]
        assert list(clamp.get_ydata()) == [float(r["c_rad_s"]) for r in flagged]
        error, bound = bottom.lines
        assert list(error.get_ydata()) == stored(variant, "constant_unsaturated", "abs_error_rad_s")
        assert list(bound.get_ydata()) == stored(variant, "constant_unsaturated", "bound_rad_s")
        assert bottom.get_yscale() == "log"
        for ax in (top, bottom):
            assert {line.get_color() for line in ax.lines} == {style.INK}


def test_canvas_holds_only_axes_text_panel_letters_and_legend(built):
    _, _, fig = built
    printed = {t.get_text() for t in fig.findobj(Text) if t.get_visible() and t.get_text().strip()}
    allowed = {f"({c})" for c in plot.LETTERS} | {plot.XLABEL, *plot.YLABELS}
    allowed |= {s["label"] for s in style.SERIES.values()}
    allowed |= {t.get_text() for ax in fig.axes for t in ax.get_xticklabels() + ax.get_yticklabels()}
    assert printed <= allowed, printed - allowed
    assert len(fig.legends) == 1 and not any(ax.get_legend() for ax in fig.axes)


def test_nothing_printed_touches_anything(built):
    _, _, fig = built
    assert style.audit(fig) == []


def test_caption_matches_data_file_and_readme(built):
    data, spec, _ = built
    text = plot.caption(data, spec)
    assert text == plot.STEM.with_suffix(".caption.md").read_text().strip()
    assert "256 steps of dt = 1/32 s, input -8 rad/s, then +8 rad/s from t = 4 s" in text
    assert "2 steps per variant (t = 2 s and t = 5 s)" in text
    assert "64 steps of dt = 1/32 s at 0.5 rad/s" in text
    assert "at least 324 times (zero-reset) and 897 times (tracking-reset)" in text
    squash = lambda s: " ".join(s.split())
    assert squash(text) in squash((ROOT / "README.md").read_text())


def test_manifest_records_committed_files():
    manifest = json.loads((plot.OUT / "figure.json").read_text())
    assert {name: sha(plot.OUT / name) for name in manifest["outputs"]} == manifest["outputs"]
    assert manifest["figure_sha256"] == manifest["outputs"]["core-qualification.png"]
    assert manifest["source_sha256"] == sha(plot.SOURCE)
    assert manifest["config_sha256"] == sha(plot.CONFIG)
    assert manifest["generator_sha256"] == sha(ROOT / "plot.py")
    assert manifest["style_helper_sha256"] == sha(ROOT / "figure_style.py")
