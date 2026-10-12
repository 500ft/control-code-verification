"""Independent exact-rounding audit of the prospectively selected pilot rows."""
from fractions import Fraction as Q
import gzip
import json
from pathlib import Path
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from campaign.generate_cases import adjacent, f32
from qualify import analytic_checks, ROOT


def binary32(exact, zero_sign):
    candidate=f32(float(exact)) if exact else f32(zero_sign)
    choices=[candidate,adjacent(candidate,-1),adjacent(candidate,1)]
    # Exact distances and even significand resolve rounding independently of NumPy.
    return min(choices,key=lambda v:(abs(Q(v)-exact),struct.unpack('>I',struct.pack('>f',v))[0]&1))


def oracle(x,u,dt,reset,cfg,limit):
    if reset:return (max(-limit,min(limit,u)) if cfg['reset_tracks_input'] else 0.),0,0
    if not dt:return x,0,0
    denominator=binary32(Q(cfg['tau'])+Q(dt),cfg['tau']+dt)
    alpha=binary32(Q(dt)/Q(denominator),dt/denominator)
    difference=binary32(Q(u)-Q(x),u-x)
    delta=binary32(Q(alpha)*Q(difference),alpha*difference)
    lo=binary32(-Q(cfg['slew_down'])*Q(dt),-cfg['slew_down']*dt)
    hi=binary32(Q(cfg['slew_up'])*Q(dt),cfg['slew_up']*dt)
    clipped=max(lo,min(hi,delta))
    reached=binary32(Q(x)+Q(clipped),x+clipped)
    flag=lambda v,low,high:-1 if v<low else 1 if v>high else 0
    return max(-limit,min(limit,reached)),flag(delta,lo,hi),flag(reached,-limit,limit)


def main():
    cases={c['id']:c for c in map(json.loads,Path(sys.argv[1]).read_text().splitlines())}
    spec=json.loads((ROOT/'spec.json').read_text());analytic=analytic_checks(spec)
    audited=0
    with gzip.open(sys.argv[2],'rt') as rows:
        for line in rows:
            row=json.loads(line);case=cases[row['id']]
            if not case['stratum'].startswith('directed') and row['step']%16:continue
            s=case['steps'][row['step']]
            expected=oracle(row['prior_reference'],s['u'],s['dt'],s['reset'],spec['variants'][case['variant']],spec['domain']['state_abs_max'])
            assert struct.pack('>3f',*expected).hex()==row['reference_bits'],row
            audited+=1
    print(json.dumps(dict(audited_steps=audited,status='passed',analytic_checks=analytic)))


if __name__=='__main__':main()
