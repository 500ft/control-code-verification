"""Recount raw observations independently and shrink branch representatives."""
from collections import Counter
from fractions import Fraction as Q
import gzip
import json
from pathlib import Path
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from campaign.observe import evaluate
from campaign.audit_observation import oracle
from qualify import ROOT, compiled, sha


def decode(bits):return struct.unpack('>3f',bytes.fromhex(bits))


def branch_keys(row):
    if 'exact_flags' not in row:return []
    actual=decode(row['reference_bits'])[1:]
    return [f'{("slew","clamp")[i]}:{exact}->{int(actual[i])}' for i,exact in enumerate(row['exact_flags']) if exact!=actual[i]]


def recount(directory):
    s=json.loads((directory/'summary.json').read_text());counts=Counter();traces={};branches=Counter();selected={};rows=0
    with gzip.open(directory/'rows.jsonl.gz','rt') as raw:
        for line in raw:
            row=json.loads(line);rows+=1;labels=[]
            if 'reference_bits' in row:
                a=decode(row['reference_bits'])
                for suffix,field in (('common','common_c_bits'),('rollout','native_bits')):
                    b=decode(row[field])
                    if a[0]!=b[0]:labels.append('numeric_'+suffix)
                    elif row['reference_bits'][:8]!=row[field][:8]:labels.append('signed_zero_'+suffix)
                    if a[1:]!=b[1:]:labels.append('branch_'+suffix)
                if list(a[1:])!=row['exact_flags'] or list(decode(row['native_bits'])[1:])!=row['exact_flags']:
                    labels.append('branch_requirement')
                if max(row['local_errors'])>float(Q(1,524288)) or max(row['state_errors'])>row['bound']:labels.append('numeric_bound')
            else:labels=['unclassified']
            assert sorted(labels)==sorted(row['classes']),row
            counts.update(labels);traces.setdefault(row['id'],set()).update(labels)
            for key in branch_keys(row):branches[key]+=1;selected.setdefault(key,row)
    trace_counts=Counter(label for labels in traces.values() for label in labels)
    assert rows==s['evaluated_steps'] and counts==Counter(s['step_classes']) and trace_counts==Counter(s['trace_classes'])
    return dict(rows=rows,step_classes=counts,trace_classes=trace_counts,branch_transitions=branches),selected


def main():
    base=Path(sys.argv[1]);spec=json.loads((ROOT/'spec.json').read_text());report={};selected={}
    for phase in ('pilot','campaign'):
        report[phase],found=recount(base/(phase+'-observation'))
        for key,row in found.items():selected.setdefault(key,(phase,row))
    cases={}
    paths={'pilot':base.parent/'compute-tasks-20261011/receipts/control-pilot-inputs.jsonl','campaign':base/'campaign-inputs.jsonl'}
    wanted={row['id'] for phase,row in selected.values()}
    for phase,path in paths.items():
        with path.open() as stream:
            for line in stream:
                c=json.loads(line)
                if c['id'] in wanted:cases[c['id']]=c
    build=base/'minimize-build';build.mkdir(exist_ok=True);runs={};builds={}
    for name in spec['variants']:runs[name],builds[name]=compiled(name,spec,build)
    minimized=[]
    for key,(phase,row) in selected.items():
        case=cases[row['id']];steps=case['steps'][:row['step']+1];initial_length=len(steps);checks=0
        def match(proposal):
            nonlocal checks
            checks+=1
            for observed in evaluate(dict(case,steps=proposal),runs,spec):
                if key in branch_keys(observed):return observed
            return None
        n=2
        while len(steps)>1:
            size=(len(steps)+n-1)//n;reduced=False
            for start in range(0,len(steps),size):
                candidate=steps[:start]+steps[start+size:]
                if candidate and match(candidate):steps=candidate;n=max(2,n-1);reduced=True;break
            if not reduced:
                if n>=len(steps):break
                n=min(len(steps),2*n)
        observed=match(steps);assert observed
        sample=steps[observed['step']]
        independently_rounded=oracle(observed['prior_reference'],sample['u'],sample['dt'],sample['reset'],spec['variants'][case['variant']],spec['domain']['state_abs_max'])
        assert struct.pack('>3f',*independently_rounded).hex()==observed['reference_bits']
        # Every remaining single deletion must lose the chosen transition.
        for i in range(len(steps)):
            assert not match(steps[:i]+steps[i+1:])
        minimized.append(dict(transition=key,original_phase=phase,original_id=case['id'],original_step=row['step'],
                              original_prefix_steps=initial_length,case=dict(case,steps=steps),observation=observed,
                              replay_count=checks,method='contiguous deletion ddmin; single-deletion minimal; exact-rounding oracle independently replayed; no scalar optimization'))
    result=dict(independent_recount=report,minimal_branch_examples=minimized,builds=builds,
                signed_zero_reproducer='existing evidence/development/replay.json retained unchanged')
    (base/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(counts=report,examples=[dict(transition=m['transition'],steps=len(m['case']['steps'])) for m in minimized]),indent=2))


if __name__=='__main__':main()
