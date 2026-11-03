"""Caption and manifest for the MATLAB core-qualification figure.

MATLAB draws the figure from the committed traces; see figures/matlab/README.md.
This script reads the same files, checks every statement the caption makes,
writes the caption beside the image and records the input and output hashes
in figures/figure.json. It draws nothing and needs only the standard library.
"""
import csv
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'evidence/traces.csv'
CONFIG = ROOT / 'spec.json'
# The live figure lives here; evidence/core-qualification.* is the frozen
# 2026-10-09 figure recorded in evidence/figure.json and is never rewritten.
OUT = ROOT / 'figures'
STEM = OUT / 'core-qualification'
MATLAB = OUT / 'matlab'
GENERATOR = MATLAB / 'make_core_qualification.m'
HELPERS = ('render_figures.m', 'fig_style.m', 'export_pair.m')
TRACES = ('reversal', 'constant_unsaturated')
FIELDS = ('time_s', 'input_rad_s', 'dt_s', 'intent_rad_s', 'c_rad_s', 'abs_error_rad_s', 'bound_rad_s')
OUTPUTS = ('core-qualification.png', 'core-qualification.pdf')
MATLAB_RELEASE = 'R2025b'
COMMAND = 'matlab -batch "addpath(\'figures/matlab\'); render_figures" && python3 plot.py'


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
    """Validated inputs for the caption; every number is read, not typed."""
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
        f"t = {f['switch_t']:g} s. The thick blue line is the exact rational intent and the "
        "thin orange line with dots is the binary32 compiled C output; the two agree at "
        "every step, so the orange line lies on the blue one. Hollow circles mark the "
        f"{len(f['clamp_times'])} steps per variant ({clamp}) where the state reaches the "
        f"rate clamp of {f['limit']:g} rad/s in magnitude, drawn as dotted grey lines. Their "
        "uncertainty interval touches the branch threshold, so the branch requirement stays "
        "open; all implementations took the same branch at these steps. Panels (c) and (d) "
        f"show the constant-input trace, {f['constant_steps']} steps of dt = {f['dt']} s at "
        f"{f['constant_input']:g} rad/s, on a log scale: the orange line with dots is the "
        "absolute error of compiled C against exact intent and the blue line is the "
        "deterministic worst-case bound from NUMERICS.md. The error stays at least "
        f"{margins} below the bound. Both variants use slew limits "
        f"{f['slew_up']:+g} and {-f['slew_down']:+g} rad/s² and the same rate clamp. Each row "
        "shares its y axis across the two variants. Source: evidence/traces.csv "
        f"(traces {' and '.join(TRACES)}) and spec.json."
    )


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest() -> dict:
    outputs = {name: sha(OUT / name) for name in OUTPUTS}
    return {
        'source': 'evidence/traces.csv', 'source_sha256': sha(SOURCE),
        'config_sha256': sha(CONFIG),
        'generator': 'figures/matlab/make_core_qualification.m', 'generator_sha256': sha(GENERATOR),
        'helpers': {f'figures/matlab/{h}': sha(MATLAB / h) for h in HELPERS},
        'caption_writer': 'plot.py', 'caption_writer_sha256': sha(Path(__file__)),
        'command': COMMAND, 'matlab': MATLAB_RELEASE,
        'figure_sha256': outputs['core-qualification.png'], 'outputs': outputs,
        'caption': 'figures/core-qualification.caption.md',
        'selected_traces': list(TRACES),
        'frozen_predecessor': 'evidence/figure.json',
    }


def main():
    data, spec = load()
    STEM.with_suffix('.caption.md').write_text(caption(data, spec) + '\n')
    (OUT / 'figure.json').write_text(json.dumps(manifest(), indent=2) + '\n')


if __name__ == '__main__':
    main()
