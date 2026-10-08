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

Local setup, CasADi float C generation and the isolated/stateful numerical
comparisons have executed. The [result](evidence/results.json) and
[trace table](evidence/traces.csv) preserve agreement, errors and unresolved
branch-threshold cases. [Registration](registration.json) predates the
implementation. The [specification](spec.json) and [numerical argument](NUMERICS.md)
declare state, reset precedence, dt, units, saturation, types and error bounds.
The intent uses exact rational arithmetic; it need not be replaced with float64.
These are development results, with integration still unqualified.

## Current blockers

Assign the second reviewer and resolve branch-use requirements before qualifying
a wrapper. Name approval separately blocks a public repository. The original
failsafe repository remains paused pending its owner's release/closure choice;
that choice does not block local core review. No physical, funding, purchase or
publication decision has been supplied.

## Dependency order

Setup and numerical requirements → reference-qualified core → reviewed wrapper
and comparison boundaries → independently motivated defect corpus → pilot →
registered confirmation. Public naming and remote CI are a parallel setup branch.
A blocked PX4 replay path does not erase the completed core result.

### Setup and generator qualification

Prerequisites: the local source/register and an available compiler environment.

- Done: local git, explicit float32 reference, inspected CasADi float output and
  compiler flags, analytic checks and reproducible development comparisons.
- Conditional: create a public remote only after name authorization; configure
  CI to reproduce the qualified core. Keep final cases private.
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
- Current: review the functional use of flags whose uncertainty interval touches
  a branch. Specify any required margin or hysteresis; do not widen a numerical
  tolerance to resolve a functional ambiguity.
- Future: freeze any necessary semantic repair and fresh verification cases.
  Cases exposed during development cannot become final cases.

Completion evidence: reviewed requirements, a recorded comparison for the
admitted core, and resolved or explicitly excluded branch-sensitive behavior.
Numerical agreement alone does not complete this milestone.

### Reviewed wrapper and B2B boundaries

Prerequisites: qualified core semantics and a second reviewer. Write admission,
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

Completion evidence: reviewer sign-off, common frozen inputs, known-good and
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
