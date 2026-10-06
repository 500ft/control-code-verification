# Core specification and numerical argument

This is a command shaper for angular rate. Its state is the last commanded
rate, so asymmetric acceleration limits model distinct increasing and
decreasing actuator slew. The parameters, units, admissible domain, horizon
and compiler flags live in [spec.json](spec.json). The variants change reset
semantics and filter time constant. They were authored and frozen for this
qualification; this does not establish absence from model training data.

For state x, input u and time increment h, the non-reset update is

```
a = h / (tau + h)
d = a * (u - x)
z = x + clip(d, -slew_down*h, slew_up*h)
x_next = clip(z, -limit, limit)
```

This is backward Euler for `tau * dx/dt = u - x`, with a reachable-increment
projection and an absolute rate clamp. It qualifies the discrete requirement;
no continuous-time discretization-error or actuator-tracking claim is made.
Reset takes precedence over zero-dt hold and the update. Zero reset clears
state; tracking reset sets it to the clamped current input. Reset deliberately
bypasses the acceleration limit. Zero dt without reset holds state exactly.
The returned slew and clamp flags use strict comparisons; equality belongs to
the unclipped branch. Reset and hold report inactive flags.

Inputs must be finite, within the registered domain, and already exactly
representable as binary32; reset must be a boolean. Validation applies even
on reset. `core.validate` is the qualification harness's admission boundary.
The bare generated C assumes these preconditions. It is not an integration
wrapper and must not be called on arbitrary external data.

`core.intent` uses exact rational arithmetic and independently forms the
weighted next target `(tau*x + h*u)/(tau+h)`, then projects onto the reachable
state interval. `core.reference` rounds each operation to NumPy binary32.
The generator builds a separate symbolic expression. Frozen development
inputs are dyadic so input conversion error is absent; deployment conversion
would need its own requirement. Constants are exactly representable.

## Error bound

Let epsilon be binary32 unit roundoff from the register. Over the registered
domain, `|u-x| <= 10`, `a <= 1/3`, and each signed slew increment has magnitude
at most 1/4. Correctly rounded addition and division give
`|a_hat-a| <= 2*epsilon`: the usual relative bound is
`2*epsilon/(1-epsilon)` times a. Subtracting u-x contributes at most
`10*epsilon`. Multiplying the rounded difference and coefficient therefore
contributes less than `28*epsilon` rad/s absolute error to d, including the
product's rounding and cross terms.

The slew multipliers are powers of two, hence exact here. Clipping is
nonexpansive, so the delta bound also bounds its clipped value. Adding the
state rounds by less than `3*epsilon` rad/s. The final projection is also
nonexpansive. The registered `32*epsilon` local bound leaves room above that
sum; selections in generated C add a selected finite value to zero exactly.
Reset and hold are exact.

These absolute bounds also cover subnormal differences: when a relative
rounding bound fails at gradual underflow, its absolute error is at most half
the minimum subnormal, far below the slack above. Inputs and coefficients do
not approach overflow. This assumes gradual underflow and nearest-even
rounding; other floating-point modes are outside qualification.

For the exact map, as x varies each region has slope either `1-a`, `1`, or
`0`, with continuous joins. It is nonexpansive in x. Therefore cumulative
state error is at most the preceding bound plus the local bound on each
update. Reset returns the bound to zero; hold preserves it. The runner checks
this recurrence against exact rational trajectories and reports the
registered worst-horizon bound in [results](evidence/results.json).

Independent analytic checks use the geometric closed-form constant-input
response, linear positive and negative slew ramps through the clamp,
equilibrium, hold and reset precedence. They prevent agreement between the
implementations from being the only requirements check.

## Branch requirement gate

Numerical agreement is separate from functional acceptance. The runner carries
state uncertainty into the raw-delta and pre-clamp comparisons. An interval
touching a branch threshold records a requirement issue, even if the executed
implementations chose the same branch. These are conservative uncertainty
flags, not observed failures. No functional tolerance was supplied or inferred.

Before integration, a reviewer must decide whether strict branch identity is
required and how branch-near inputs should be handled. If an external action
uses these flags, its margin or hysteresis must be specified and checked.
Widening numerical tolerance cannot answer that question. The current result
keeps integration unqualified, with final cases withheld.

## Generated artifact inspection

CasADi emits `casadi_real float` and float temporaries. Unsuffixed literals are
assigned to float temporaries before arithmetic; all coefficient values in
this module are exact in that type. Generated code uses basic arithmetic,
comparisons and finite selections; it calls no transcendental math functions.
The Clang IR check confirms float arithmetic, no double arithmetic and no
fast/contraction flags. Build commands, tool versions and hashes are recorded
in the results. This inspection qualifies this local build only.

The [CasADi C-generation documentation](https://web.casadi.org/docs/#generating-c-code)
is the tool reference. Generated sources retain CasADi's licensing notices.
