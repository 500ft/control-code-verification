# Executed development branch-use review

The replay explains every retained branch issue as an uncertainty interval
covering a threshold tie in the exact and reconstructed binary32 paths. Exact intent, the binary32 reference and
compiled C emitted the same branch flags. The [executed detail](evidence/branch-use.json)
is the numerical source; its [generated table](evidence/branch-use-table.md)
maps each development step to its predicate, interval and output tuple.
Original results, inputs, generated C and numerical bounds are unchanged.

## What was executed

The original generation and qualification commands were rerun in a separate
checkout. Generated C and the trace CSV matched byte for byte; scientific
result fields matched the retained [result](evidence/results.json). Environment,
binary identities and elapsed time describe the new execution separately.

`python review_branch_use.py` then compiled the unchanged C through the existing
adapter, replayed the registered development traces and checked native state
and flags against the explicit binary32 reference. It matched the stored trace
states, bounds and issue locations. The [run record](evidence/branch-use-run.json)
identifies the compiler, binaries, LLVM and detail hash. Original qualification
still provides the isolated-step comparisons and analytic checks.

For each flagged step the detail records exact inputs, the uncertain comparison,
closed interval, rounding of every arithmetic operation and native output bits.
Intermediate values are reconstructed from source; only the output tuples are
observed from C. Each rounding operation is independently checked by exact
rational distances to adjacent binary32 values, including ties-to-even. The
weighted-target exact intent independently checks the increment/projection form.
No new cases, integration inputs or final outcomes were opened.

## Why these intervals touch

The rate-clamp cases arrive exactly at the rate limit. Their slew-limited
increments and preceding states are exactly representable. Rounding in the
raw delta is removed by slew clipping; the subsequent addition is exact at
these steps. Strict comparison at the rate limit returns an inactive clamp
flag, even though the output is on the limit. The nonzero propagated bound
still straddles that threshold.

The near-slew case has an exactly representable delta equal to its upper
increment limit. The filter coefficient rounds upward, then multiplication
rounds back to the exact delta. The upper strict comparison is false. The
operation fractions, signed rounding errors and bit patterns are in the
[detail](evidence/branch-use.json); this explanation does not assume all
near-threshold inputs behave alike.

The bound is conservative at these exposed steps. A false strict predicate at
equality also selects the same state value as the clipping arm would select.
That local equality does not establish flag stability for perturbed inputs,
later steps or another consumer. No tolerance, margin, hysteresis or contract
was changed, and the historical issue flags remain in the original evidence.

## Source and consumer map

| Quantity | Source and current consumer | Functional consequence |
| :--- | :--- | :--- |
| Slew and clamp comparison predicates | [Generator](generate.py#L23), [exact intent](core.py#L28), [rounded reference](core.py#L43) | Select the clipped increment and next state. These predicates affect the numerical state update. |
| Emitted slew flag, output index 1 | [Zero-reset C](generated/zero_reset.c#L105), [tracking-reset C](generated/tracking_reset.c#L117); compared in [qualify.py](qualify.py#L119) | Verification observes the flag; no repository application consumes it for a control or mode transition. |
| Emitted clamp flag, output index 2 | [Zero-reset C](generated/zero_reset.c#L119), [tracking-reset C](generated/tracking_reset.c#L131); same verifier | Same current verification use. Inactive at exact equality under the existing contract. |
| Next state, output index 0 | [Zero-reset C](generated/zero_reset.c#L101), [tracking-reset C](generated/tracking_reset.c#L113); [sequence recurrence](qualify.py#L139) | Only this output is passed as the next state. The emitted flags are computed after the state store and do not feed it back. |
| Conservative `branch_issue` diagnostic | [Interval inspection](qualify.py#L120), [figure input](plot.py#L24) | Marks requirement-review locations. It is distinct from either emitted flag and is never an input to the core. |
| External flag or state consumer | No wrapper/application is present in this repository | Intended action, sensitivity to a flag change and functional acceptance remain unspecified. |

The map applies to both emitted flags at every row of the generated table.
Repository source inspection covered the Python consumers and both generated
C functions. Absence of an in-repository consumer gives no evidence about an
unprovided external application. Diagnostic-only emitted flags could be a
future contract proposal if the reviewer establishes that no action depends
on them. This review neither adopts that proposal nor removes flag checking.

## Remaining decision and reproduction

A human reviewer must specify the intended consumer and whether exact flag
identity is required at thresholds, then review any necessary semantic change.
The independent second reviewer is still unassigned. Wrapper qualification
remains blocked; numerical agreement does not qualify integration.

From a separate checkout with the pinned dependencies and Clang:

```sh
python review_branch_use.py
git diff --exit-code -- evidence/branch-use.json evidence/branch-use-table.md
```

Run this before `qualify.py`, which overwrites the historical result with its
new run identity. The branch review reads the historical result and records
its hash. Per-run compiler/binary identity is written to ignored
`build/branch-use/run.json`; CI retains it with the development artifacts.
The committed run record describes the local execution and is not rewritten
by CI. No generated report replaces the preserved original evidence.
