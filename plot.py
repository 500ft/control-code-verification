"""Plot committed development observations only; no simulation or holdout reads."""
import csv
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parent
source = root / 'evidence/traces.csv'
rows = list(csv.DictReader(source.open()))
spec = json.loads((root / 'spec.json').read_text())
BLUE, PURPLE, RED = '#2980b9', '#7d3c98', '#c0392b'
plt.rcParams.update({'font.size': 11, 'axes.titlesize': 12,
                     'figure.facecolor': 'white', 'svg.hashsalt': 'core-qualification'})
fig, axes = plt.subplots(2, 2, figsize=(10, 8), sharey='row')
fig.subplots_adjust(left=.10, right=.97, bottom=.14, top=.79, hspace=.78, wspace=.18)
for col, (variant, cfg) in enumerate(spec['variants'].items()):
    trajectory = [r for r in rows if r['variant'] == variant and r['trace'] == 'reversal']
    top = axes[0, col]
    t = [float(r['time_s']) for r in trajectory]
    top.plot(t, [float(r['intent_rad_s']) for r in trajectory],
             color=PURPLE, ls='--', lw=2.4, label='Exact intent')
    top.plot(t, [float(r['c_rad_s']) for r in trajectory],
             color=BLUE, lw=1.2, marker='o', markevery=16, ms=3,
             label='Compiled C (binary32 agreement)')
    issues = [r for r in trajectory if r['branch_issue'] == 'True']
    top.scatter([float(r['time_s']) for r in issues], [float(r['c_rad_s']) for r in issues],
                marker='x', s=50, color=RED, zorder=4, label='Threshold uncertainty')
    top.axhline(0, color='#606770', lw=.7)
    top.set(title=f"{variant.replace('_', ' ').capitalize()} · tau = {cfg['tau']} s",
            xlabel='Elapsed time [s]', xlim=(0,max(t)), ylim=(-2.3,2.3))
    selected = [r for r in rows if r['variant'] == variant and r['trace'] == 'constant_unsaturated']
    bottom = axes[1, col]
    bottom.plot([float(r['time_s']) for r in selected], [float(r['abs_error_rad_s']) for r in selected],
                label='Absolute state error', color=BLUE, marker='o', markevery=8, ms=3, lw=1.4)
    bottom.plot([float(r['time_s']) for r in selected], [float(r['bound_rad_s']) for r in selected],
                label='Deterministic numerical bound', ls='--', color=PURPLE, lw=1.8)
    bottom.set(yscale='log', ylim=(5e-11,2e-4), xlim=(0,max(float(r['time_s']) for r in selected)),
               xlabel='Elapsed time [s]', title='Constant unsaturated input')
    bottom.set_xticks([0,.5,1,1.5,2])
axes[0,0].set_ylabel('Rate [rad/s]')
axes[1,0].set_ylabel('Absolute error / bound [rad/s]')
for ax in axes.flat:
    ax.grid(axis='y', alpha=.18)
    ax.spines[['top','right']].set_visible(False)
fig.suptitle('Numerical core qualification', fontsize=16, y=.98)
fig.text(.5,.935,'Deterministic development traces · integration unqualified',ha='center',fontsize=11)
fig.legend(*axes[0,0].get_legend_handles_labels(), loc='upper center',
           bbox_to_anchor=(.5,.90), ncol=3, frameon=False, fontsize=9)
fig.legend(*axes[1,0].get_legend_handles_labels(), loc='upper center',
           bbox_to_anchor=(.5,.48), ncol=2, frameon=False, fontsize=10)
sha = hashlib.sha256(source.read_bytes()).hexdigest()
fig.text(.5,.045,'Top: reversal trace; crosses mark unresolved branch requirements.\nBottom: common log scale; bounds are analytical, not confidence intervals.',ha='center',fontsize=10)
outputs={}
for ext in ['png','svg']:
    p=root/f'evidence/core-qualification.{ext}'
    fig.savefig(p,dpi=170,metadata={'Date':None} if ext=='svg' else None)
    if ext == 'svg':
        p.write_text('\n'.join(line.rstrip() for line in p.read_text().splitlines()) + '\n')
    outputs[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
plt.close(fig)
(root/'evidence/figure.json').write_text(json.dumps({
    'source':'evidence/traces.csv','source_sha256':sha,
    'config_sha256':hashlib.sha256((root/'spec.json').read_bytes()).hexdigest(),
    'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'command':'python3 plot.py','matplotlib':matplotlib.__version__,
    'figure_sha256':outputs['core-qualification.png'],'outputs':outputs,
    'selected_traces':['reversal','constant_unsaturated'],
    'reference_commit':'bad572fc0902437445a5446bb5bc43098cc6211f'
},indent=2)+'\n')
