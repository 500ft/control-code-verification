# Roadmap

## Question and finish line

Which deployment defects remain after a costed back-to-back comparison, and
which extra checks detect them at what marginal cost?

Finish with a registered comparison on independently qualified implementations
and defect mechanisms, reporting residual defects and verification cost. A
result where ordinary B2B removes every qualified defect is useful. Generation
method and verification method are separate factors; no weak baseline is
introduced to favor another check. This roadmap does not authorize a campaign.

## Verified starting point

Published source, CasADi float C generation and the isolated/stateful numerical
comparisons have executed. The [result](evidence/results.json) and
[trace table](evidence/traces.csv) preserve agreement, errors and unresolved
branch-threshold cases. [Registration](registration.json) predates the
implementation. The [specification](spec.json) and [numerical argument](NUMERICS.md)
declare state, reset precedence, dt, units, saturation, types and error bounds.
The intent uses exact rational arithmetic; it need not be replaced with float64.
These are development results, with integration still unqualified.

## Current blockers

The [observational continuation](evidence/observational/README.md) completed the
registered development budget with exact-reference coverage and an executable
ARM Linux GCC/QEMU comparison. Signed-zero representation and exact-versus-rounded
branch differences remain observed requirements questions. Specify their
functional consumers and acceptance requirements before qualifying a wrapper.
The [Claude AI technical review reconciliation](evidence/review/README.md)
admits the numerical next-state-value claim for the declared domain, strict
arithmetic and registered trace horizon. Its targeted cases add reverse-slew
flag differences and negative-zero paths. The selected PX4 consumer is now
source-traced in [CONSUMER.md](CONSUMER.md); functional requirements are now adopted; wrapper behavior remains unqualified. Human review is deferred and is
not required for this scoped development admission. Numerical agreement does not decide functional
acceptability.
The original first-failure pilot and its bitwise criterion remain preserved;
its stop no longer prevents descriptive numerical observation.

The consumer is chosen: PX4 rate-setpoint shaping, shadow in every mode and
active in acro and offboard body-rate mode ([CONSUMER.md](CONSUMER.md)).
The [adopted development contract](CONSUMER.md#adopted-development-contract)
selects a separate symmetric active variant, diagnostic logging, bumpless
entry, three-class invalid-input handling and a continuous error ceiling.
The [registered active development result](active/README.md) generated that
variant and found a directed counterexample to its continuous numerical
ceiling. A separate [PX4 timestamp-domain development result](active/px4_domain/README.md)
also found a counterexample under source-permitted 125/126 microsecond
timestamp gaps. Those gaps are not an observed sensor schedule. Current gate:
the separately registered [binary64 precision variant](active/binary64/README.md)
has a prospective bound below the unchanged ceiling and passed directed host
replay. Its [scoped Claude AI technical review](active/binary64/review/README.md)
admits the numerical value bound under strict arithmetic and the summed-dt
horizon. PX4 runtime and wrapper qualification remain open. Preserve the original
artifacts and final cases. The
[build-only host probe](evidence/consumer-build/README.md) demonstrates an
isolated library with target-local warning and arithmetic overrides,
optimization and LTO objects. It does not establish a pinned PX4 target build
or runtime behavior. The existing staging name is now used for the
public repository under the owner's delegated implementation instruction. The
original failsafe repository remains paused pending its owner's release/closure choice;
that choice does not block local core review. No physical, funding, purchase or
paper-publication decision has been supplied.

## Dependency order

Setup and numerical requirements → reference-qualified core → reviewed wrapper
and comparison boundaries → independently motivated defect corpus → pilot →
registered confirmation. Public source setup and
[hosted development reproduction](https://github.com/500ft/control-code-verification/actions/runs/37854170219) are complete.
A blocked PX4 replay path does not erase the completed core result.

### Setup and generator qualification

Prerequisites: the local source/register and an available compiler environment.

- Done: local git, explicit float32 reference, inspected CasADi float output and
  compiler flags, analytic checks and reproducible development comparisons.
- Done: publish the reviewed source and development evidence at
  [control-code-verification](https://github.com/500ft/control-code-verification).
  Final cases remain private.
- Done: [hosted CI](https://github.com/500ft/control-code-verification/actions/runs/37854170219)
  regenerated C, compiled it and reproduced the retained numerical result and
  trace CSV. The [workflow](.github/workflows/qualify.yml) is merged.
- Future: qualify another precision or generator only when its comparison needs
  it. Inspect constants, casts, math calls and compiler behavior separately.
- Inspect any reused failsafe runner/parameter transport before adapting it.
  Select and pin a supported firmware/toolchain through actual qualification;
  the old failsafe version is not automatically the successor's version.

Completion evidence: recorded source/tool versions, generated artifacts,
compiler commands and independent reference checks for every admitted path.
An unexecuted double build is not part of the current result.

### Reference-qualified controller

Prerequisites: setup plus reviewed state/reset/dt requirements, a finite input
and horizon domain and numerical error bounds before running comparisons.

- Done: the filter variants pass independent analytic limits and common frozen
  development traces against exact intent, explicit float32 and compiled C.
- Done: [executed branch-use review](BRANCH_USE.md) reproduces the retained
  result and maps each flagged step to its comparison, interval, rounding and
  emitted output. The exposed cases are threshold ties with matching flags.
  Returned flags currently feed verification; clipping predicates affect state.
- Done: the bounded development pilot measured rational-reference cost and
  passed host arithmetic controls, then stopped on its first bitwise
  discrepancy. A minimized direct C replay preserves the finding; state values
  and flags agree there. Original inputs and results remain unchanged.
- Done: a separately registered observational continuation completed every
  eligible pilot and randomized development trace with independent histories,
  exact-reference coverage, independent rounding audit and minimized branch
  examples. No observed numerical-bound violation occurred. ARM Linux GCC and
  QEMU executed the original registered corpus and the known-zero diagnostic;
  this supplies no Cortex-M/PX4 or hardware-timing qualification.
- Done within scope: the [pinned Claude AI technical review](evidence/review/README.md)
  and focused reproduction admit only the numerical next-state-value claim
  under strict arithmetic and the registered trace horizon. The original
  numerical budget and historical results remain unchanged. The review's
  tighter-bound estimate and universal reverse-clamp exclusion are unestablished.
- Current: the separately specified active variant failed its registered
  continuous numerical ceiling on a directed development case
  ([result](active/results.json), [closed-form calculation](active/README.md),
  [Claude AI technical review](active/review/README.md)).
  The separately registered PX4 timestamp-domain analysis also failed the
  same ceiling ([result](active/px4_domain/results.json)); the historical
  PX4-domain result had no available ARM target build.
  The broad-domain failure remains in force. No narrower contract was adopted.
  A separate persistent binary64 variant now has a prospective
  [nonexpansive arithmetic bound](active/binary64/PROOF.md) and passed
  [directed development comparisons](active/binary64/results.json), including
  both retained binary32 counterexamples. An isolated pinned `fmu-v6c` build
  compiled a strict option-A library and the existing rate module; a separate
  linked probe contains hardware double instructions. This does not establish
  firmware integration or runtime timing. A [scoped Claude AI technical
  review](active/binary64/review/README.md) pinned to the result commit and
  focused post-review controls admit the new core's numerical value bound only
  under strict arithmetic and a positive-dt sum of at most 1,800 seconds.
  Target runtime arithmetic and wrapper behavior remain unqualified.
  Diagnostic flags and zero-sign-insensitive value acceptance are adopted.
  The original numerical bound and 256-step qualification stay unchanged.
  The registered binary32 active implementation's continuous ceiling is
  refuted. That result does not classify all compensated binary32 methods.
  The isolated-library host probe is retained as historical evidence.
- Future: freeze any necessary semantic repair and fresh verification cases.
  Cases exposed during development cannot become final cases.

Completion evidence: a traced consumer contract, the [reconciled review](evidence/review/README.md),
the recorded comparison for the admitted value claim, and resolved or
explicitly excluded branch-sensitive behavior.
Numerical agreement alone does not complete this milestone.

### Reviewed wrapper and B2B boundaries

Prerequisites: qualified core semantics, a consumer contract and a resolved
generated-C warning-set build requirement. The scoped Claude AI technical
review is complete for the numerical value claim. Write admission,
initialization, reset/mode, timestamp, stale/absent/reordered-message and
publisher rules before collecting wrapper results.

- Preserve isolated numerical-step and stateful sequence comparisons, including
  saturation, resets and variable dt. Extend them only for admitted new semantics.
- Qualify the wrapper on registered message histories and known-good controls.
- PX4 replay is conditional on a pinned supported build, all subscribed topics
  at required rates, matching timestamps including zero stamps, initialized
  state, controlled publishers, dropout treatment and a known-good repeat.
- Qualify SITL scenarios with requirements written independently of the reference.
  Recorded-rate replay establishes no hardware timing guarantees. Hardware claims would
  need separately authorized measurements.
- For each admitted boundary, demonstrate detection of a justified known defect
  and record setup and execution cost separately.

Completion evidence: resolved review findings, common frozen inputs, known-good and
known-defect outcomes, exclusions, reproducible comparison logs and cost records
for step, state, message and SITL boundaries. None of the latter two has run.

### Independently motivated defect corpus

Prerequisites: qualified comparisons and an independent basis for defect labels.

Inspect historical controller-integration defects and their fixes, then justify
injected variants against those mechanisms. Separate real, seeded and generated
artifacts. Retain correct alternatives and cases whose labels remain unresolved.
Archive generator versions, prompts and repair history if generation is later
authorized. Deterministic CasADi reruns are one artifact, not independent ports.

Completion evidence: reproducible defect/requirement pairs, independent label
review, meaningful controls and coverage by mechanism and module. Proposed
corpus counts are planning targets, not qualified sample-size requirements.

### Pilot, then registered confirmation

Prerequisites for the pilot: qualified corpus, equal B2B access across generation
arms and an authorized execution budget. Collect paired discordance, cost and
module variation; use these to justify the independent-port sample design.

Prerequisites for confirmation: reviewed design and power/precision rationale,
frozen implementation, requirements, analysis and controller/defect holdouts
before exposure. Existing final cases remain untouched until that freeze; any
case used for tuning loses held-out status.

Completion evidence: classified misses and detections, false alarms, uncertainty
and cost at the independent-generation level, with clustered module effects
reported. Do not count ticks or deterministic repeats as samples. If ordinary
initialization/timestamp handling resolves the qualified failures, report that
result rather than searching for a more favorable corpus. Writing, publication
and hardware extensions need separate authorization and evidence.
