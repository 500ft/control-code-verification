"""Generation factor only. The verifier does not use this expression as its oracle."""
import json
import os
from pathlib import Path
import casadi as ca

ROOT = Path(__file__).resolve().parent


def generate():
    spec = json.loads((ROOT/'spec.json').read_text())
    out = ROOT/'generated'
    out.mkdir(exist_ok=True)
    previous = Path.cwd()
    os.chdir(out)
    try:
        for name, cfg in spec['variants'].items():
            v = ca.SX.sym('v', 4)
            x, u, dt, reset = (v[i] for i in range(4))
            clip = lambda a, lo, hi: ca.if_else(a < lo, lo, ca.if_else(a > hi, hi, a))
            flag = lambda a, lo, hi: ca.if_else(a < lo, -1, ca.if_else(a > hi, 1, 0))
            limit = spec['domain']['state_abs_max']
            delta = dt/(cfg['tau']+dt)*(u-x)
            lo, hi = -cfg['slew_down']*dt, cfg['slew_up']*dt
            reached = x+clip(delta, lo, hi)
            reset_value = clip(u, -limit, limit) if cfg['reset_tracks_input'] else 0
            state = ca.if_else(reset, reset_value, ca.if_else(dt == 0, x, clip(reached, -limit, limit)))
            y = ca.vertcat(state, ca.if_else(ca.logic_or(reset, dt == 0), 0, flag(delta, lo, hi)),
                          ca.if_else(ca.logic_or(reset, dt == 0), 0, flag(reached, -limit, limit)))
            ca.Function(name, [v], [y]).generate(name+'.c', {'casadi_real':'float', 'with_header':True})
            # Normalize generator whitespace only; arithmetic stays untouched.
            for suffix in ('.c', '.h'):
                path = out/(name+suffix)
                path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())+'\n')
    finally:
        os.chdir(previous)


if __name__ == '__main__':
    generate()
