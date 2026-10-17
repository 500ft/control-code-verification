"""Shared figure rules for committed plots: a data-only canvas with the words in a caption.

Plots call ``apply()`` before drawing, ``save()`` to write every format and
``audit()`` to prove that nothing printed touches anything else. Only
presentation lives here; no plotted value is computed in this module.

- The canvas carries data, axes, tick labels, axis labels, panel letters and
  one framed legend. Titles, conditions, outcomes and notes live in the
  caption file written next to the image and in the README under it.
- Series are told apart by line style and marker shape, never by colour, so
  the figure reads the same in greyscale print.
- Type is Computer Modern (matplotlib's bundled ``cmr10``), the same family
  as the Latin Modern used by LaTeX-built figures.
"""
import hashlib
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.text import Text

INK = "black"
# One style per plotted entity in every committed figure.
SERIES = {
    "exact_intent": {"label": "Exact intent", "color": INK, "lw": 1.6, "ls": (0, (4, 3))},
    "compiled_c": {"label": "Compiled C", "color": INK, "lw": 0.8, "ls": "-",
                   "marker": "o", "ms": 3.2, "mew": 0.8, "mfc": INK},
    "clamp_step": {"label": "Step at rate clamp", "color": INK, "ls": "none",
                   "marker": "x", "ms": 7, "mew": 1.1},
    "bound": {"label": "Analytical bound", "color": INK, "lw": 1.0, "ls": (0, (5, 2, 1, 2))},
}

# Three type sizes, chosen by role: axis labels and legend, then panel
# letters, then tick labels.
LABEL_SIZE, LETTER_SIZE, TICK_SIZE = 9, 9, 7
DPI = 600


def apply(salt: str) -> None:
    """Set the shared rcParams. The salt keeps SVG element ids stable."""
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["cmr10"],
        "mathtext.fontset": "cm",
        # cmr10 has no Unicode minus; mathtext tick labels carry a proper one.
        "axes.formatter.use_mathtext": True,
        "axes.unicode_minus": False,
        "font.size": LABEL_SIZE,
        "axes.labelsize": LABEL_SIZE,
        "legend.fontsize": LABEL_SIZE,
        "xtick.labelsize": TICK_SIZE,
        "ytick.labelsize": TICK_SIZE,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.8,
        "axes.edgecolor": INK,
        "legend.frameon": True,
        "legend.fancybox": False,
        "legend.edgecolor": INK,
        "legend.framealpha": 1.0,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.dpi": DPI,
        # Glyphs as paths so the SVG renders the same without cmr10 installed;
        # the salt keeps element ids stable, so reruns give the same bytes.
        "svg.fonttype": "path",
        "svg.hashsalt": salt,
    })


def audit(fig) -> list[tuple[str, str]]:
    """Pairs of printed things whose boxes touch. Empty means the canvas is clean.

    Every drawn text (tick labels inside the view, axis labels, panel letters,
    legend entries) is checked against every other drawn text, against the
    data drawn in each axes and against each legend frame. Data is not checked
    against data: compiled C lying on its intent is the point of the figure.
    Texts inside a legend are not checked against their own frame.
    """
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    legends = list(fig.legends) + [ax.get_legend() for ax in fig.axes if ax.get_legend()]
    owner = {id(child): legend for legend in legends for child in legend.findobj()}
    tick_labels, drawn = set(), []
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            low, high = sorted(axis.get_view_interval())
            slack = 1e-9 * (high - low)
            for tick in axis.get_major_ticks() + axis.get_minor_ticks():
                for label in (tick.label1, tick.label2):
                    tick_labels.add(id(label))
                    if label.get_visible() and label.get_text().strip() and low - slack <= tick.get_loc() <= high + slack:
                        drawn.append(label)
    drawn += [t for t in fig.findobj(Text)
              if id(t) not in tick_labels and t.get_visible() and t.get_text().strip()]
    texts = [(f"text {t.get_text()!r}", t.get_window_extent(renderer).padded(1), owner.get(id(t))) for t in drawn]
    others = [(f"data in {ax.get_ylabel() or 'axes'}", line.get_window_extent(renderer), None)
              for ax in fig.axes for line in ax.lines]
    others += [("legend frame", legend.get_window_extent(renderer), legend) for legend in legends]
    hits = []
    for i, (name_a, box_a, legend_a) in enumerate(texts):
        for name_b, box_b, legend_b in texts[i + 1:] + others:
            if legend_a is not None and legend_a is legend_b:
                continue
            if box_a.overlaps(box_b):
                hits.append((name_a, name_b))
    return hits


def save(fig, stem, formats=("png", "svg")) -> dict[str, str]:
    """Write ``stem.<ext>`` for each format with no timestamps; refuse a touching canvas.

    Returns {file name: sha256} for the figure manifest.
    """
    hits = audit(fig)
    if hits:
        raise ValueError(f"printed items touch: {hits}")
    stem = Path(stem)
    outputs = {}
    for ext in formats:
        path = stem.with_suffix(f".{ext}")
        fig.savefig(path, dpi=DPI, metadata={"Date": None} if ext in ("svg", "pdf") else {})
        if ext == "svg":
            # Matplotlib path lines carry trailing spaces; normalize the text export.
            path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
        outputs[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return outputs
