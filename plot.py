"""Plot only committed development observations, no simulation or holdout reads."""
import csv
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root=Path(__file__).resolve().parent
source=root/'evidence/traces.csv'
rows=list(csv.DictReader(source.open()))
spec=json.loads((root/'spec.json').read_text())
fig,axes=plt.subplots(2,2,figsize=(11,7),layout='constrained')
for col,(variant,cfg) in enumerate(spec['variants'].items()):
    trajectory=[r for r in rows if r['variant']==variant and r['trace']=='reversal']
    top=axes[0,col]
    top.plot([float(r['time_s']) for r in trajectory],[float(r['intent_rad_s']) for r in trajectory],color='#ca6702',ls='--',lw=3,label='Exact intent')
    top.plot([float(r['time_s']) for r in trajectory],[float(r['c_rad_s']) for r in trajectory],color='#005f73',lw=1.2,label='Compiled C')
    issues=[r for r in trajectory if r['branch_issue']=='True']
    top.scatter([float(r['time_s']) for r in issues],[float(r['c_rad_s']) for r in issues],marker='x',s=55,color='#ae2012',zorder=4,label='Branch issue')
    top.set(title=f"{variant.replace('_',' ')} | tau={cfg['tau']} s",xlabel='Elapsed time (s)',ylabel='Rate (rad/s)')
    top.legend(fontsize=8,loc='lower right')
    selected=[r for r in rows if r['variant']==variant and r['trace']=='constant_unsaturated']
    bottom=axes[1,col]
    bottom.plot([float(r['time_s']) for r in selected],[float(r['abs_error_rad_s']) for r in selected],label='Absolute state error',color='#005f73')
    bottom.plot([float(r['time_s']) for r in selected],[float(r['bound_rad_s']) for r in selected],label='Derived numerical bound',ls='--',color='#ca6702')
    bottom.set(yscale='log',xlabel='Elapsed time (s)',ylabel='Error / bound (rad/s)',title='Unsaturated constant-input trace')
    bottom.legend(fontsize=8,loc='center right')
for ax in axes.flat:
    ax.grid(alpha=.2)
    ax.spines[['top','right']].set_visible(False)
fig.suptitle('Executed core qualification | deterministic development traces',fontsize=14)
sha=hashlib.sha256(source.read_bytes()).hexdigest()
fig.supxlabel('Config: spec.json | Data: evidence/traces.csv (SHA-256 '+sha[:12]+')\nReversal markers flag threshold uncertainty; numerical agreement alone does not qualify branch use.',fontsize=9)
fig.savefig(root/'evidence/core-qualification.png',dpi=170)
(root/'evidence/figure.json').write_text(json.dumps({'source':'evidence/traces.csv','source_sha256':sha,'config_sha256':hashlib.sha256((root/'spec.json').read_bytes()).hexdigest(),'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'command':'python3 plot.py','matplotlib':matplotlib.__version__,'figure_sha256':hashlib.sha256((root/'evidence/core-qualification.png').read_bytes()).hexdigest()},indent=2)+'\n')
