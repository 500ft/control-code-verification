# Roadmap

## Question and finish line

Which deployment defects remain after a costed back-to-back (B2B) comparison
of implementations on the same inputs, and which extra checks detect them at
what marginal cost?

The finish line is a registered comparison using independently checked
implementations and independently justified defect mechanisms. Report defects
remaining after ordinary B2B testing and the cost of each additional check.
A result in which ordinary B2B detects every tested defect is useful. Keep
generation method and verification method as separate factors, with the same
strong baseline for each check. The comparison campaign remains unauthorized.

## Verified starting point

The published source generated C with CasADi and compared isolated steps and
stateful sequences. The [result](evidence/results.json) and
[trace table](evidence/traces.csv) report agreement, errors and branch-threshold
questions. The [registration](registration.json) preceded implementation.
The [specification](spec.json) and [numerical argument](NUMERICS.md) define
state, reset precedence, `dt`, units, saturation, types and error bounds.
Exact rational arithmetic defines the intended result. These are development
comparisons; integration has not been tested.

## Current blockers

The [observational continuation](evidence/observational/README.md) completed
the registered development comparisons, including exact-reference coverage
and an ARM Linux GCC/QEMU run. It observed signed-zero and
exact-versus-rounded branch differences. The non-blind
[Claude AI technical review](evidence/review/README.md) and focused checks
support the original shadow filters' numerical next-state values only for
their declared domain, strict arithmetic and trace horizon. Targeted review
cases also found reverse-slew flag differences and negative-zero paths.
[CONSUMER.md](CONSUMER.md) records the chosen PX4 consumer and adopted
functional requirements. No wrapper behavior has passed those requirements;
numerical agreement alone cannot establish it. Human review is deferred and
is not required for this numerical development review. The original
first-failure pilot and its bitwise stopping rule remain in the historical
record.

The chosen PX4 placement is a diagnostic shadow filter in every rate-loop
mode and active rate-setpoint shaping in acro and offboard body-rate mode
([CONSUMER.md](CONSUMER.md)).
The [adopted development contract](CONSUMER.md#adopted-development-contract)
selects a separate symmetric active variant, diagnostic logging, bumpless
entry, three-class invalid-input handling and a continuous error ceiling.
The [registered active development result](active/README.md) generated that
variant and found a directed counterexample to its continuous numerical
ceiling. A separate [PX4 timestamp-domain development result](active/px4_domain/README.md)
also found a counterexample under source-permitted 125/126 microsecond
timestamp gaps. Those gaps are not an observed sensor schedule. The later
[persistent binary64 variant](active/binary64/README.md) passed directed host
comparisons. Its proof and non-blind
[Claude AI technical review](active/binary64/review/README.md) support the
numerical value bound under strict arithmetic when positive `dt` values sum
to at most 1,800 seconds. That sum does not establish wall time or PX4 runtime
behavior. The original artifacts remain unchanged; the wrapper and final cases
remain untested. The
[pinned `fmu-v6c` target build](active/binary64/target-build.json) compiled
the strict option-A binary64 library and the existing rate module (#12,
2026-10-20). It is build evidence only and establishes no firmware integration
or runtime behavior. The earlier
[build-only host probe](evidence/consumer-build/README.md) is retained as
historical evidence. The existing staging name is now used for the
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
- Done: the [persistent binary64 active variant](active/binary64/README.md)
  was qualified in development when the binary32 active comparison needed it
  (#12, 2026-10-20). Qualify any further precision or generator only when its
  comparison needs it. Inspect constants, casts, math calls and compiler
  behavior separately.
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
- Done: the non-blind [Claude AI technical review](evidence/review/README.md)
  and focused reproduction support the original filters' numerical
  next-state values under strict arithmetic and the registered trace horizon.
  The original numerical budget and historical results remain unchanged. The review's
  tighter-bound estimate and universal reverse-clamp exclusion are unestablished.
- Current: the separately specified active variant failed its registered
  continuous numerical ceiling on a directed development case
  ([result](active/results.json), [closed-form calculation](active/README.md),
  [Claude AI technical review](active/review/README.md)).
  The separately registered PX4 timestamp-domain analysis also failed the
  same ceiling ([result](active/px4_domain/results.json)); the historical
  PX4-domain result had no available ARM target build.
  The broad-domain failure remains in force. No narrower contract was adopted.
  A separate persistent binary64 variant has a
  [nonexpansive arithmetic bound](active/binary64/PROOF.md) and passed
  [directed development comparisons](active/binary64/results.json), including
  both retained binary32 counterexamples. An isolated pinned `fmu-v6c` build
  compiled a strict option-A library and the existing rate module; a separate
  linked probe contains hardware double instructions. This does not establish
  firmware integration or runtime timing. A [scoped Claude AI technical
  review](active/binary64/review/README.md) pinned to the result commit and
  focused post-review controls support the new core's numerical value bound only
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

Prerequisites: core behavior checked against its numerical specification,
the [consumer contract](CONSUMER.md), and a generated-C build with the required
compiler warnings. The Claude AI technical review covers the numerical value
claim only. Specify initialization, reset and mode transitions, timestamp and
message handling, publisher separation and wrapper acceptance before
collecting wrapper results.

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
