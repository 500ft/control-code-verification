"""Supplemental observation: preserve independent histories and every discrepancy."""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[key]='1'
import argparse
from collections import Counter
from fractions import Fraction as Q
import gzip
import json
import math
from pathlib import Path
import struct
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import intent, reference, validate
from qualify import ROOT, compiled, sha
from campaign.run import rss


def bits(values):
    return struct.pack('>3f',*values).hex()


def difference(a,b,suffix):
    labels=[]
    if a[0]!=b[0]: labels.append('numeric_'+suffix)
    elif bits((a[0],0,0))!=bits((b[0],0,0)): labels.append('signed_zero_'+suffix)
    if tuple(a[1:])!=tuple(b[1:]): labels.append('branch_'+suffix)
    return labels


def evaluate(case,runs,spec):
    cfg=spec['variants'][case['variant']];limit=spec['domain']['state_abs_max']
    exact=Q(case['initial']);ref=native=case['initial'];bound=Q(0)
    local=Q(spec['numerics']['local_error_coefficient'])*Q(spec['numerics']['unit_roundoff'])
    for i,s in enumerate(case['steps']):
        try:
            validate(float(ref),s['u'],s['dt'],s['reset'],spec)
            validate(float(native),s['u'],s['dt'],s['reset'],spec)
            exact_out=intent(exact,s['u'],s['dt'],s['reset'],cfg,limit)
            exact_local=intent(Q(float(ref)),s['u'],s['dt'],s['reset'],cfg,limit)
            native_local=exact_local if native==float(ref) else intent(Q(native),s['u'],s['dt'],s['reset'],cfg,limit)
            ref_out=reference(ref,s['u'],s['dt'],s['reset'],cfg,limit)
            common=runs[case['variant']](ref,s['u'],s['dt'],s['reset'])
            native_out=runs[case['variant']](native,s['u'],s['dt'],s['reset'])
            if not all(math.isfinite(float(v)) for v in (*ref_out,*common,*native_out)):
                raise ValueError('nonfinite output')
            bound=Q(0) if s['reset'] else bound+(local if s['dt'] else 0)
            local_errors=[abs(Q(float(ref_out[0]))-exact_local[0]),abs(Q(common[0])-exact_local[0]),abs(Q(native_out[0])-native_local[0])]
            state_errors=[abs(Q(float(ref_out[0]))-exact_out[0]),abs(Q(native_out[0])-exact_out[0])]
            labels=difference(ref_out,common,'common')+difference(ref_out,native_out,'rollout')
            if tuple(exact_out[1:])!=tuple(ref_out[1:]) or tuple(exact_out[1:])!=tuple(native_out[1:]):
                labels.append('branch_requirement')
            if max(local_errors)>local or max(state_errors)>bound: labels.append('numeric_bound')
            if any(abs(float(v[0]))>limit for v in (ref_out,common,native_out)): labels.append('unclassified')
            yield dict(step=i,prior_reference=float(ref),prior_native=native,exact_state=float(exact_out[0]),
                       exact_flags=exact_out[1:],reference_bits=bits(ref_out),common_c_bits=bits(common),native_bits=bits(native_out),
                       local_errors=list(map(float,local_errors)),state_errors=list(map(float,state_errors)),bound=float(bound),
                       rational_bits=max(exact_out[0].numerator.bit_length(),exact_out[0].denominator.bit_length()),classes=labels)
            if 'unclassified' in labels:return
            exact,ref,native=exact_out[0],ref_out[0],native_out[0]
        except (ValueError,OverflowError) as error:
            yield dict(step=i,classes=['unclassified'],error=str(error));return


def main():
    p=argparse.ArgumentParser();p.add_argument('inputs',type=Path);p.add_argument('out',type=Path);args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    spec=json.loads((ROOT/'spec.json').read_text());design=json.loads((ROOT/'campaign/observational-design.json').read_text())
    runs={};builds={};start=time.monotonic()
    for name in spec['variants']: runs[name],builds[name]=compiled(name,spec,args.out)
    summary=dict(status='running',input_sha256=sha(args.inputs),attempted_traces=0,completed_traces=0,invalid_traces=0,
                 evaluated_steps=0,exact_stateful_steps=0,ordinary_rounding_steps=0,step_classes=Counter(),trace_classes=Counter(),
                 per_stratum={},max_local_error_rad_s=0.,max_stateful_error_rad_s=0.,max_rational_bits=0,builds=builds,
                 source_sha256={f:sha(ROOT/f) for f in ('campaign/observe.py','campaign/observational-design.json','campaign/generate_cases.py','spec.json','core.py','generated/zero_reset.c','generated/tracking_reset.c')})
    representatives={}
    with args.inputs.open() as inputs, gzip.open(args.out/'rows.jsonl.gz','wt') as raw, gzip.open(args.out/'discrepancies.jsonl.gz','wt') as issues, (args.out/'traces.jsonl').open('w') as traces:
        for line in inputs:
            case=json.loads(line);summary['attempted_traces']+=1
            key=case['variant']+'/'+case['stratum'];group=summary['per_stratum'].setdefault(key,dict(traces=0,steps=0,step_classes=Counter(),trace_classes=Counter()))
            group['traces']+=1;labels=set();count=0
            try:
                assert len(case['steps'])<=spec['domain']['steps_max']
                for s in case['steps']:validate(case['initial'],s['u'],s['dt'],s['reset'],spec)
                for row in evaluate(case,runs,spec):
                    row['id']=case['id'];count+=1;group['steps']+=1;summary['evaluated_steps']+=1
                    labels.update(row['classes']);summary['step_classes'].update(row['classes']);group['step_classes'].update(row['classes'])
                    if 'state_errors' in row:
                        summary['exact_stateful_steps']+=1
                        summary['ordinary_rounding_steps']+=max(row['state_errors'])>0 and 'numeric_bound' not in row['classes']
                        summary['max_local_error_rad_s']=max(summary['max_local_error_rad_s'],*row['local_errors'])
                        summary['max_stateful_error_rad_s']=max(summary['max_stateful_error_rad_s'],*row['state_errors'])
                        summary['max_rational_bits']=max(summary['max_rational_bits'],row['rational_bits'])
                    encoded=json.dumps(row,separators=(',',':'))+'\n';raw.write(encoded)
                    if row['classes']:
                        issues.write(encoded)
                        for label in row['classes']:representatives.setdefault(label,dict(case=case,observation=row))
            except (ValueError,AssertionError) as error:
                summary['invalid_traces']+=1;labels.add('generator_invalid')
                issues.write(json.dumps(dict(id=case['id'],classes=['generator_invalid'],error=str(error)))+'\n')
            summary['trace_classes'].update(labels);group['trace_classes'].update(labels)
            if count==len(case['steps']) and 'unclassified' not in labels:summary['completed_traces']+=1
            traces.write(json.dumps(dict(id=case['id'],steps=count,classes=sorted(labels)))+'\n')
            elapsed=time.monotonic()-start;storage=sum(f.stat().st_size for f in args.out.iterdir() if f.is_file())
            if summary['attempted_traces']%64==0:
                raw.flush();issues.flush();traces.flush()
                progress=dict(traces=summary['attempted_traces'],steps=summary['evaluated_steps'],elapsed_s=elapsed,rss_bytes=rss(),artifact_bytes=storage)
                print(json.dumps(progress),flush=True)
                (args.out/'checkpoint.json').write_text(json.dumps(dict(next_trace_index=summary['attempted_traces'],summary=summary),indent=2)+'\n')
            if elapsed>design['resources']['max_seconds']-60 or rss()>design['resources']['target_rss_bytes'] or storage>design['resources']['max_artifact_bytes']-10000000:
                summary['status']='resource_stop';break
        else:summary['status']='completed'
    summary.update(elapsed_s=time.monotonic()-start,peak_rss_bytes=rss(),sha256={f:sha(args.out/f) for f in ('rows.jsonl.gz','discrepancies.jsonl.gz','traces.jsonl')})
    summary['artifact_bytes']=sum(f.stat().st_size for f in args.out.iterdir() if f.is_file())
    (args.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (args.out/'representatives.json').write_text(json.dumps(representatives,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('builds','per_stratum','source_sha256')}),flush=True)


if __name__=='__main__':main()
