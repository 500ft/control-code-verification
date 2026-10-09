"""Shared figure rules for committed plots.

Three text sizes by role, one colour per plotted entity, outward ticks,
frameless legends and byte-stable PNG/SVG output.
"""
import hashlib
from pathlib import Path
import matplotlib

# Titles, axis labels and series names; legend, notes and annotations; tick labels.
SIZES = {'base': 9, 'note': 8, 'tick': 7, 'letter': 10}

# One colour per entity in every committed figure.
COLORS = {
    'compiled_c': '#2980b9',      # compiled C output and its error against exact intent
    'exact_intent': '#e69f00',    # exact rational intent
    'bound': '#4d5560',           # analytical numerical error bound
    'threshold_step': '#c0392b',  # step whose uncertainty interval touches a branch threshold
    'zero_line': '#9aa0a6',
    'note_text': '#3c4043',
}

DPI = 300


def apply(salt):
    """Set the shared rcParams. The salt keeps SVG element ids stable."""
    matplotlib.rcParams.update({
        'font.size': SIZES['base'],
        'axes.titlesize': SIZES['base'],
        'axes.labelsize': SIZES['base'],
        'xtick.labelsize': SIZES['tick'],
        'ytick.labelsize': SIZES['tick'],
        'legend.fontsize': SIZES['note'],
        'legend.frameon': False,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'xtick.direction': 'out',
        'ytick.direction': 'out',
        'axes.linewidth': 0.8,
        'figure.facecolor': 'white',
        'savefig.facecolor': 'white',
        'svg.fonttype': 'path',
        'svg.hashsalt': salt,
    })


def panel_letter(fig, ax, letter, y):
    """Bold panel letter at the axes' left edge, on the panel-title line."""
    x = ax.get_position().x0
    fig.text(x, y, letter, fontsize=SIZES['letter'], fontweight='bold', ha='left', va='baseline')


def save(fig, stem):
    """Write stem.png (300 dpi) and stem.svg; return {file name: sha256}."""
    stem = Path(stem)
    outputs = {}
    for ext in ['png', 'svg']:
        path = stem.with_suffix(f'.{ext}')
        fig.savefig(path, dpi=DPI, metadata={'Date': None} if ext == 'svg' else None)
        if ext == 'svg':
            path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines()) + '\n')
        outputs[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return outputs
