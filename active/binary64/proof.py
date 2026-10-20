"""Exact-rational calculation of the prospective absolute error envelope."""
from fractions import Fraction as Q

U=Q(1,2**53)
A=Q(1,2**1075)
positive_updates=1800*65536
local=24*U+36*A
state=positive_updates*local
published=Q(1,2**24)
total=state+published
ceiling=Q('0.001065')
assert positive_updates==117964800
assert total<ceiling
print('positive_updates_max',positive_updates)
print('local_bound',float(local),'state_bound',float(state))
print('publication_bound',float(published),'whole_output_bound',float(total),'ceiling',float(ceiling))
