# First detection-cost datum: both retained active counterexamples

This development replay asks which comparison boundary detects each retained
binary32 active counterexample, and at what execution cost. The
[registration](registration.json) was committed at `c8a4807` before any
result; it pins both input definitions, the unchanged compiled core, the
oracles and the retained result files, and states the prediction. The
[result](results.json) owns every number: for each input and boundary, whether
the registered `0.001065 rad/s` ceiling was crossed, the first crossing step and
error, steps executed, exact-intent, binary32-reference and compiled
evaluation counts, and loop wall-clock on the executing host (Apple M1 Pro,
macOS 14.7.3, Apple clang 16, Python 3.13.7). Compile time is recorded
separately.

The two inputs are read from the registered case files: the
[continuous-ceiling tie sequence](../../active/directed.json)
(`positive_tie_accumulation`) and the
[PX4 timestamp-gap sequence](../../active/px4_domain/directed.json)
(`half_ulp_near_min`), with the compiled binary32 `dt` bits taken from the
[owning PX4-domain result](../../active/px4_domain/results.json). The
implementation under test is the unchanged
[generated active core](../../active/generated/active_symmetric.c), compiled
with the `active/qualify.py` flags. Exact intent and the explicit binary32
reference come from [core.py](../../core.py) with the active configuration
(tau 1/4, symmetric 2/2 slew, state limit 2).

Boundary (a), `registered_horizon_b2b`, is the original 256-step back-to-back
comparison. The root [qualify.py](../../qualify.py) is hard-wired to
`traces.json` and the two shadow variants, so [run.py](run.py) reproduces its
per-step loop (two exact-intent evaluations, one binary32 reference, isolated
and stateful compiled calls, bitwise C/reference assertions, the local `32u`
step bound, the accumulated horizon bound and the branch threshold inspection)
over the first 256 steps of each input, with the active configuration and
core. It is a reproduction of that comparison, not the original harness file.
Boundary (b), `directed_long_horizon`, is the per-step loop of
[active/qualify.py](../../active/qualify.py) over all registered steps for the
tie input, and of [active/px4_domain/run.py](../../active/px4_domain/run.py)
stopping at the first failure for the gap input. The driver asserts that each
directed replay reproduces the retained first-crossing step and error.

The prediction held. Neither input crosses the ceiling within the 256-step
horizon; the original horizon bound is not exceeded and the branch inspection
flags no threshold contact there. Both directed replays cross at the retained
steps with the retained errors, with no C/reference mismatch. The tie input's
256-step error equals the registered closed-form value `1/65536 rad/s`
(`256/16777216`, see the [retained calculation](../../active/README.md)); the gap
input's 256-step error is in the result. The difference between the two
boundaries here is horizon, not comparison method: the same per-step
comparison crosses the ceiling once it runs long enough, because the
accumulated error grows with the step count on these inputs.

This is one datum on two inputs, one host and one timing run; wall-clock is
descriptive. An earlier run of the same driver on the same host took about
twice as long on the longest directed loop, so the recorded times bound
nothing. It admits no boundary and does not alter the
retained results or the adopted contract. A crossing inside the 256-step
window, a directed crossing step or error different from the retained value,
or any C/reference bitwise mismatch would change the conclusion. The driver's
float32 state conversion was corrected after the registration commit and
before the first complete run; the registered prediction and pinned inputs are
unchanged.

Reproduce from the repository root with the pinned Python environment and a
host C compiler:

```sh
python evidence/detection-cost/run.py
```
