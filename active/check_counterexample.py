"""Independent closed-form check of the registered half-ULP slew case."""
from fractions import Fraction as Q
import json
from pathlib import Path

here = Path(__file__).resolve().parent
spec = json.loads((here / 'spec.json').read_text())
cases = {c['id']: c for c in json.loads((here / 'directed.json').read_text())['cases']}
results = {c['id']: c for c in json.loads((here / 'results.json').read_text())['cases']}
ceiling = Q(spec['acceptance']['ceiling_rad_per_s'])
for direction in (1, -1):
    name = ('positive' if direction == 1 else 'negative') + '_tie_accumulation'
    case, result = cases[name], results[name]
    h = Q(case['dt'])
    n = result['first_exceed']['step']
    assert h == Q(513, 33554432)
    assert 2 * h == Q(513, 16777216)  # 256.5 ulps in the [1,2) binade
    exact = direction * (1 + n * 2 * h)
    c = direction * (1 + Q(n, 32768))  # nearest-even: 256 ulps on each step
    assert abs(exact) < 2 and abs(c) < 2
    assert 8 - abs(exact) > 2 * (Q(1, 4) + h)  # slew branch remains active
    error = abs(exact - c)
    assert error == Q(result['first_exceed']['abs_error'])
    assert c == Q(result['first_exceed']['c_state'])
    assert (n - 1) * Q(1, 16777216) <= ceiling < n * Q(1, 16777216)
    assert error > ceiling
    end = case['steps']
    assert Q(result['max_abs_error']) == end * Q(1, 16777216)
    print(name, 'first crossing', n, 'error', float(error), 'maximum', float(Q(result['max_abs_error'])))
