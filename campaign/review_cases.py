"""Replay only the reviewed branch and zero-sign counterexamples. No held-out inputs."""
import hashlib
import json
from fractions import Fraction as Q
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import intent, reference, validate


SPEC = json.loads((ROOT / 'spec.json').read_text())
FLAGS = [flag for flag in SPEC['compiler_flags'] if flag not in ('-shared', '-fPIC')]
REVERSE = [
    ('zero_reset', 'bfd9ebe2', 'bf834628', '3d352dd2'),
    ('zero_reset', '3f9f8df1', '3f65de22', '3d49ee01'),
    ('tracking_reset', '3c06e32d', '3f9758b2', '3d32575f'),
    ('tracking_reset', '3f8f3bf2', '3f03e1aa', '3d54b1d4'),
]
ZERO = [
    ('zero_reset', 'hold', '80000000', '00000000', '00000000', False),
    ('tracking_reset', 'hold', '80000000', '00000000', '00000000', False),
    ('tracking_reset', 'reset', '00000000', '80000000', '3d800000', True),
    ('zero_reset', 'update', '80000000', '80000001', '37800000', False),
    ('tracking_reset', 'update', '80000000', '80000001', '37800000', False),
]


def value(bits):
    return struct.unpack('<f', bytes.fromhex(bits)[::-1])[0]


def bits(value):
    return f'{struct.unpack("<I", struct.pack("<f", float(value)))[0]:08x}'


def exact_step(x, u, dt, cfg):
    """Separate increment/projection derivation from the weighted-target intent."""
    x, u, dt = Q(x), Q(u), Q(dt)
    delta = dt * (u - x) / (Q(cfg['tau']) + dt)
    lo, hi = -Q(cfg['slew_down']) * dt, Q(cfg['slew_up']) * dt
    slew = -1 if delta < lo else 1 if delta > hi else 0
    reached = x + max(lo, min(hi, delta))
    clamp = -1 if reached < -2 else 1 if reached > 2 else 0
    return max(Q(-2), min(Q(2), reached)), slew, clamp


def native(exe, variant, x, u, dt, reset):
    line = f'{int(variant == "tracking_reset"):x} 1 {x} {x} {u} {dt} {int(reset):x}\n'
    run = subprocess.run([str(exe)], input=line, text=True, capture_output=True, check=True)
    state, slew, clamp, common_state, common_slew, common_clamp = run.stdout.split()
    assert (state, slew, clamp) == (common_state, common_slew, common_clamp)
    return state, int(value(slew)), int(value(clamp))


def main():
    sources = ('generated/zero_reset.c', 'generated/tracking_reset.c')
    with tempfile.TemporaryDirectory() as directory:
        exe = Path(directory) / 'review-cross-runner'
        compile_command = ['cc', *FLAGS, 'campaign/cross_runner.c', *sources, '-o', str(exe)]
        subprocess.run(compile_command, cwd=ROOT, capture_output=True, text=True, check=True)
        reverse = []
        for variant, xb, ub, hb in REVERSE:
            x, u, dt = value(xb), value(ub), value(hb)
            cfg = SPEC['variants'][variant]
            validate(x, u, dt, False, SPEC)
            exact = exact_step(x, u, dt, cfg)
            assert exact == intent(x, u, dt, False, cfg, 2.0)
            rounded = reference(x, u, dt, False, cfg, 2.0)
            c_state, c_slew, c_clamp = native(exe, variant, xb, ub, hb, False)
            assert exact[1:] == (0, 0)
            assert rounded[1:] == (c_slew, c_clamp)
            assert c_slew in (-1, 1) and c_clamp == 0
            assert c_state == bits(rounded[0])
            assert abs(Q(float(rounded[0])) - exact[0]) <= Q(32) * Q(SPEC['numerics']['unit_roundoff'])
            reverse.append(dict(variant=variant, x=xb, u=ub, dt=hb,
                                exact_flags=list(exact[1:]), reference_flags=list(rounded[1:]),
                                c_flags=[c_slew, c_clamp], c_state=c_state))
        zeros = []
        for variant, path, xb, ub, hb, reset in ZERO:
            x, u, dt = value(xb), value(ub), value(hb)
            cfg = SPEC['variants'][variant]
            validate(x, u, dt, reset, SPEC)
            exact = intent(x, u, dt, reset, cfg, 2.0)
            rounded = reference(x, u, dt, reset, cfg, 2.0)
            c_state, c_slew, c_clamp = native(exe, variant, xb, ub, hb, reset)
            assert bits(rounded[0]) == '80000000'
            assert c_state == '00000000'
            assert rounded[1:] == (c_slew, c_clamp) == (0, 0)
            assert exact[1:] == (0, 0)
            assert abs(Q(float(rounded[0])) - exact[0]) <= Q(32) * Q(SPEC['numerics']['unit_roundoff'])
            zeros.append(dict(variant=variant, path=path, x=xb, u=ub, dt=hb,
                              reset=reset, exact_state=str(exact[0]),
                              reference_state='80000000', c_state=c_state,
                              flags=[c_slew, c_clamp]))
    warnings = []
    for source in sources:
        command = ['cc', *FLAGS, '-Wfloat-equal', '-fsyntax-only', source]
        run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        assert run.returncode != 0 and '-Wfloat-equal' in run.stderr
        warnings.append(dict(source=source, exit_code=run.returncode,
                             error_count=run.stderr.count('error:'),
                             first_error=next(line for line in run.stderr.splitlines() if 'error:' in line)))
    compiler_version = subprocess.check_output(['cc', '--version'], text=True).splitlines()[0]
    print(json.dumps(dict(compiler=compiler_version, compiler_flags=FLAGS,
                          source_sha256={source: hashlib.sha256((ROOT / source).read_bytes()).hexdigest()
                                         for source in sources},
                          reverse_slew=reverse, negative_zero=zeros,
                          float_equal_werror=warnings), indent=2))


if __name__ == '__main__':
    main()
