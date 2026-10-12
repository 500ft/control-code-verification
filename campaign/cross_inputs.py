"""Translate only the original registered public development traces for C I/O."""
import json
from pathlib import Path
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import reference
from qualify import ROOT, sha

spec=json.loads((ROOT/'spec.json').read_text())
registration=json.loads((ROOT/'registration.json').read_text())
assert sha(ROOT/'traces.json')==registration['sha256']['traces.json']
traces=json.loads((ROOT/'traces.json').read_text())
bits=lambda x:struct.pack('>f',float(x)).hex()
for variant,(name,cfg) in enumerate(spec['variants'].items()):
    for trace in traces:
        ref=trace['initial']
        for i,s in enumerate(trace['steps']):
            print(f"{variant:x} {int(i==0):x} {bits(trace['initial'])} {bits(ref)} {bits(s['u'])} {bits(s['dt'])} {int(s['reset']):x}")
            ref=reference(ref,s['u'],s['dt'],s['reset'],cfg,spec['domain']['state_abs_max'])[0]
