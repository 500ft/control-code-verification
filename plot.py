"""Plot committed development observations only; no simulation or holdout reads.

The canvas shows only the stored traces. Everything in words, including the
conditions and the finding, is written by ``caption()`` to a file beside the
image and copied into the README under it.
"""
import csv
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import NullLocator

import figure_style as style

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'evidence/traces.csv'
CONFIG = ROOT / 'spec.json'
# The live figure lives here; evidence/core-qualification.* is the frozen
# 2026-10-09 figure recorded in evidence/figure.json and is never rewritten.
OUT = ROOT / 'figures'
STEM = OUT / 'core-qualification'
TRACES = ('reversal', 'constant_unsaturated')
FIELDS = ('time_s', 'input_rad_s', 'dt_s', 'intent_rad_s', 'c_rad_s', 'abs_error_rad_s', 'bound_rad_s')
LETTERS = 'abcd'
XLABEL, YLABELS = 'Elapsed time [s]', ('Commanded rate [rad/s]', 'Absolute error [rad/s]')

# Layout in inches: 183 mm wide, two rows of two panels, legend above.
WIDTH, HEIGHT = 7.2, 4.8
MARGINS = {'left': .09, 'right': .99, 'top': .88, 'bottom': .09, 'wspace': .12, 'hspace': .5}


def load():
    rows = list(csv.DictReader(SOURCE.open()))
    spec = json.loads(CONFIG.read_text())

    def trace(variant, name):
        selected = [r for r in rows if r['variant'] == variant and r['trace'] == name]
        data = {k: [float(r[k]) for r in selected] for k in FIELDS}
        data['issue'] = [r['branch_issue'] == 'True' for r in selected]
        return data

    return {name: {v: trace(v, name) for v in spec['variants']} for name in TRACES}, spec


def facts(data: dict, spec: dict) -> dict:
    """Validated inputs shared by the figure and its caption; every number is read, not typed."""
    variants = spec['variants']
    reversal, constant = (data[name] for name in TRACES)
    limit = spec['domain']['state_abs_max']
    # Every caption statement below must hold for every plotted step.
    assert all(e == 0 for d in reversal.values() for e in d['abs_error_rad_s']), 'reversal agreement'
    assert all(abs(c) == limit for d in reversal.values()
               for c, flagged in zip(d['c_rad_s'], d['issue']) if flagged), 'clamp steps'
    assert not any(f for d in constant.values() for f in d['issue']), 'constant trace has no flagged step'
    assert len({(cfg['slew_up'], cfg['slew_down']) for cfg in variants.values()}) == 1, 'shared slew'
    dts = {dt for group in (reversal, constant) for d in group.values() for dt in d['dt_s']}
    assert len(dts) == 1, 'single dt'
    dt = Fraction(dts.pop())
    first = reversal[next(iter(variants))]
    switch = next(i for i, u in enumerate(first['input_rad_s']) if u != first['input_rad_s'][0])
    assert {len(d['time_s']) for d in reversal.values()} == {len(first['time_s'])}
    assert all(d['input_rad_s'] == first['input_rad_s'] for d in reversal.values())
    assert len({u for d in constant.values() for u in d['input_rad_s']}) == 1
    assert len({len(d['time_s']) for d in constant.values()}) == 1
    clamp_times = {v: [t for t, f in zip(d['time_s'], d['issue']) if f] for v, d in reversal.items()}
    assert len({tuple(t) for t in clamp_times.values()}) == 1, 'same clamp steps in both variants'
    # Floor of the smallest bound-to-error ratio; a zero error would make it unbounded.
    margin = {v: math.floor(min(b / e for e, b in zip(d['abs_error_rad_s'], d['bound_rad_s'])))
              for v, d in constant.items()}
    assert all(m >= 100 for m in margin.values()), margin
    cfg0 = next(iter(variants.values()))
    return {
        'reversal_steps': len(first['time_s']), 'dt': dt,
        'input_before': first['input_rad_s'][0], 'input_after': first['input_rad_s'][switch],
        'switch_t': first['time_s'][switch] - float(dt),
        'clamp_times': next(iter(clamp_times.values())), 'limit': limit,
        'constant_steps': len(next(iter(constant.values()))['time_s']),
        'constant_input': next(iter(constant.values()))['input_rad_s'][0],
        'margin': margin, 'slew_up': cfg0['slew_up'], 'slew_down': cfg0['slew_down'],
        'tau': {v: cfg['tau'] for v, cfg in variants.items()},
    }


def name(variant: str) -> str:
    return variant.replace('_', '-')


def caption(data: dict, spec: dict) -> str:
    f = facts(data, spec)
    variants = list(spec['variants'])
    taus = ' and '.join(f"{name(v)} (time constant {f['tau'][v]:g} s)" for v in variants)
    margins = ' and '.join(f"{f['margin'][v]} times ({name(v)})" for v in variants)
    clamp = ' and '.join(f"t = {t:g} s" for t in f['clamp_times'])
    return (
        "Numerical core qualification on the frozen development traces; integration "
        f"is unqualified. Panels (a) and (b) show the reversal trace for the {taus} "
        f"variants: {f['reversal_steps']} steps of dt = {f['dt']} s, input "
        f"{f['input_before']:+g} rad/s, then {f['input_after']:+g} rad/s from "
        f"t = {f['switch_t']:g} s. The dashed line is the exact rational intent and the "
        "solid line with circles is the binary32 compiled C output; the two agree at "
        f"every step, so the solid line lies on the dashed one. Crosses mark the "
        f"{len(f['clamp_times'])} steps per variant ({clamp}) where the state reaches the "
        f"rate clamp of {f['limit']:g} rad/s in magnitude. Their uncertainty interval touches "
        "the branch threshold, so the branch requirement stays open; all implementations "
        "took the same branch at these steps. Panels (c) and (d) show the constant-input "
        f"trace, {f['constant_steps']} steps of dt = {f['dt']} s at {f['constant_input']:g} "
        "rad/s, on a log scale: the solid line with circles is the absolute error of "
        "compiled C against exact intent and the dash-dot line is the deterministic "
        "worst-case bound from NUMERICS.md. The error stays at least "
        f"{margins} below the bound. Both variants use slew limits "
        f"{f['slew_up']:+g} and {-f['slew_down']:+g} rad/s² and the same rate clamp. Each row "
        "shares its y axis across the two variants. Source: evidence/traces.csv "
        f"(traces {' and '.join(TRACES)}) and spec.json."
    )


def figure(data: dict, spec: dict):
    facts(data, spec)
    variants = list(spec['variants'])
    style.apply('core-qualification')
    fig, axes = plt.subplots(2, 2, figsize=(WIDTH, HEIGHT), sharey='row')
    fig.subplots_adjust(**MARGINS)
    for col, variant in enumerate(variants):
        top, bottom = axes[0, col], axes[1, col]
        d = data['reversal'][variant]
        top.plot(d['time_s'], d['intent_rad_s'], zorder=2, **style.SERIES['exact_intent'])
        top.plot(d['time_s'], d['c_rad_s'], markevery=16, zorder=3, **style.SERIES['compiled_c'])
        flagged = [(t, c) for t, c, f in zip(d['time_s'], d['c_rad_s'], d['issue']) if f]
        top.plot(*zip(*flagged), zorder=4, **style.SERIES['clamp_step'])
        top.set(xlim=(-0.16, 8.16), ylim=(-2.4, 2.4), xticks=range(0, 9, 2), yticks=[-2, -1, 0, 1, 2])

        d = data['constant_unsaturated'][variant]
        bottom.plot(d['time_s'], d['abs_error_rad_s'], markevery=8, zorder=3, **style.SERIES['compiled_c'])
        bottom.plot(d['time_s'], d['bound_rad_s'], zorder=2, **style.SERIES['bound'])
        bottom.set(yscale='log', ylim=(5e-11, 2e-4), xlim=(-0.04, 2.04), xticks=[0, .5, 1, 1.5, 2])
        bottom.yaxis.set_minor_locator(NullLocator())
    for row, label in enumerate(YLABELS):
        axes[row, 0].set_ylabel(label)
    for i, ax in enumerate(axes.flat):
        ax.set_xlabel(XLABEL)
        ax.tick_params(length=3)
        ax.text(0, 1.04, f'({LETTERS[i]})', transform=ax.transAxes, ha='left', va='bottom',
                size=style.LETTER_SIZE)
    handles = [Line2D([], [], **style.SERIES[key]) for key in style.SERIES]
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.5, .995), ncol=len(handles),
               columnspacing=1.4, handletextpad=.5, handlelength=2.6, borderaxespad=0)
    return fig


def main():
    data, spec = load()
    OUT.mkdir(exist_ok=True)
    fig = figure(data, spec)
    outputs = style.save(fig, STEM)
    plt.close(fig)
    STEM.with_suffix('.caption.md').write_text(caption(data, spec) + '\n')
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    (OUT / 'figure.json').write_text(json.dumps({
        'source': 'evidence/traces.csv', 'source_sha256': sha(SOURCE),
        'config_sha256': sha(CONFIG),
        'generator_sha256': sha(Path(__file__)),
        'style_helper': 'figure_style.py', 'style_helper_sha256': sha(ROOT / 'figure_style.py'),
        'command': 'python3 plot.py', 'matplotlib': matplotlib.__version__,
        'figure_sha256': outputs['core-qualification.png'], 'outputs': outputs,
        'caption': 'figures/core-qualification.caption.md',
        'selected_traces': list(TRACES),
        'frozen_predecessor': 'evidence/figure.json',
    }, indent=2) + '\n')


if __name__ == '__main__':
    main()
