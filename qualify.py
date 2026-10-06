"""Execute frozen development traces. Never reads the withheld final cases."""
import csv
import ctypes as ct
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import platform
import re
import struct
import subprocess
import sys
import time
import casadi
import numpy as np
from core import intent, reference, validate

ROOT = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def analytic_checks(spec):
    limit = spec['domain']['state_abs_max']
    for cfg in spec['variants'].values():
        dt, u, x = Q(1,32), Q(1,2), Q(0)
        ratio = Q(cfg['tau'])/(Q(cfg['tau'])+dt)
        for n in range(1,65):
            x = intent(x,u,dt,False,cfg,limit)[0]
            assert x == u*(1-ratio**n), 'closed-form unsaturated step'
        x = Q(0)
        for n in range(1,33):
            x = intent(x,Q(8),dt,False,cfg,limit)[0]
            assert x == min(Q(limit), n*Q(cfg['slew_up'])*dt), 'positive slew ramp and saturation'
        x = Q(0)
        for n in range(1,65):
            x = intent(x,Q(-8),dt,False,cfg,limit)[0]
            assert x == max(-Q(limit), -n*Q(cfg['slew_down'])*dt), 'negative slew ramp and saturation'
        assert intent(Q(1),Q(-8),0,False,cfg,limit)[0] == 1
        expected = -Q(limit) if cfg['reset_tracks_input'] else Q(0)
        assert intent(Q(1),Q(-8),0,True,cfg,limit)[0] == expected
        assert intent(Q(1),Q(-8),dt,True,cfg,limit)[0] == expected
        assert intent(Q(1,2),Q(1,2),dt,False,cfg,limit)[0] == Q(1,2)
    rejected = 0
    for args in [(0,float('nan'),0,True),(0,0,-.1,False),(3,0,0,False),
                 (0,9,0,False),(0,0,1e-9,False),(0,0,.1,False),(0,0,0,1),(0,.1,0,False)]:
        try:
            validate(*args,spec)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError('invalid input admitted')
    return {'closed_form_step':True,'asymmetric_slew_ramps':True,'zero_dt_hold':True,
            'reset_precedes_hold_and_update':True,'equilibrium':True,'invalid_inputs_rejected':rejected}


def compiled(name, spec, build):
    src = ROOT/'generated'/f'{name}.c'
    target = build/f'{name}.so'
    command = ['cc',*spec['compiler_flags'],str(src),'-o',str(target)]
    subprocess.run(command,check=True,capture_output=True)
    ir = build/f'{name}.ll'
    subprocess.run(['cc','-O2','-fno-fast-math','-ffp-contract=off','-S','-emit-llvm',str(src),'-o',str(ir)],check=True,capture_output=True)
    llvm = ir.read_text()
    assert '#define casadi_real float' in src.read_text()
    assert not re.search(r'\b(?:fadd|fsub|fmul|fdiv|fcmp)\s+\w*\s*double\b',llvm), 'double arithmetic found'
    assert not re.search(r'\b(?:fast|reassoc|contract)\b', '\n'.join(l for l in llvm.splitlines() if re.search(r'\bf(?:add|sub|mul|div)\b',l)))
    lib = ct.CDLL(str(target))
    fn = getattr(lib,name)
    fp = ct.POINTER(ct.c_float)
    fn.argtypes = [ct.POINTER(fp),ct.POINTER(fp),ct.POINTER(ct.c_longlong),fp,ct.c_int]
    fn.restype = ct.c_int
    def run(x,u,dt,reset):
        a = (ct.c_float*4)(x,u,dt,reset)
        b = (ct.c_float*3)()
        assert fn((fp*1)(a),(fp*1)(b),None,None,0) == 0
        return tuple(b)
    return run, {'source_sha256':sha(src),'command':command,'binary_sha256':sha(target),
                 'llvm_sha256':sha(ir),'float_arithmetic_ops':len(re.findall(r'\bf(?:add|sub|mul|div) float\b',llvm)),
                 'double_arithmetic':False,'fast_math_or_contraction':False}


def main():
    start = time.perf_counter()
    spec = json.loads((ROOT/'spec.json').read_text())
    registration = json.loads((ROOT/'registration.json').read_text())
    for file in ('spec.json','traces.json'):
        assert sha(ROOT/file) == registration['sha256'][file], 'freeze changed'
    traces = json.loads((ROOT/'traces.json').read_text())
    build = ROOT/'build'; build.mkdir(exist_ok=True)
    evidence = ROOT/'evidence'; evidence.mkdir(exist_ok=True)
    analytic = analytic_checks(spec)
    step_bound = Q(spec['numerics']['local_error_coefficient'])*Q(spec['numerics']['unit_roundoff'])
    rows, builds, findings = [], {}, []
    max_step = max_sequence = 0.
    branch_disagreements = 0
    for name,cfg in spec['variants'].items():
        run, builds[name] = compiled(name,spec,build)
        limit = spec['domain']['state_abs_max']
        for trace in traces:
            exact = Q(trace['initial']); ref = cstate = trace['initial']
            bound = Q(0); t = 0.
            assert len(trace['steps']) <= spec['domain']['steps_max']
            for i,s in enumerate(trace['steps']):
                u,dt,reset = s['u'],s['dt'],s['reset']
                validate(float(ref),u,dt,reset,spec)
                local = intent(Q(float(ref)),u,dt,reset,cfg,limit)
                expected = intent(exact,u,dt,reset,cfg,limit)
                actual = reference(ref,u,dt,reset,cfg,limit)
                isolated = run(ref,u,dt,reset)
                sequence = run(cstate,u,dt,reset)
                assert struct.pack('3f',*isolated) == struct.pack('3f',*actual), 'isolated C differs from float32 bits'
                assert struct.pack('3f',*sequence) == struct.pack('3f',*isolated), 'stateful C differs from float32 bits'
                err_step = abs(Q(float(actual[0]))-local[0])
                assert err_step <= step_bound
                previous_bound = bound
                bound = Q(0) if reset else bound+(step_bound if dt else 0)
                err_sequence = abs(Q(sequence[0])-expected[0])
                assert err_sequence <= bound
                branch_disagreements += tuple(expected[1:]) != tuple(actual[1:])
                # The raw delta uncertainty includes prior-state error and local arithmetic.
                # Its sensitivity to state is alpha <= 1; reached state is nonexpansive.
                risks = []
                if not reset and dt:
                    alpha = Q(dt)/(Q(cfg['tau'])+Q(dt))
                    delta = alpha*(Q(u)-exact)
                    raw_radius = alpha*previous_bound+step_bound
                    if min(abs(delta-Q(cfg['slew_up'])*Q(dt)),abs(delta+Q(cfg['slew_down'])*Q(dt))) <= raw_radius:
                        risks.append('slew branch interval touches threshold')
                    reached = exact+max(-Q(cfg['slew_down'])*Q(dt),min(Q(cfg['slew_up'])*Q(dt),delta))
                    if min(abs(reached-Q(limit)),abs(reached+Q(limit))) <= bound:
                        risks.append('rate clamp interval touches threshold')
                if risks:
                    findings.append({'variant':name,'trace':trace['name'],'step':i,'issues':risks})
                t += dt
                rows.append(dict(variant=name,trace=trace['name'],step=i,time_s=t,input_rad_s=u,dt_s=dt,reset=reset,
                                 intent_rad_s=float(expected[0]),float32_rad_s=float(actual[0]),c_rad_s=sequence[0],
                                 abs_error_rad_s=float(err_sequence),bound_rad_s=float(bound),branch_issue=bool(risks)))
                max_step=max(max_step,float(err_step)); max_sequence=max(max_sequence,float(err_sequence))
                exact,ref,cstate=expected[0],actual[0],sequence[0]
    with (evidence/'traces.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    result={'status':'numerical agreement passed; branch requirements unresolved',
            'analytic_checks':analytic,'development_sequences':len(traces)*len(spec['variants']),
            'evaluated_steps':len(rows),'independent_ports':None,'c_float32_bit_exact':True,
            'max_isolated_error_rad_s':max_step,'max_stateful_error_rad_s':max_sequence,
            'max_horizon_bound_rad_s':float(step_bound*spec['domain']['steps_max']),
            'branch_disagreements':branch_disagreements,'branch_requirement_issues':findings,
            'integration_qualified':False,'withheld_executed':False,'px4_replay_executed':False,
            'elapsed_generation_excluded_s':time.perf_counter()-start,
            'environment':{'python':sys.version,'numpy':np.__version__,'casadi':casadi.__version__,
                           'platform':platform.platform(),'compiler':subprocess.check_output(['cc','--version'],text=True).strip()},
            'builds':builds,'sha256':{f:sha(ROOT/f) for f in ['spec.json','traces.json','registration.json','core.py','generate.py','qualify.py','evidence/traces.csv']}}
    (evidence/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['builds','sha256','environment','branch_requirement_issues']},indent=2))
    print('branch requirement issue steps:',len(findings))


if __name__ == '__main__':
    main()
