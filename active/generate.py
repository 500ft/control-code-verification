"""Generate only the separately registered active variant; original C is untouched."""
import json
import os
from fractions import Fraction
from pathlib import Path
import casadi as ca

HERE = Path(__file__).resolve().parent
spec = json.loads((HERE / 'spec.json').read_text())
name = spec['variant']
tau = float(Fraction(spec['tau']))
up = float(Fraction(spec['slew_up']))
down = float(Fraction(spec['slew_down']))
limit = float(Fraction(spec['state_abs_max']))
v = ca.SX.sym('v', 4)
x, u, dt, reset = [v[i] for i in range(4)]
clip = lambda a, lo, hi: ca.if_else(a < lo, lo, ca.if_else(a > hi, hi, a))
flag = lambda a, lo, hi: ca.if_else(a < lo, -1, ca.if_else(a > hi, 1, 0))
delta = dt / (tau + dt) * (u - x)
lo, hi = -down * dt, up * dt
reached = x + clip(delta, lo, hi)
state = ca.if_else(reset, 0, ca.if_else(dt == 0, x, clip(reached, -limit, limit)))
y = ca.vertcat(state, ca.if_else(ca.logic_or(reset, dt == 0), 0, flag(delta, lo, hi)),
               ca.if_else(ca.logic_or(reset, dt == 0), 0, flag(reached, -limit, limit)))
out = HERE / 'generated'
out.mkdir(exist_ok=True)
previous = Path.cwd()
os.chdir(out)
try:
    ca.Function(name, [v], [y]).generate(name + '.c',
                                        {'casadi_real': 'float', 'with_header': True})
finally:
    os.chdir(previous)
for suffix in ('.c', '.h'):
    path = out / (name + suffix)
    path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines()) + '\n')
