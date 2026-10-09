"""Plot committed development observations only; no simulation or holdout reads."""
import csv
import hashlib
import json
from fractions import Fraction
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import NullLocator
import figure_style as style

root = Path(__file__).resolve().parent
source = root / 'evidence/traces.csv'
rows = list(csv.DictReader(source.open()))
spec = json.loads((root / 'spec.json').read_text())
COLORS, SIZES = style.COLORS, style.SIZES
FIELDS = ['time_s', 'input_rad_s', 'dt_s', 'intent_rad_s', 'c_rad_s', 'abs_error_rad_s', 'bound_rad_s']


def trace(variant, name):
    selected = [r for r in rows if r['variant'] == variant and r['trace'] == name]
    data = {k: [float(r[k]) for r in selected] for k in FIELDS}
    data['issue'] = [r['branch_issue'] == 'True' for r in selected]
    return data


variants = spec['variants']
reversal = {v: trace(v, 'reversal') for v in variants}
constant = {v: trace(v, 'constant_unsaturated') for v in variants}
limit = spec['domain']['state_abs_max']

# Every title and label below must hold for every plotted step.
assert all(e == 0 for d in reversal.values() for e in d['abs_error_rad_s']), 'reversal title'
assert all(100 * e < b for d in constant.values()
           for e, b in zip(d['abs_error_rad_s'], d['bound_rad_s'])), 'constant-input title'
assert all(abs(c) == limit for d in reversal.values()
           for c, flagged in zip(d['c_rad_s'], d['issue']) if flagged), 'clamp-step label'
assert len({(cfg['slew_up'], cfg['slew_down']) for cfg in variants.values()}) == 1, 'shared slew note'
dts = {dt for group in (reversal, constant) for d in group.values() for dt in d['dt_s']}
assert len(dts) == 1, 'single dt note'
dt = Fraction(dts.pop())
first = reversal[next(iter(variants))]
switch = next(i for i, u in enumerate(first['input_rad_s']) if u != first['input_rad_s'][0])
switch_t = first['time_s'][switch] - float(dt)
assert {len(d['time_s']) for d in reversal.values()} == {len(first['time_s'])}
assert all(d['input_rad_s'] == first['input_rad_s'] for d in reversal.values())
constant_inputs = {u for d in constant.values() for u in d['input_rad_s']}
constant_steps = {len(d['time_s']) for d in constant.values()}
assert len(constant_inputs) == 1 and len(constant_steps) == 1
cfg0 = next(iter(variants.values()))


def num(x, fmt='g'):
    return format(x, fmt).replace('-', '\u2212')


style.apply('core-qualification')
W, H = 7.2, 6.4
fig = plt.figure(figsize=(W, H))
left, right, gap, axes_h = 0.66, 0.14, 0.22, 1.80
axes_w = (W - left - right - gap) / 2
fy = lambda inches_from_top: 1 - inches_from_top / H
rows_layout = [  # header, condition note, panel titles, axes top (inches from top)
    (0.70, 0.88, 1.10, 1.18),
    (3.64, 3.82, 4.04, 4.12),
]
fig.text(left / W, fy(0.20), 'Numerical core qualification on frozen development traces',
         ha='left', va='baseline')
fig.text(left / W, fy(0.38),
         f"Both reset variants: slew limits +{num(cfg0['slew_up'])} / \u2212{num(cfg0['slew_down'])} rad/s\u00b2, "
         f"rate clamp \u00b1{num(limit)} rad/s. Integration is unqualified.",
         ha='left', va='baseline', fontsize=SIZES['note'], color=COLORS['note_text'])
headers = [
    ('Reversal trace: binary32 compiled C equals the exact rational intent at every step',
     f"{len(first['time_s'])} steps of dt = {dt} s; input {num(first['input_rad_s'][0], '+g')} rad/s, "
     f"then {num(first['input_rad_s'][switch], '+g')} rad/s from t = {num(switch_t)} s"),
    ('Constant input: compiled C error stays more than 100\u00d7 below the analytical bound',
     f"{constant_steps.pop()} steps of dt = {dt} s at {num(constant_inputs.pop())} rad/s; "
     'bounds are deterministic worst cases from NUMERICS.md'),
]
axes = []
for r, (header_y, note_y, title_y, top_y) in enumerate(rows_layout):
    fig.text(left / W, fy(header_y), headers[r][0], ha='left', va='baseline')
    fig.text(left / W, fy(note_y), headers[r][1], ha='left', va='baseline',
             fontsize=SIZES['note'], color=COLORS['note_text'])
    row_axes = []
    for col in range(2):
        x0 = left + col * (axes_w + gap)
        ax = fig.add_axes([x0 / W, fy(top_y + axes_h), axes_w / W, axes_h / H],
                          sharey=row_axes[0] if row_axes else None)
        row_axes.append(ax)
    axes.append(row_axes)

letters = iter('abcd')
for r, row_axes in enumerate(axes):
    title_y = fy(rows_layout[r][2])
    for (variant, cfg), ax in zip(variants.items(), row_axes):
        style.panel_letter(fig, ax, next(letters), title_y)
        fig.text(ax.get_position().x0 + 0.17 / W, title_y,
                 f"{variant.replace('_', ' ').capitalize()} (\u03c4 = {num(cfg['tau'])} s)",
                 ha='left', va='baseline')

for col, variant in enumerate(variants):
    top, bottom = axes[0][col], axes[1][col]
    d = reversal[variant]
    top.axhline(0, color=COLORS['zero_line'], lw=.7, zorder=1)
    top.plot(d['time_s'], d['intent_rad_s'], color=COLORS['exact_intent'], ls='--', lw=2.4,
             zorder=2, label='Exact intent')
    top.plot(d['time_s'], d['c_rad_s'], color=COLORS['compiled_c'], lw=1.1, marker='o',
             markevery=16, ms=3, zorder=3, label='Compiled C')
    flagged = [(t, c) for t, c, f in zip(d['time_s'], d['c_rad_s'], d['issue']) if f]
    top.scatter(*zip(*flagged), marker='x', s=40, lw=1.4, color=COLORS['threshold_step'], zorder=4,
                label='Reaches clamp:\nrequirement open')
    top.set(xlim=(-0.16, 8.16), ylim=(-2.3, 2.3), xticks=range(9), xlabel='Elapsed time [s]')

    d = constant[variant]
    bottom.plot(d['time_s'], d['abs_error_rad_s'], color=COLORS['compiled_c'], lw=1.1,
                marker='o', markevery=8, ms=3, zorder=3)
    bottom.plot(d['time_s'], d['bound_rad_s'], color=COLORS['bound'], ls='--', lw=1.4, zorder=2)
    bottom.set(yscale='log', ylim=(5e-11, 2e-4), xlim=(-0.04, 2.04),
               xticks=[0, .5, 1, 1.5, 2], xlabel='Elapsed time [s]')
    bottom.yaxis.set_minor_locator(NullLocator())

axes[0][0].set_ylabel('Commanded rate [rad/s]')
axes[1][0].set_ylabel('Absolute error [rad/s]')
for row_axes in axes:
    row_axes[1].tick_params(labelleft=False)
    for ax in row_axes:
        ax.grid(axis='y', alpha=.18)

handles, labels = axes[0][0].get_legend_handles_labels()
axes[0][0].legend(handles, labels, loc='lower right', bbox_to_anchor=(1.0, 0.0),
                  handlelength=1.9, handletextpad=0.4, borderaxespad=0.2, labelspacing=0.3)
c_axes = axes[1][0]
c_axes.text(1.30, 3.5e-5, 'Analytical bound', color=COLORS['bound'], fontsize=SIZES['note'],
            ha='center', va='top')
c_axes.text(1.30, 4.5e-8, 'Compiled C error vs exact intent', color=COLORS['compiled_c'],
            fontsize=SIZES['note'], ha='center', va='bottom')

sha = hashlib.sha256(source.read_bytes()).hexdigest()
outputs = style.save(fig, root / 'evidence/core-qualification')
plt.close(fig)
(root/'evidence/figure.json').write_text(json.dumps({
    'source':'evidence/traces.csv','source_sha256':sha,
    'config_sha256':hashlib.sha256((root/'spec.json').read_bytes()).hexdigest(),
    'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'style_helper':'figure_style.py',
    'style_helper_sha256':hashlib.sha256((root/'figure_style.py').read_bytes()).hexdigest(),
    'command':'python3 plot.py','matplotlib':matplotlib.__version__,
    'figure_sha256':outputs['core-qualification.png'],'outputs':outputs,
    'selected_traces':['reversal','constant_unsaturated'],
    'reference_commit':'bad572fc0902437445a5446bb5bc43098cc6211f'
},indent=2)+'\n')
