"""Finite-domain DEVELOPMENT inputs only. Does not read outcomes or withheld data."""
import hashlib
import json
from pathlib import Path
import random
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
SPEC = json.loads((ROOT/'spec.json').read_text())
STRATA = ('variable_dt', 'saturation', 'slew_threshold', 'reset_precedence',
          'smooth_growth', 'tiny_values')


def f32(x):
    return struct.unpack('>f', struct.pack('>f', x))[0]


def adjacent(x, direction):
    """Neighbor toward positive/negative infinity, including zero/subnormals."""
    if x == 0:
        return direction*struct.unpack('>f', bytes.fromhex('00000001'))[0]
    b = struct.unpack('>I', struct.pack('>f', x))[0]
    b += direction if x > 0 else -direction
    return struct.unpack('>f', struct.pack('>I', b))[0]


def sample(u, dt, reset=False):
    return dict(u=f32(u), dt=f32(dt), reset=bool(reset))


def directed():
    for variant, cfg in SPEC['variants'].items():
        for x in (0.0, -0.0, 2.0, -2.0, adjacent(2.0, -1), adjacent(-2.0, 1)):
            key = struct.pack('>f', x).hex()
            for reset in (False, True):
                yield dict(id=f'{variant}/hold-reset/{key}/{reset}', variant=variant,
                           stratum='directed_hold_reset', seed=None, initial=x,
                           steps=[sample(-8, 0, reset), sample(8, 1/32)])
        for x in (0.0, 1.875, -1.9375):
            for dt in (2**-16, 1/32, 1/16):
                for sign, slew in ((1, cfg['slew_up']), (-1, cfg['slew_down'])):
                    threshold = f32(x+sign*slew*(cfg['tau']+dt))
                    for u in (adjacent(threshold,-1), threshold, adjacent(threshold,1)):
                        yield dict(id=f'{variant}/threshold/{x}/{dt}/{sign}/{u.hex()}',
                                   variant=variant, stratum='directed_threshold', seed=None,
                                   initial=x, steps=[sample(u,dt),sample(-u,dt),sample(u,0,True)])
        for sign in (-1,1):
            yield dict(id=f'{variant}/subnormal/{sign}',variant=variant,
                       stratum='directed_subnormal',seed=None,initial=sign*2**-149,
                       steps=[sample(sign*2**-126,1/16),sample(0,2**-16),sample(0,0)])


def randomized(phase, per_stratum):
    config = json.loads((ROOT/'campaign/design.json').read_text())
    base = config['seeds'][phase]
    for variant_index, (variant,cfg) in enumerate(SPEC['variants'].items()):
        for stratum_index, stratum in enumerate(STRATA):
            for index in range(per_stratum):
                seed = base+variant_index*10000000+stratum_index*100000+index
                r = random.Random(seed)
                x = f32(r.uniform(-2,2))
                steps=[]
                for j in range(config['horizon']):
                    dt=f32(2**r.uniform(-16,-4)); u=f32(r.uniform(-8,8)); reset=False
                    if stratum=='saturation':
                        u=r.choice((-8,8,adjacent(-2,-1),-2,adjacent(-2,1),adjacent(2,-1),2,adjacent(2,1)))
                        dt=r.choice((2**-16,1/32,1/16))
                    elif stratum=='slew_threshold':
                        # Reset anchors a permitted known state before near-threshold updates.
                        dt=r.choice((2**-16,1/32,1/16))
                        if j%2==0:
                            u=r.choice((-1.0,0.0,1.0)); reset=True
                            anchor=u if cfg['reset_tracks_input'] else 0.0
                        else:
                            sign=r.choice((-1,1)); rate=cfg['slew_up'] if sign>0 else cfg['slew_down']
                            u=f32(anchor+sign*rate*(cfg['tau']+dt))
                            u=r.choice((adjacent(u,-1),u,adjacent(u,1)))
                    elif stratum=='reset_precedence':
                        reset=r.random()<.25; dt=r.choice((0,2**-16,1/32,1/16))
                    elif stratum=='smooth_growth':
                        u=f32(r.uniform(-.02,.02)); dt=f32(2**r.uniform(-16,-10)); x=0.0
                    elif stratum=='tiny_values':
                        x=0.0
                        u=r.choice((-1,1))*r.choice((2**-149,2**-140,2**-126,2**-120))
                    steps.append(sample(u,dt,reset))
                yield dict(id=f'{phase}/{variant}/{stratum}/{index}',variant=variant,
                           stratum=stratum,seed=seed,initial=x,steps=steps)


def cases(phase, per_stratum):
    if phase=='pilot':
        yield from directed()
    yield from randomized(phase,per_stratum)


def main():
    phase=sys.argv[1]; per_stratum=int(sys.argv[2]); out=Path(sys.argv[3])
    h=hashlib.sha256(); count=steps=0
    with out.open('wb') as f:
        for case in cases(phase,per_stratum):
            line=(json.dumps(case,sort_keys=True,separators=(',',':'))+'\n').encode()
            f.write(line);h.update(line);count+=1;steps+=len(case['steps'])
    print(json.dumps(dict(corpus_sha256=h.hexdigest(),traces=count,steps=steps)))


if __name__=='__main__':
    main()
