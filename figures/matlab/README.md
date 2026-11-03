# MATLAB figure and table sources

These scripts draw the core-qualification figure and write the observational
result tables as LaTeX. They read only committed files. Python still does all
computation; MATLAB only draws.

## Regenerate

From the repository root, with MATLAB R2025b:

```sh
matlab -batch "addpath('figures/matlab'); render_figures"
python3 plot.py
```

`render_figures` writes:

| Output | Script | Inputs |
| :--- | :--- | :--- |
| `figures/core-qualification.pdf`, `.png` (300 dpi) | `make_core_qualification.m` | `evidence/traces.csv`, `spec.json` |
| `figures/observational-stages.tex`, `-strata.tex`, `-classes.tex` | `make_observational_tables.m` | `evidence/observational/pilot-summary.json`, `campaign-summary.json`, `campaign/observational-design.json` |

`python3 plot.py` then rewrites `figures/core-qualification.caption.md` and
the manifest `figures/figure.json`. It checks every caption statement against
the traces first.

## Typeset the tables

Each `.tex` file is a booktabs and siunitx `tabular` fragment. To make the PDF
and the 300-dpi PNG, copy a fragment to `figures/matlab/fragment.tex` and run:

```sh
cd figures/matlab
lualatex table_page.tex
pdftoppm -r 300 -png -singlefile table_page.pdf ../observational-stages
mv table_page.pdf ../observational-stages.pdf
```

The committed PDFs were built with Tectonic from the same preamble.
`python3 campaign/render_summary.py` writes
`evidence/observational/table.md`, which shows each PNG with its Markdown
table under it. `python -m pytest test_figure.py` checks that the typeset
numbers match that Markdown table.

## Style

`fig_style.m` sets LaTeX text, Computer Modern type, the 9/8/7 pt size ladder
and the MATLAB default blue and orange. `export_pair.m` writes the vector PDF
and the 300-dpi PNG. Blue marks exact arithmetic (intent and its bound) and
orange marks compiled C. Hollow circles mark steps whose branch requirement
stays open. Grey dotted lines are the rate clamp.
