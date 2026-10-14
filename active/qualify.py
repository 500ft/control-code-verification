"""Execute the preregistered active development cases against exact intent and strict C."""
import ctypes as ct
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import platform
import struct
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import intent, reference
from active.boundary import initialize, validate_step

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'active'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
spec = json.loads((HERE / 'spec.json').read_text())
cases = json.loads((HERE / 'directed.json').read_text())
supplemental = json.loads((HERE / 'supplemental-directed.json').read_text())
supplemental_registration = json.loads((HERE / 'registration-supplemental.json').read_text())
assert sha(HERE / 'supplemental-directed.json') == supplemental_registration['sha256']
registration = json.loads((HERE / 'registration.json').read_text())
for name in ('spec.json', 'directed.json'):
    assert sha(HERE / name) == registration['sha256']['active/' + name]
assert spec['variant'] == 'active_symmetric'
ceiling = Q(spec['acceptance']['ceiling_rad_per_s'])
limit = Q(spec['state_abs_max'])
input_limit = Q(spec['input_abs_max'])
cfg = dict(tau=float(Q(spec['tau'])), slew_up=float(Q(spec['slew_up'])),
           slew_down=float(Q(spec['slew_down'])), reset_tracks_input=False)


def valid(x, u, dt):
    try:
        validate_step(x, u, dt, float(limit), float(input_limit),
                      float(Q(spec['dt_min_positive'])), float(Q(spec['dt_max'])))
    except ValueError:
        return False
    return True


build = ROOT / 'build' / 'active'
build.mkdir(parents=True, exist_ok=True)
source = HERE / 'generated' / (spec['variant'] + '.c')
shared = build / 'active_symmetric.so'
command = ['cc', '-std=c99', '-O2', '-fno-fast-math', '-ffp-contract=off',
           '-Wall', '-Wextra', '-Wno-unused-parameter', '-Werror', '-shared', '-fPIC',
           str(source), '-o', str(shared)]
subprocess.run(command, check=True, capture_output=True)
lib = ct.CDLL(str(shared))
fn = lib.active_symmetric
ptr = ct.POINTER(ct.c_float)
fn.argtypes = [ct.POINTER(ptr), ct.POINTER(ptr), ct.POINTER(ct.c_longlong), ptr, ct.c_int]
fn.restype = ct.c_int


def run(x, u, dt, reset=False):
    arg = (ct.c_float * 4)(x, u, dt, reset)
    out = (ct.c_float * 3)()
    assert fn((ptr * 1)(arg), (ptr * 1)(out), None, None, 0) == 0
    return tuple(out)


results = []
for cohort, case in [('original', c) for c in cases['cases']] + [('review_supplement', c) for c in supplemental['cases']]:
    kind = case['kind']
    if kind == 'initializer':
        previous = Q(case['preceding'])
        try:
            initialized = initialize(float(previous), float(limit))
            accepted = True
        except ValueError:
            initialized = None
            accepted = False
        results.append({'cohort': cohort, 'id': case['id'], 'kind': kind, 'accepted': accepted,
                        'output': str(Q(initialized)) if accepted else None,
                        'matches_registered_expectation': accepted == (case['expect'].startswith('unchanged'))})
        continue
    if kind == 'reject':
        u = float('nan') if case['u'] == 'NaN' else Q(case['u'])
        rejected = not valid(Q(case['x0']), u, Q(case['dt']))
        results.append({'cohort': cohort, 'id': case['id'], 'kind': kind, 'rejected_before_core': rejected})
        continue
    x0, u, dt = (Q(case[k]) for k in ('x0', 'u', 'dt'))
    assert valid(x0, u, dt), case['id']
    exact, native, rounded = x0, float(x0), float(x0)
    max_error = Q(0)
    first_exceed = None
    c_reference_mismatches = 0
    exact_flag_mismatches = 0
    observed_at = {}
    for step in range(1, case['steps'] + 1):
        exact_out = intent(exact, u, dt, False, cfg, limit)
        c_out = run(native, float(u), float(dt))
        ref_out = reference(rounded, float(u), float(dt), False, cfg, float(limit))
        if struct.pack('3f', *c_out) != struct.pack('3f', *map(float, ref_out)):
            c_reference_mismatches += 1
        if tuple(exact_out[1:]) != tuple(int(f) for f in c_out[1:]):
            exact_flag_mismatches += 1
        exact, native, rounded = exact_out[0], c_out[0], float(ref_out[0])
        error = abs(Q(native) - exact)
        if error > max_error:
            max_error = error
        if first_exceed is None and error > ceiling:
            first_exceed = {'step': step, 'elapsed_s': str(dt * step),
                            'exact_state': str(exact), 'c_state_hex': struct.pack('f', native).hex(),
                            'c_state': native, 'abs_error': str(error)}
        if step in (1, case['steps'] // 2, case['steps']):
            observed_at[str(step)] = {'exact_state': str(exact), 'c_state': native,
                                      'abs_error': str(error), 'c_flags': [int(f) for f in c_out[1:]]}
    if cohort == 'review_supplement':
        assert c_reference_mismatches == 0
        assert exact_flag_mismatches == 0
        assert all(row['c_flags'] == [0, 0] for row in observed_at.values())
    results.append({'cohort': cohort, 'id': case['id'], 'kind': kind, 'steps': case['steps'],
                    'max_abs_error': str(max_error), 'ceiling_exceeded': first_exceed is not None,
                    'first_exceed': first_exceed, 'c_reference_mismatches': c_reference_mismatches,
                    'exact_flag_mismatches': exact_flag_mismatches, 'observed_at': observed_at})

failed = [r for r in results if r.get('ceiling_exceeded')]
record = {'status': 'failed adopted continuous numerical ceiling on directed development cases' if failed else 'directed cases passed; universal ceiling still unproved',
          'quantity_interpretation': 'propagated next-state divergence between independently evolved exact and compiled histories, as required by CONSUMER.md for a continuous segment',
          'registration_sha256': sha(HERE / 'registration.json'),
          'supplemental_registration_sha256': sha(HERE / 'registration-supplemental.json'),
          'harness_sha256': {name: sha(HERE / name) for name in ('qualify.py', 'boundary.py', 'generate.py')},
          'oracle_sha256': sha(ROOT / 'core.py'),
          'source_sha256': sha(source), 'binary_sha256': sha(shared),
          'compiler_command': command, 'compiler': subprocess.check_output(['cc', '--version'], text=True).splitlines()[0],
          'platform': platform.platform(), 'python': sys.version.split()[0],
          'cases': results, 'continuous_ceiling_holds': all(not r.get('ceiling_exceeded', False) for r in results),
          'universal_ceiling_refuted': bool(failed), 'target_build_qualified': False,
          'wrapper_admitted': False, 'withheld_executed': False}
(HERE / 'results.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'cases': len(results), 'ceiling_failures': [r['id'] for r in results if r.get('ceiling_exceeded')],
                  'c_reference_mismatches': sum(r.get('c_reference_mismatches', 0) for r in results)}, indent=2))
