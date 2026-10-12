"""Exact operands at the minimized observed branch transitions."""
from fractions import Fraction as Q
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import intent
from campaign.audit_observation import binary32, oracle
from qualify import ROOT


def explain(example,spec):
    case=example['case'];cfg=spec['variants'][case['variant']];limit=spec['domain']['state_abs_max']
    exact=Q(case['initial']);ref=case['initial']
    for i,s in enumerate(case['steps']):
        u,dt=s['u'],s['dt']
        if i==example['observation']['step']:
            alpha=Q(dt)/(Q(cfg['tau'])+Q(dt));delta=alpha*(Q(u)-exact)
            lo,hi=-Q(cfg['slew_down'])*Q(dt),Q(cfg['slew_up'])*Q(dt)
            reached=exact+max(lo,min(hi,delta))
            den=binary32(Q(cfg['tau'])+Q(dt),cfg['tau']+dt)
            a=binary32(Q(dt)/Q(den),dt/den)
            difference=binary32(Q(u)-Q(ref),u-ref)
            d=binary32(Q(a)*Q(difference),a*difference)
            clipped=max(float(lo),min(float(hi),d))
            z=binary32(Q(ref)+Q(clipped),ref+clipped)
            kind,direction=example['transition'].split(':')
            lower=direction.startswith('-')
            threshold=(lo if lower else hi) if kind=='slew' else Q(-limit if lower else limit)
            operand=delta if kind=='slew' else reached
            rounded=Q(d if kind=='slew' else z)
            assert (operand<threshold if lower else operand>threshold) and rounded==threshold
            return dict(predicate=f'{kind} {"<" if lower else ">"} threshold',exact_operand_rad_s=str(operand),threshold_rad_s=str(threshold),rounded_operand_rad_s=str(rounded),exact_signed_gap_rad_s=str(operand-threshold),interpretation='exact operand strictly beyond threshold; binary32 operand equals threshold; strict rounded predicate false; external functional consequence unspecified')
        exact=intent(exact,u,dt,s['reset'],cfg,limit)[0]
        ref=oracle(ref,u,dt,s['reset'],cfg,limit)[0]
    raise AssertionError('missing observation')


if __name__=='__main__':
    path=Path(sys.argv[1]);r=json.loads(path.read_text());spec=json.loads((ROOT/'spec.json').read_text())
    for example in r['minimal_branch_examples']:example['operand_explanation']=explain(example,spec)
    path.write_text(json.dumps(r,indent=2)+'\n')
