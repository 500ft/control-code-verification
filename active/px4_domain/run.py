"""Replay registered PX4-tick development cases against strict C and exact intent."""
import ctypes as ct
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from core import intent, reference
from active.boundary import validate_step

sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
registration = json.loads((HERE / 'registration.json').read_text())
for name in ('spec.json', 'directed.json'):
    assert sha(HERE / name) == registration['sha256'][name]
spec = json.loads((HERE / 'spec.json').read_text())
cases = json.loads((HERE / 'directed.json').read_text())['cases']
build = ROOT / 'build' / 'px4-domain'
build.mkdir(parents=True, exist_ok=True)
probe = build / 'dt.c'
probe.write_text('#include <stdio.h>\n#include <stdint.h>\n#include <string.h>\nint main(void) { unsigned k[] = {125,126,2500,20000,30000}; for (unsigned i=0;i<5;i++) { float d=k[i]*1e-6f; if(d<0.000125f)d=0.000125f; if(d>0.02f)d=0.02f; uint32_t bits; memcpy(&bits,&d,4); printf("%u %08x\\n",k[i],bits); } }\n')
flags = ['-O2', '-fno-fast-math', '-ffp-contract=off', '-Wall', '-Wextra', '-Werror']
subprocess.run(['cc', '-std=c99', *flags, str(probe), '-o', str(build/'dt')], check=True)
dt_bits = {int(k): int(b, 16) for k,b in (line.split() for line in subprocess.check_output([str(build/'dt')], text=True).splitlines())}
dt = {k: struct.unpack('<f', struct.pack('<I', bits))[0] for k,bits in dt_bits.items()}
assert struct.pack('<f', dt[125]).hex() == spec['dt_min_bits_le']
assert struct.pack('<f', dt[30000]).hex() == spec['dt_max_bits_le']

source = ROOT / 'active/generated/active_symmetric.c'
binary = build / 'active_symmetric.so'
command = ['cc', '-std=c99', *flags, '-Wno-unused-parameter', '-shared', '-fPIC', str(source), '-o', str(binary)]
subprocess.run(command, check=True)
fn = ct.CDLL(str(binary)).active_symmetric
ptr = ct.POINTER(ct.c_float)
fn.argtypes = [ct.POINTER(ptr), ct.POINTER(ptr), ct.POINTER(ct.c_longlong), ptr, ct.c_int]
fn.restype = ct.c_int
def step(x,u,h,reset=False):
    arg=(ct.c_float*4)(x,u,h,reset)
    out=(ct.c_float*3)()
    assert fn((ptr*1)(arg),(ptr*1)(out),None,None,0)==0
    return tuple(out)

cfg=dict(tau=0.25,slew_up=2.0,slew_down=2.0,reset_tracks_input=False)
ceiling=Q(spec['ceiling_rad_per_s'])
results=[]
for case in sorted(cases, key=lambda c: c['repetitions']):
    exact=Q(case['x0']); native=float(exact); rounded=float(exact)
    max_error=Q(0); first=None; calls=0; mismatches=0; flags={}
    for repeat in range(case['repetitions']):
        for u_text,k in zip(case['commands'],case['delta_us']):
            u=Q(u_text); h=dt[k]
            validate_step(native,float(u),h,2.,8.,dt[125],dt[30000])
            exact_out=intent(exact,u,Q(h),False,cfg,Q(2))
            c_out=step(native,float(u),h)
            ref_out=reference(rounded,float(u),h,False,cfg,2.)
            mismatches += struct.pack('<3f',*c_out)!=struct.pack('<3f',*map(float,ref_out))
            exact,native,rounded=exact_out[0],c_out[0],float(ref_out[0]); calls+=1
            flags[str(tuple(int(v) for v in c_out[1:]))]=flags.get(str(tuple(int(v) for v in c_out[1:])),0)+1
            error=abs(Q(native)-exact)
            max_error=max(max_error,error)
            if first is None and error>ceiling:
                first={'step':calls,'elapsed_s':str(sum(Q(dt[k2]) for k2 in case['delta_us'])*(repeat) + sum(Q(dt[k2]) for k2 in case['delta_us'][:(calls-1)%len(case['commands'])+1])), 'error':str(error), 'c_state':native,'exact_state':str(exact)}
                break
        if first: break
    results.append({'id':case['id'],'steps_executed':calls,'first_exceed':first,'max_abs_error':str(max_error),'c_reference_mismatches':mismatches,'flags':flags})
    if first: break

# Separate, explicitly non-PX4-Run calls and admission boundary checks.
controls={'hold':step(1.,8.,0.)[0]==1.,'reset':step(1.,8.,dt[125],True)[0]==0.}
for value in (0.,dt[125]/2,dt[30000]*2):
    try: validate_step(0.,1.,value,2.,8.,dt[125],dt[30000]); rejected=False
    except ValueError: rejected=True
    controls['rejected_dt_'+str(value)]=rejected
assert all(controls.values()) and all(r['c_reference_mismatches']==0 for r in results)
out={'registration_sha256':sha(HERE/'registration.json'),'runner_sha256':sha(__file__),'source_sha256':sha(source),'binary_sha256':sha(binary),'compiler':subprocess.check_output(['cc','--version'],text=True).splitlines()[0],'command':command,'dt_bits':{str(k):f'{v:08x}' for k,v in dt_bits.items()},'cases':results,'controls':controls,'stopped_on_first_failure':any(r['first_exceed'] for r in results)}
(HERE/'results.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'cases_executed':len(results),'steps_executed':sum(r['steps_executed'] for r in results),'first_failure':next((r['first_exceed'] for r in results if r['first_exceed']),None)},indent=2))
