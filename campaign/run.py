"""One-worker development comparison, with first-failure stop and external output."""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[key]='1'
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import resource
import struct
import subprocess
import sys
import time
from fractions import Fraction as Q
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import intent, reference, validate
from qualify import ROOT, analytic_checks, compiled, sha


def rss():
    value=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform=='darwin' else value*1024


def pack(values):
    return struct.pack('>3f',*values).hex()


def benchmark(cases,spec):
    start=time.monotonic();steps=largest=0
    for case in cases:
        if case['stratum']!='smooth_growth':
            continue
        state=Q(case['initial']);cfg=spec['variants'][case['variant']]
        for s in case['steps']:
            state=intent(state,s['u'],s['dt'],s['reset'],cfg,spec['domain']['state_abs_max'])[0]
            largest=max(largest,state.numerator.bit_length(),state.denominator.bit_length())
            steps+=1
    return dict(steps=steps,seconds=time.monotonic()-start,max_rational_bits=largest,peak_rss_bytes=rss())


def main():
    parser=argparse.ArgumentParser();parser.add_argument('inputs',type=Path);parser.add_argument('out',type=Path)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    start=time.monotonic();spec=json.loads((ROOT/'spec.json').read_text());design=json.loads((ROOT/'campaign/design.json').read_text())
    # Input sizes are bounded by the frozen tranche; never load withheld inputs.
    cases=[json.loads(line) for line in args.inputs.read_text().splitlines()]
    for c in cases:
        assert len(c['steps'])<=spec['domain']['steps_max']
        for s in c['steps']:
            validate(c['initial'],s['u'],s['dt'],s['reset'],spec)
    analytic=analytic_checks(spec)
    control=args.out/'controls'
    command=['cc',*[f for f in spec['compiler_flags'] if f not in ('-shared','-fPIC')],str(ROOT/'campaign/arithmetic_controls.c'),'-o',str(control)]
    subprocess.run(command,check=True,capture_output=True)
    completed=subprocess.run([str(control)],capture_output=True,text=True)
    controls=dict(command=command,binary_sha256=sha(control),exit_code=completed.returncode,output=completed.stdout,stderr=completed.stderr)
    (args.out/'controls.json').write_text(json.dumps(controls,indent=2)+'\n')
    assert completed.returncode==0,'arithmetic controls failed'
    cost=benchmark(cases,spec)
    print(json.dumps({'benchmark':cost}),flush=True)
    runs={};builds={}
    for name in spec['variants']:
        runs[name],builds[name]=compiled(name,spec,args.out)
    local=Q(spec['numerics']['local_error_coefficient'])*Q(spec['numerics']['unit_roundoff'])
    summary=dict(status='executed',input_sha256=sha(args.inputs),input_traces=len(cases),input_steps=sum(len(c['steps']) for c in cases),
                 attempted_traces=0,executed_traces=0,executed_steps=0,invalid_inputs=0,
                 branch_disagreement_steps=0,c_reference_bit_disagreements=0,numeric_bound_violations=0,
                 nonzero_state_error_steps=0,max_local_error_rad_s=0.,max_stateful_error_rad_s=0.,max_rational_bits=0,
                 per_stratum={},analytic_checks=analytic,benchmark=cost,builds=builds,
                 exact_policy='all executed steps; isolated and stateful',withheld_executed=False,integration_qualified=False)
    failure=None
    with gzip.open(args.out/'outputs.jsonl.gz','wt') as out:
        for case in cases:
            summary['attempted_traces']+=1
            cfg=spec['variants'][case['variant']];run=runs[case['variant']]
            exact=Q(case['initial']);ref=cstate=case['initial'];bound=Q(0)
            group=summary['per_stratum'].setdefault(case['stratum'],dict(traces=0,steps=0,branch_disagreements=0))
            group['traces']+=1
            for i,s in enumerate(case['steps']):
                validate(float(ref),s['u'],s['dt'],s['reset'],spec)
                expected=intent(exact,s['u'],s['dt'],s['reset'],cfg,spec['domain']['state_abs_max'])
                isolated_exact=intent(Q(float(ref)),s['u'],s['dt'],s['reset'],cfg,spec['domain']['state_abs_max'])
                actual=reference(ref,s['u'],s['dt'],s['reset'],cfg,spec['domain']['state_abs_max'])
                isolated=run(ref,s['u'],s['dt'],s['reset']);native=run(cstate,s['u'],s['dt'],s['reset'])
                bound=Q(0) if s['reset'] else bound+(local if s['dt'] else 0)
                le=abs(Q(float(actual[0]))-isolated_exact[0]);se=abs(Q(native[0])-expected[0])
                bit_mismatch=pack(actual)!=pack(isolated) or pack(isolated)!=pack(native)
                branch=tuple(expected[1:])!=tuple(actual[1:]);violation=le>local or se>bound
                summary['executed_steps']+=1;group['steps']+=1
                summary['branch_disagreement_steps']+=branch;group['branch_disagreements']+=branch
                summary['c_reference_bit_disagreements']+=bit_mismatch;summary['numeric_bound_violations']+=violation
                summary['nonzero_state_error_steps']+=se!=0
                summary['max_local_error_rad_s']=max(summary['max_local_error_rad_s'],float(le))
                summary['max_stateful_error_rad_s']=max(summary['max_stateful_error_rad_s'],float(se))
                summary['max_rational_bits']=max(summary['max_rational_bits'],expected[0].numerator.bit_length(),expected[0].denominator.bit_length())
                row=dict(id=case['id'],step=i,input=s,prior_c=cstate,intent=float(expected[0]),exact_flags=expected[1:],
                         reference_bits=pack(actual),isolated_c_bits=pack(isolated),stateful_c_bits=pack(native),
                         local_error=float(le),stateful_error=float(se),bound=float(bound),branch_disagreement=branch)
                out.write(json.dumps(row)+'\n')
                if bit_mismatch or violation:
                    failure=dict(case=case,failing_step=i,prefix=case['steps'][:i+1],observation=row,
                                 exact_state=str(expected[0]),classification='unclassified implementation/representation disagreement' if bit_mismatch else 'numeric bound violation')
                    summary['status']='stopped_at_first_disagreement';break
                exact,ref,cstate=expected[0],actual[0],native[0]
            if failure:
                break
            summary['executed_traces']+=1
            print(json.dumps(dict(trace=case['id'],steps=summary['executed_steps'],elapsed_s=time.monotonic()-start,rss_bytes=rss())),flush=True)
            if time.monotonic()-start>design['resources']['max_seconds']-60 or rss()>design['resources']['target_rss_bytes']:
                summary['status']='resource_stop';break
    if failure:
        (args.out/'failure.json').write_text(json.dumps(failure,indent=2)+'\n')
    summary.update(elapsed_s=time.monotonic()-start,peak_rss_bytes=rss(),raw_sha256=sha(args.out/'outputs.jsonl.gz'),
                   artifact_bytes=sum(p.stat().st_size for p in args.out.iterdir() if p.is_file()),next_trace_index=summary['executed_traces'])
    (args.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('builds','per_stratum','analytic_checks')}),flush=True)


if __name__=='__main__':
    main()
