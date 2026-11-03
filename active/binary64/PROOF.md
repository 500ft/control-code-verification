# Prospective arithmetic argument

This argument applies to the exact operation order that the new C generator
must emit. Inputs `u` and `h` are finite binary32 values promoted exactly to
binary64. The persistent state `x` is binary64 and stays in `[-2,2]`. Set
`tau=1/4`, `2^-16 <= h <= 1/16`, and `|u| <= 8`. Reset sets exact zero; hold
returns the unchanged state. An invalid operation is rejected before arithmetic.

The positive-dt operations are, in order:

```
d = RN64(tau + h)
v = RN64(u - x)
a = RN64(h / d)
delta = RN64(a * v)
lo = -2*h; hi = 2*h
q = median(lo, delta, hi)
r = RN64(x + q)
x_next = median(-2, r, 2)
published = RN32(x_next)
```

The slew and clamp diagnostics compare the binary64 intermediates and do not
affect state. `2*h` is exact in binary64 on this domain. The published float
is never used as the next persistent state.

For exact arithmetic, the state map is
`F(x)=clip(x+clip(h*(u-x)/(tau+h),-2h,2h),-2,2)`.
Its continuous pieces have slopes `1` on a slew branch,
`tau/(tau+h)` on the lag branch, and `0` at the state cap. The slopes all lie
in `[0,1]`; the pieces meet at branch boundaries. Therefore the entire map
is globally nonexpansive in the previous state, including a change of branch.

Let `U=2^-53` and `A=2^-1075`. Every nearest-even binary64 operation,
including one with a subnormal exact result, has absolute error at most
`U*|exact result|+A`. Since `tau+h <= 5/16`, denominator error is at most
`E_d=(5/16)U+A`, and the rounded denominator exceeds `1/8`. Since
`|u-x| <= 10`, difference error is at most `E_v=10U+A` and its rounded
magnitude is less than 11. The exact alpha is at most `1/4`, and the rounded
quotient has magnitude less than `1/2`. Denominator perturbation and quotient
rounding give `E_a <= 2E_d+(1/2)U+A = (9/8)U+3A`. Product propagation and
rounding give
`E_delta <= 11E_a+(1/4)E_v+(11/2)U+A <= 21U+35A`.
Projection onto the exact slew interval is 1-Lipschitz, including branch
changes. The pre-rounding reached magnitude is at most `17/8`, so the state
addition contributes at most `(17/8)U+A`. The outer cap is also
1-Lipschitz. Thus the uniform local state error is at most `24U+36A`.

Initialization from a binary32 setpoint is exact in binary64, so initial
error is zero. At most `1800*65536 = 117964800` positive updates fit within
the registered 1,800-second segment; any zero-dt holds add no error.
Nonexpansiveness propagates the state bound to `N*(24U+36A)` for any such
history, without resets. Separately, converting a capped state in `[-2,2]`
to nearest-even binary32 adds at most `2^-24` absolute error, including
subnormal outputs. [The executable rational calculation](proof.py) compares
the sum with the unchanged `0.001065 rad/s` ceiling. This is an arithmetic
argument for the specified emitted operations under strict IEEE rounding;
target build and linked behavior still require verification.
