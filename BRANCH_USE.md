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

The [Claude AI technical review reconciliation](evidence/review/README.md)
admits the numerical next-state-value claim within its declared domain, strict
arithmetic and registered trace horizon. It reproduces reverse-direction slew
flag differences and additional negative-zero paths. Branch and bit identity,
consumer behavior and wrapper qualification remain unresolved. Human review
is deferred for this scoped development gate. No flag-use contract or semantic
repair has been approved.

### Review scope and decision record

Claude AI technical review should inspect the frozen [specification](spec.json),
including the admissible input domain and variants; the [binary32 error
argument](NUMERICS.md#error-bound); and the [reset and hold
precedence](NUMERICS.md#core-specification-and-numerical-argument). Check the
argument against the original [threshold-contact result](evidence/results.json)
and its [nine-step replay](evidence/branch-use.json): those conservative
intervals touch thresholds, while the executed flags agree. Then inspect the
separately minimized [exact-versus-rounded examples](evidence/observational/independent-review.json)
and the direct [signed-zero reproducer](evidence/development/replay.json).
The [observational account](evidence/observational/README.md) states the
development corpus and environment limits. The received report's hash,
reviewed commit, model/session provenance, non-blind exposure, separately
derived checks, commands and per-claim dispositions are recorded in the
[reconciliation](evidence/review/README.md). Assignment alone did not complete
review. Same-model helper sessions and a separate calculation are different
from independent authorship; neither is human or external peer review.

| Decision field | Question to resolve with the actual consumer | Evidence or answer needed |
| :--- | :--- | :--- |
| State | Is the returned rate/state used only as the next numerical state, or does its threshold-side value select another action? | Identify the consuming interface and behavior for equality and nearby values. |
| Mode | Do either returned slew/clamp flags change a mode, guard or safety action? | Trace the consumer and specify the required branch identity at and near each threshold. |
| Anti-windup | Does a controller use either flag to freeze, reset or back-calculate another state? | Supply the rule and decide whether an exact-versus-rounded flag change is acceptable. |
| Logging | Are flags or state bits used for telemetry, alarms, replay keys or acceptance decisions? | State which representation and branch comparisons must match. |
| Signed zero | Can a downstream calculation or bitwise consumer distinguish negative from positive zero? | Trace sign-sensitive operations or serialization and specify whether sign preservation is required. |
| Disposition | What functional requirement governs any accepted difference? | Record Claude report provenance, per-claim disposition and resolutions; define tests for any adopted contract. |

Owner decision 2026-10-13: the consumer is PX4 rate-setpoint shaping with a
shadow instance in every mode and an active instance in acro and offboard
body-rate mode, recorded in [CONSUMER.md](CONSUMER.md). That record gives
derived answers for the State, Mode and Anti-windup fields and leaves Logging,
Signed zero and Disposition open as owner decisions 3 and 6.

Before that decision the repository had no supplied external consumer. Its
emitted flags feed verification, while clipping predicates affect the next state. The
original result records numerical agreement in its exercised corpus; the
later examples show exact-active to rounded-inactive flags. The
[reviewed reverse-slew cases](evidence/review/reproduced.json) show the opposite
direction for slew flags in both variants. The [zero-sign cases](evidence/review/reproduced.json)
also extend the original hold reproducer to tracking reset and an underflowing
update. Neither observation decides functional acceptability. Diagnostic-only
flags, a branch margin and hysteresis remain
conditional options requiring a supported consumer requirement. Do not run
more random traces or implement a wrapper until the consumer contract and
warning-set build requirement resolve their gates.

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
