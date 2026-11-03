"""Replay both retained binary32 active counterexample inputs through two boundaries.

(a) registered_horizon_b2b: the original 256-step back-to-back comparison loop
    from qualify.py (two exact-intent evaluations, one binary32 reference and two
    compiled calls per step, local and horizon bound checks, branch inspection),
    driven with the counterexample inputs and the active symmetric binary32 core.
(b) directed_long_horizon: the per-step loop of active/qualify.py and
    active/px4_domain/run.py that found each counterexample.
The root harness is hard-wired to traces.json and the shadow variants, so this
driver reproduces its loop instead of modifying it.
"""
import ctypes as ct
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import platform
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from core import intent, reference, validate
from active.boundary import validate_step

sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
registration = json.loads((HERE / 'registration.json').read_text())
# The hosted workflow regenerates the two retained result files with environment
# fields before this step, so they are read from the commit, not the working tree.
RETAINED = ('active/results.json', 'active/px4_domain/results.json')
committed = {name: subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT) for name in RETAINED}
for name, digest in registration['pinned_sha256'].items():
    content = committed[name] if name in RETAINED else (ROOT / name).read_bytes()
    assert hashlib.sha256(content).hexdigest() == digest, name
root_spec = json.loads((ROOT / 'spec.json').read_text())
active_spec = json.loads((ROOT / 'active/spec.json').read_text())
active_cases = {c['id']: c for c in json.loads((ROOT / 'active/directed.json').read_text())['cases']}
px4_cases = {c['id']: c for c in json.loads((ROOT / 'active/px4_domain/directed.json').read_text())['cases']}
retained = {'active': json.loads(committed['active/results.json']),
            'px4_domain': json.loads(committed['active/px4_domain/results.json'])}
ceiling = Q(active_spec['acceptance']['ceiling_rad_per_s'])
limit = Q(active_spec['state_abs_max'])
cfg = dict(tau=float(Q(active_spec['tau'])), slew_up=float(Q(active_spec['slew_up'])),
           slew_down=float(Q(active_spec['slew_down'])), reset_tracks_input=False)
step_bound = Q(root_spec['numerics']['local_error_coefficient']) * Q(root_spec['numerics']['unit_roundoff'])
horizon = root_spec['domain']['steps_max']

build = ROOT / 'build' / 'detection-cost'
build.mkdir(parents=True, exist_ok=True)
source = ROOT / 'active/generated/active_symmetric.c'
shared = build / 'active_symmetric.so'
command = ['cc', '-std=c99', '-O2', '-fno-fast-math', '-ffp-contract=off', '-Wall', '-Wextra',
           '-Wno-unused-parameter', '-Werror', '-shared', '-fPIC', str(source), '-o', str(shared)]
t0 = time.perf_counter()
subprocess.run(command, check=True, capture_output=True)
compile_s = time.perf_counter() - t0
fn = ct.CDLL(str(shared)).active_symmetric
ptr = ct.POINTER(ct.c_float)
fn.argtypes = [ct.POINTER(ptr), ct.POINTER(ptr), ct.POINTER(ct.c_longlong), ptr, ct.c_int]
fn.restype = ct.c_int


def run(x, u, dt, reset=False):
    arg = (ct.c_float * 4)(x, u, dt, reset)
    out = (ct.c_float * 3)()
    assert fn((ptr * 1)(arg), (ptr * 1)(out), None, None, 0) == 0
    return tuple(out)


# Input sequences, taken from the registered case files; dt bits from the owning results.
tie = active_cases['positive_tie_accumulation']
gap = px4_cases['half_ulp_near_min']
dt_bits = retained['px4_domain']['dt_bits']
gap_dt = {k: struct.unpack('<f', struct.pack('<I', int(dt_bits[str(k)], 16)))[0] for k in gap['delta_us']}
assert struct.pack('<f', gap_dt[125]).hex() == json.loads((ROOT / 'active/px4_domain/spec.json').read_text())['dt_min_bits_le']
sequences = {
    'continuous_ceiling_tie': {'x0': Q(tie['x0']), 'registered_steps': tie['steps'],
                               'step': lambda i: (float(Q(tie['u'])), float(Q(tie['dt']))),
                               'retained': next(c for c in retained['active']['cases'] if c['id'] == tie['id'])},
    'px4_timestamp_gap': {'x0': Q(gap['x0']), 'registered_steps': gap['repetitions'] * len(gap['commands']),
                          'step': lambda i: (float(Q(gap['commands'][i % 2])), gap_dt[gap['delta_us'][i % 2]]),
                          'retained': next(c for c in retained['px4_domain']['cases'] if c['id'] == gap['id'])},
}
assert float(Q(tie['dt'])) == float(struct.unpack('f', struct.pack('f', float(Q(tie['dt']))))[0])


def registered_horizon_b2b(seq):
    """The qualify.py per-step loop, truncated to the registered 256-step horizon."""
    exact = seq['x0']; ref = cstate = float(exact)
    bound = Q(0); max_sequence = Q(0); first = None; branch_disagreements = 0; branch_issues = 0
    original_bound_exceeded = False
    t0 = time.perf_counter()
    for i in range(horizon):
        u, dt = seq['step'](i)
        validate(float(ref), u, dt, False, root_spec)
        local = intent(Q(float(ref)), u, dt, False, cfg, float(limit))
        expected = intent(exact, u, dt, False, cfg, float(limit))
        actual = reference(float(ref), u, dt, False, cfg, float(limit))
        isolated = run(float(ref), u, dt)
        sequence = run(cstate, u, dt)
        assert struct.pack('3f', *isolated) == struct.pack('3f', *actual), 'isolated C differs from float32 bits'
        assert struct.pack('3f', *sequence) == struct.pack('3f', *isolated), 'stateful C differs from float32 bits'
        assert abs(Q(float(actual[0])) - local[0]) <= step_bound
        previous_bound = bound
        bound += step_bound
        err_sequence = abs(Q(sequence[0]) - expected[0])
        original_bound_exceeded |= err_sequence > bound
        branch_disagreements += tuple(expected[1:]) != tuple(actual[1:])
        alpha = Q(dt) / (Q(cfg['tau']) + Q(dt))
        delta = alpha * (Q(u) - exact)
        raw_radius = alpha * previous_bound + step_bound
        reached = exact + max(-Q(cfg['slew_down']) * Q(dt), min(Q(cfg['slew_up']) * Q(dt), delta))
        branch_issues += (min(abs(delta - Q(cfg['slew_up']) * Q(dt)), abs(delta + Q(cfg['slew_down']) * Q(dt))) <= raw_radius
                          or min(abs(reached - limit), abs(reached + limit)) <= bound)
        max_sequence = max(max_sequence, err_sequence)
        if first is None and err_sequence > ceiling:
            first = {'step': i + 1, 'abs_error': str(err_sequence)}
        exact, ref, cstate = expected[0], actual[0], sequence[0]
    wall = time.perf_counter() - t0
    return {'steps_executed': horizon, 'ceiling_crossed': first is not None, 'first_crossing': first,
            'max_abs_error_rad_s': str(max_sequence), 'max_abs_error_float': float(max_sequence),
            'original_horizon_bound_rad_s': str(bound), 'original_horizon_bound_exceeded': original_bound_exceeded,
            'branch_flag_disagreements': branch_disagreements, 'branch_threshold_contacts': branch_issues,
            'exact_intent_evaluations': 2 * horizon, 'binary32_reference_evaluations': horizon,
            'compiled_calls': 2 * horizon, 'wall_clock_s': wall}


def directed_long_horizon(seq, stop_on_first):
    """The active/qualify.py (run to end) or px4_domain/run.py (stop at first failure) loop."""
    exact = seq['x0']; native = rounded = float(exact)
    max_error = Q(0); first = None; mismatches = 0; calls = 0
    t0 = time.perf_counter()
    for i in range(seq['registered_steps']):
        u, dt = seq['step'](i)
        validate_step(native, u, dt, float(limit), float(Q(active_spec['input_abs_max'])),
                      float(Q(active_spec['dt_min_positive'])), float(Q(active_spec['dt_max'])))
        exact_out = intent(exact, u, dt, False, cfg, float(limit))
        c_out = run(native, u, dt)
        ref_out = reference(rounded, u, dt, False, cfg, float(limit))
        mismatches += struct.pack('3f', *c_out) != struct.pack('3f', *map(float, ref_out))
        exact, native, rounded = exact_out[0], c_out[0], float(ref_out[0]); calls += 1
        error = abs(Q(native) - exact)
        max_error = max(max_error, error)
        if first is None and error > ceiling:
            first = {'step': calls, 'abs_error': str(error), 'c_state': native}
            if stop_on_first:
                break
    wall = time.perf_counter() - t0
    ret = seq['retained']['first_exceed']
    retained_error = ret.get('abs_error', ret.get('error'))
    return {'steps_executed': calls, 'registered_steps': seq['registered_steps'], 'stops_on_first_failure': stop_on_first,
            'ceiling_crossed': first is not None, 'first_crossing': first,
            'max_abs_error_rad_s': str(max_error), 'max_abs_error_float': float(max_error),
            'c_reference_mismatches': mismatches,
            'retained_first_crossing': {'step': ret['step'], 'abs_error': retained_error},
            'matches_retained': first is not None and first['step'] == ret['step'] and first['abs_error'] == retained_error,
            'exact_intent_evaluations': calls, 'binary32_reference_evaluations': calls, 'compiled_calls': calls,
            'wall_clock_s': wall}


results = {}
for name, seq in sequences.items():
    results[name] = {'registered_horizon_b2b': registered_horizon_b2b(seq),
                     'directed_long_horizon': directed_long_horizon(seq, stop_on_first=(name == 'px4_timestamp_gap'))}
    assert results[name]['directed_long_horizon']['matches_retained'], name
    assert results[name]['directed_long_horizon']['c_reference_mismatches'] == 0

record = {
    'question': 'which boundary detects each retained binary32 active counterexample, at what execution cost',
    'detection_criterion': 'absolute next-state error against exact intent exceeds ' + active_spec['acceptance']['ceiling_rad_per_s'] + ' rad/s',
    'registration_sha256': sha(HERE / 'registration.json'),
    'driver_sha256': sha(__file__),
    'oracle_sha256': {'core.py': sha(ROOT / 'core.py'), 'active/boundary.py': sha(ROOT / 'active/boundary.py')},
    'source_sha256': sha(source), 'binary_sha256': sha(shared), 'compiler_command': command,
    'compiler': subprocess.check_output(['cc', '--version'], text=True).splitlines()[0],
    'compile_wall_clock_s': compile_s,
    'host': {'platform': platform.platform(), 'machine': platform.machine(),
             'cpu': subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], capture_output=True, text=True).stdout.strip(),
             'python': sys.version.split()[0]},
    'gap_dt_bits_le': {str(k): struct.pack('<f', v).hex() for k, v in gap_dt.items()},
    'sequences': results,
    'detected_by_registered_horizon_b2b': [n for n, r in results.items() if r['registered_horizon_b2b']['ceiling_crossed']],
    'detected_by_directed_long_horizon': [n for n, r in results.items() if r['directed_long_horizon']['ceiling_crossed']],
    'prediction_held': all(not r['registered_horizon_b2b']['ceiling_crossed'] and r['directed_long_horizon']['matches_retained']
                           for r in results.values()),
}
(HERE / 'results.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({n: {b: {k: r[b][k] for k in ('steps_executed', 'ceiling_crossed', 'first_crossing', 'max_abs_error_float', 'wall_clock_s')}
                      for b in r} for n, r in results.items()}, indent=2))
