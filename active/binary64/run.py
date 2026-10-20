"""Execute preregistered binary64 active development cases."""
import ctypes as ct
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import platform
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from core import intent
from active.binary64.reference import f32, initialize, step as reference_step

sha=lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
registration=json.loads((HERE/'registration.json').read_text())
for name,expected in registration['sha256'].items():
    assert sha(HERE/name)==expected, name
spec=json.loads((HERE/'spec.json').read_text())
cases=json.loads((HERE/'directed.json').read_text())['cases']
supplemental_registration=json.loads((HERE/'registration-supplemental.json').read_text())
assert sha(HERE/'supplemental-directed.json')==supplemental_registration['sha256']
supplemental=json.loads((HERE/'supplemental-directed.json').read_text())
assert spec['variant']=='active_symmetric_binary64_state'
build=ROOT/'build/binary64'
build.mkdir(parents=True,exist_ok=True)
source=HERE/'generated/active_symmetric_binary64_state.c'
shared=build/'active_symmetric_binary64_state.so'
flags=['-std=c99','-O2','-fno-fast-math','-fno-associative-math','-fno-reciprocal-math',
       '-fsigned-zeros','-ftrapping-math','-ffp-contract=off','-Wall','-Wextra','-Werror','-Wno-float-equal']
shared_command=['cc',*flags,'-shared','-fPIC',str(source),'-o',str(shared)]
subprocess.run(shared_command,check=True,capture_output=True)

class State(ct.Structure): _fields_=[('x',ct.c_double),('initialized',ct.c_int)]
class Output(ct.Structure): _fields_=[('published',ct.c_float),('slew_flag',ct.c_int),('clamp_flag',ct.c_int),('status',ct.c_int)]
lib=ct.CDLL(str(shared))
lib.active_double_init.argtypes=[ct.POINTER(State),ct.c_float]
lib.active_double_init.restype=ct.c_int
lib.active_double_reset.argtypes=[ct.POINTER(State)]
lib.active_double_step.argtypes=[ct.POINTER(State),ct.c_float,ct.c_float]
lib.active_double_step.restype=Output

def inputs(case):
    kind=case['kind']
    if kind=='constant':
        for _ in range(case['steps']): yield f32(float(Q(case['u']))),f32(float(Q(case['dt'])))
    elif kind=='alternating':
        hs=[struct.unpack('<f',struct.pack('<I',int(b,16)))[0] for b in case['dt_bits_hex']]
        for i in range(case['steps']): yield f32(float(Q(case['commands'][i%2]))),hs[i%2]
    elif kind=='list':
        for u in case['commands']: yield f32(float(Q(u))),f32(float(Q(case['dt'])))
    elif kind=='paired':
        for _ in range(case['repetitions']):
            for u,h in zip(case['commands'],case['dts']): yield f32(float(Q(u))),f32(float(Q(h)))
    else: raise ValueError(kind)

cfg={'tau':0.25,'slew_up':2.0,'slew_down':2.0,'reset_tracks_input':False}
ceiling=Q(spec['acceptance']['ceiling_rad_per_s'])
results=[]
for case in cases:
    if case['kind']=='compiled_horizon': continue
    state=State(); initial=f32(float(Q(case['x0'])))
    assert lib.active_double_init(ct.byref(state),initial)==0
    ref=initialize(initial); exact=Q(initial)
    max_state=Q(0); max_published=Q(0); first=None; calls=0
    state_mismatch=published_mismatch=flag_mismatch=exact_flag_mismatch=0
    exact_steps=0
    for command,dt in inputs(case):
        native=lib.active_double_step(ct.byref(state),command,dt)
        try:
            ref,ref_published,ref_slew,ref_clamp,ref_status=reference_step(ref,command,dt)
        except ValueError as exc:
            raise ValueError(f"{case['id']} step {calls+1}: x={ref}, u={command}, dt={dt}") from exc
        state_mismatch+=struct.pack('<d',state.x)!=struct.pack('<d',ref)
        published_mismatch+=struct.pack('<f',native.published)!=struct.pack('<f',ref_published)
        flag_mismatch+=(native.slew_flag,native.clamp_flag,native.status)!=(ref_slew,ref_clamp,ref_status)
        assert native.status==0
        calls+=1
        # A finite exact replay for all known counterexamples. The jitter case
        # uses only a short exact prefix to avoid explosive rational denominators.
        if case['kind']!='paired' or calls<=64:
            exact_out=intent(exact,Q(command),Q(dt),False,cfg,Q(2))
            exact=exact_out[0]; exact_steps+=1
            exact_flag_mismatch+=(native.slew_flag,native.clamp_flag)!=tuple(exact_out[1:])
            state_error=abs(Q(state.x)-exact)
            published_error=abs(Q(native.published)-exact)
            max_state=max(max_state,state_error); max_published=max(max_published,published_error)
            if first is None and (state_error>ceiling or published_error>ceiling):
                first={'step':calls,'state_error':str(state_error),'published_error':str(published_error)}
    results.append({'id':case['id'],'steps':calls,'exact_steps':exact_steps,
                    'max_state_error':str(max_state),'max_published_error':str(max_published),
                    'first_exceed':first,'state_reference_mismatches':state_mismatch,
                    'published_reference_mismatches':published_mismatch,
                    'flag_reference_mismatches':flag_mismatch,
                    'exact_flag_differences':exact_flag_mismatch})

# Registered post-review subnormal state case, counted separately.
supplemental_results=[]
for case in supplemental['cases']:
    assert case['kind']=='subnormal'
    initial=struct.unpack('<f',struct.pack('<I',int(case['x0_float32_bits'],16)))[0]
    command=f32(float(Q(case['u']))); dt=f32(float(Q(case['dt'])))
    state=State(); assert lib.active_double_init(ct.byref(state),initial)==0
    ref=initialize(initial); exact=Q(initial)
    nonzero_subnormal_steps=0; first_subnormal_step=None
    max_state=Q(0); max_published=Q(0)
    mismatches=0
    for i in range(1,case['steps']+1):
        out=lib.active_double_step(ct.byref(state),command,dt)
        ref,pub,rs,rc,status=reference_step(ref,command,dt)
        mismatches+=struct.pack('<d',state.x)!=struct.pack('<d',ref)
        mismatches+=struct.pack('<f',out.published)!=struct.pack('<f',pub)
        mismatches+=(out.slew_flag,out.clamp_flag,out.status)!=(rs,rc,status)
        if 0<abs(state.x)<sys.float_info.min:
            nonzero_subnormal_steps+=1
            if first_subnormal_step is None: first_subnormal_step=i
        if i<=case['exact_prefix_steps']:
            exact=intent(exact,Q(command),Q(dt),False,cfg,Q(2))[0]
            max_state=max(max_state,abs(Q(state.x)-exact))
            max_published=max(max_published,abs(Q(out.published)-exact))
    assert mismatches==0 and first_subnormal_step is not None
    assert max_state<=ceiling and max_published<=ceiling
    supplemental_results.append({'id':case['id'],'steps':case['steps'],
        'exact_steps':case['exact_prefix_steps'],'first_nonzero_binary64_subnormal_step':first_subnormal_step,
        'nonzero_binary64_subnormal_steps':nonzero_subnormal_steps,'final_state_hex':state.x.hex(),
        'max_exact_prefix_state_error':str(max_state),'max_exact_prefix_published_error':str(max_published),
        'c_reference_mismatches':mismatches})

# Separate boundary operations. A rejected call must leave the persistent state unchanged.
controls={}
state=State()
controls['uninitialized_rejected']=lib.active_double_step(ct.byref(state),1.,1/512).status==-1
controls['init_at_cap']=lib.active_double_init(ct.byref(state),2.)==0 and state.x==2.
controls['init_beyond_cap_rejected']=lib.active_double_init(ct.byref(state),2.25)==-1 and state.x==2.
controls['nan_init_rejected']=lib.active_double_init(ct.byref(state),float('nan'))==-1 and state.x==2.
hold=lib.active_double_step(ct.byref(state),1.,0.)
controls['hold_unchanged']=hold.status==1 and state.x==2. and hold.published==2.
controls['negative_zero_dt_hold']=lib.active_double_step(ct.byref(state),1.,-0.).status==1 and state.x==2.
for name,u,h in [('nan',float('nan'),1/512),('infinite_command',float('inf'),1/512),
                 ('command',9.,1/512),('small_dt',1.,1/131072),('large_dt',1.,1/8),
                 ('infinite_dt',1.,float('inf'))]:
    controls[name+'_rejected']=lib.active_double_step(ct.byref(state),u,h).status==-1 and state.x==2.
controls['init_negative_cap']=lib.active_double_init(ct.byref(state),-2.)==0 and state.x==-2.
lib.active_double_reset(ct.byref(state))
controls['disarm_zero']=state.x==0. and state.initialized==1
# The first old tie increment is representable in binary64, but its published
# binary32 value is rounded. The second step must use the persistent double.
tie=f32(float(Q('513/33554432')))
assert lib.active_double_init(ct.byref(state),1.)==0
out=lib.active_double_step(ct.byref(state),8.,tie)
saved=state.x
next_reference=reference_step(saved,8.,tie)[0]
lib.active_double_step(ct.byref(state),8.,tie)
controls['persistent_state_excludes_published_feedback']=saved!=float(out.published) and state.x==next_reference

horizon_case=next(c for c in cases if c['kind']=='compiled_horizon')
horizon_bin=build/'horizon'
horizon_command=['cc',*flags,'-I',str(HERE),str(HERE/'horizon.c'),str(source),'-o',str(horizon_bin)]
subprocess.run(horizon_command,check=True,capture_output=True)
horizon=json.loads(subprocess.check_output([str(horizon_bin)],text=True))
assert horizon['steps']==horizon_case['steps'] and Q(horizon['elapsed_s'])==Q(horizon_case['steps'])*Q(horizon_case['dt'])
assert horizon['checksum']==2*horizon['steps']
assert Q(horizon['state'])==Q(horizon_case['exact_even_state'])
assert all(controls.values())
assert all(not r['first_exceed'] and not r['state_reference_mismatches'] and
           not r['published_reference_mismatches'] and not r['flag_reference_mismatches'] for r in results)
record={'registration_sha256':sha(HERE/'registration.json'),'generator_sha256':sha(HERE/'generate.py'),
        'supplemental_registration_sha256':sha(HERE/'registration-supplemental.json'),
        'reference_sha256':sha(HERE/'reference.py'),'runner_sha256':sha(__file__),
        'source_sha256':sha(source),'shared_binary_sha256':sha(shared),'horizon_binary_sha256':sha(horizon_bin),
        'compiler':subprocess.check_output(['cc','--version'],text=True).splitlines()[0],
        'platform':platform.platform(),'command':shared_command,'horizon_command':horizon_command,
        'cases':results,'supplemental_cases':supplemental_results,'controls':controls,'horizon':horizon,
        'universal_state_bound':str(117964800*(24*Q(1,2**53)+36*Q(1,2**1075))),
        'universal_published_bound':str(117964800*(24*Q(1,2**53)+36*Q(1,2**1075))+Q(1,2**24)),
        'target_build_qualified':False,'scoped_claude_review_complete':False,'wrapper_admitted':False,'final_cases_opened':False}
(HERE/'results.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'directed_cases':len(results),'supplemental_cases':len(supplemental_results),
                  'steps':sum(r['steps'] for r in results),
                  'horizon_steps':horizon['steps'],'controls_passed':sum(controls.values()),
                  'exact_failures':[r['id'] for r in results if r['first_exceed']]},indent=2))
