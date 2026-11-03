"""The MATLAB figure, its caption, its manifest and the typeset tables match the committed data.

MATLAB cannot run in CI, so these checks read the committed outputs and the
MATLAB sources. They need only pytest: ``python -m pytest test_figure.py``.
"""
import json
import re
from pathlib import Path

import pytest

import plot

ROOT = Path(__file__).resolve().parent
FIGURES = ROOT / "figures"


@pytest.fixture(scope="module")
def loaded():
    return plot.load()


def test_caption_matches_data_file_and_readme(loaded):
    data, spec = loaded
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
    assert manifest == plot.manifest()
    assert set(manifest["outputs"]) == {"core-qualification.png", "core-qualification.pdf"}


def test_matlab_generator_reads_the_plotted_traces():
    source = plot.GENERATOR.read_text()
    assert "'evidence', 'traces.csv'" in source and "'spec.json'" in source
    for trace in plot.TRACES:
        assert f'"{trace}"' in source
    assert "branch_issue" in source


def numbers(cells):
    return [float(c.replace(",", "")) for c in cells]


def tex_rows(name):
    """Data rows of a MATLAB-written tabular fragment, as lists of cells."""
    lines = (FIGURES / name).read_text().splitlines()
    body = lines[lines.index("\\midrule") + 1:lines.index("\\bottomrule")]
    return [[c.strip() for c in line[:-2].split("&")] for line in body if line != "\\midrule"]


def md_tables():
    tables, current = [], None
    for line in (ROOT / "evidence/observational/table.md").read_text().splitlines():
        if line.startswith("|"):
            if current is None:
                current = []
                tables.append(current)
            current.append([c.strip() for c in line.strip("|").split("|")])
        else:
            current = None
    return [t[2:] for t in tables]  # drop header and alignment rows


def plain(cell):
    return re.sub(r"\\texttt\{(.*)\}", r"\1", cell).replace("\\_", "_")


def test_typeset_tables_match_markdown_tables():
    stages, strata, classes = md_tables()
    # Stage table: columns regrouped as traces, steps, run.
    order = [0, 4, 1, 2, 3, 5, 6, 7]
    tex = tex_rows("observational-stages.tex")
    assert [r[0] for r in tex] == [r[0] for r in stages]
    for t, m in zip(tex, stages):
        assert numbers(t[1:]) == [numbers(m[1:])[i] for i in order]
    tex = tex_rows("observational-strata.tex")
    variant = None
    assert len(tex) == len(strata)
    for t, m in zip(tex, strata):
        variant = plain(t[0]) or variant
        assert f"{variant}/{plain(t[1])}" == m[0]
        assert numbers(t[2:]) == numbers(m[1:])
    tex = tex_rows("observational-classes.tex")
    assert [plain(r[0]) for r in tex] == [r[0] for r in classes]
    for t, m in zip(tex, classes):
        assert numbers(t[1:]) == numbers(m[1:])


def test_typeset_tables_have_images():
    for stem in ("observational-stages", "observational-strata", "observational-classes"):
        for ext in (".tex", ".pdf", ".png"):
            assert (FIGURES / f"{stem}{ext}").is_file(), stem + ext
