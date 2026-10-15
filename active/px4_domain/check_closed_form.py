"""Independent rational check of the saved reachable-tick counterexample."""
from fractions import Fraction as Q
import json
from pathlib import Path
import struct

here=Path(__file__).resolve().parent
record=json.loads((here/'results.json').read_text())
row=next(c for c in record['cases'] if c['id']=='half_ulp_near_min')
failure=row['first_exceed']
assert failure and failure['step']%2==1
n=(failure['step']-1)//2
def h(k): return Q(struct.unpack('<f',struct.pack('<I',int(record['dt_bits'][str(k)],16)))[0])
up,down=h(125),h(126)
ulp=Q(1,8388608)
assert 2097 < 2*up/ulp < 2098
assert 2113 < 2*down/ulp < 2114
# Starting at 5/4, rounded up increments 2097 ulps and down increments
# 2114 ulps. The parity alternates, but each pair loses 17 ulps.
exact=Q(5,4)+n*2*(up-down)+2*up
rounded=Q(5,4)-17*n*ulp+2097*ulp
error=abs(exact-rounded)
previous=abs((Q(5,4)+(n-1)*2*(up-down)+2*up)-(Q(5,4)-17*(n-1)*ulp+2097*ulp))
assert exact==Q(failure['exact_state'])
assert rounded==Q(failure['c_state'])
assert error==Q(failure['error'])
assert previous<=Q('0.001065')<error
assert Q(1)<exact<Q(2) and Q(1)<rounded<Q(2)
assert failure['elapsed_s']==str(n*(up+down)+up)
print('pair count',n,'first-crossing step',failure['step'],'elapsed_s',float(Q(failure['elapsed_s'])),'error_rad_per_s',float(error))
