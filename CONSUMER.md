# Consumer contract: PX4 rate-setpoint shaping, shadow and active

Owner decision 2026-10-13 (chat): for this repository, adopt "the combination
layered controller idea". That is the layered placement discussed the same
day: one shadow filter instance per axis in every flight mode, logging only,
plus one active instance per axis that shapes the rate setpoint in acro mode
and in offboard body-rate mode. This settled decision 1 of the external
proposal. On 2026-10-14 the owner delegated the remaining selections with
“lets do these”. Codex selected the development contract below; these choices
authorize qualification and do not establish flight handling or target safety.

Proposal: `implementation/control-consumer-20261013/PROPOSAL.md` in the
external audit directory, SHA-256
`d5258a628c3730dccc7e352c1f7a002a02923093abc5722d7edbe11fee79bd0e`, written
by the same session as the technical review and therefore not independent of
it. Its source tracing was spot-checked against the pinned host on
2026-10-13: compiler flags, acro rate defaults, the dt clamp, the invalid
setpoint path, the integrator reset condition and the manual-control message
semantics all matched.

## Host and target

- PX4-Autopilot `c9b9e4e25e57e82fdddd5db7283c3b26fd0afa17`, a main-branch
  commit of 2026-10-12 between v1.17.0 and v1.18.0-rc1. Not a release.
- Board: Pixhawk 6C (`fmu-v6c`, STM32H743 Cortex-M7).
- Multicopter builds only. VTOL, fixed-wing and rover paths are excluded.

## Placement

The proposed integration point for both instances is in
`MulticopterRateControl::Run`, after source selection and before
`RateControl::update`. They would step on every gyro-triggered rate-loop
cycle with a valid in-domain input, including cycles without a new setpoint
message (default 400 Hz,
`IMU_GYRO_RATEMAX`) using that cycle's `dt`, which PX4 constrains to
0.125 ms to 20 ms. The filter domain is 15.3 us to 62.5 ms, so every PX4 `dt`
is inside it and the `dt = 0` hold path is unreachable from this host.

| Instance | Runs in | Input | Output goes to |
| :--- | :--- | :--- | :--- |
| Shadow (3 axes) | every mode | a copy of the selected, pre-shaping `_rates_setpoint` after PX4 non-finite substitution where applied, including a held value on a cycle without a message | proposed log fields only; no control consumer |
| Active (3 axes) | acro and offboard body-rate | the same selected, pre-shaping copy on each rate tick | would replace `_rates_setpoint` only for the PID; proposed separate topic |

The [pinned commander selection](https://github.com/PX4/PX4-Autopilot/blob/c9b9e4e25e57e82fdddd5db7283c3b26fd0afa17/src/modules/commander/ModeUtil/control_mode.cpp)
maps ACRO to `manual=true` and `SetpointType::Rates`. OFFBOARD maps
`offboard=true` and `offboard_control_mode.body_rate=true` to
`SetpointType::Rates` after higher-priority setpoint branches.
[That type](https://github.com/PX4/PX4-Autopilot/blob/c9b9e4e25e57e82fdddd5db7283c3b26fd0afa17/src/modules/commander/ModeUtil/setpoint_types.cpp)
sets `rates=true` and `allocation=true` without setting `attitude`.
[Commander clears the flags before each update](https://github.com/PX4/PX4-Autopilot/blob/c9b9e4e25e57e82fdddd5db7283c3b26fd0afa17/src/modules/commander/Commander.cpp).
Require
`rates=true`, `attitude=false`, and either `manual=true` (acro) or
`offboard=true` (body-rate offboard). A bare `offboard && !attitude` condition
would also admit direct actuator control, where the rate loop is disabled.
Other modes bypass active shaping. The wrapper must still test transitions and
publisher behavior before admission.

Publisher separation is a future wrapper requirement: publish the shaped
setpoint on a new topic (working name `vehicle_rates_setpoint_shaped`) and never on
`vehicle_rates_setpoint`. In offboard body-rate mode the rate controller
subscribes to `vehicle_rates_setpoint`; publishing the shaped value there
would feed the filter's own output back in as a fresh command on the next
cycle. The raw stick stays in `manual_control_setpoint` and the raw offboard
command stays in `vehicle_rates_setpoint`. The new topic requires an explicit
logger subscription before ULog can hold the shaped value.

The [pinned rate module](https://github.com/PX4/PX4-Autopilot/blob/c9b9e4e25e57e82fdddd5db7283c3b26fd0afa17/src/modules/mc_rate_control/MulticopterRateControl.cpp)
recomputes the manual setpoint on a new manual message, or copies a new
`vehicle_rates_setpoint` on the other path. Otherwise its member
`_rates_setpoint` is held. On startup or mode entry that member may carry its
initialized or preceding-mode value. Shadow and active state must be separate;
neither samples the other output. The selected copy, source identity, freshness,
startup initialization, bypass and re-entry resets need wrapper tests. The adopted reset and stale-input requirements are recorded below.

The active development variant retains the 2 rad/s output cap and the finite
input domain of 8 rad/s. The cap is an explicit command requirement for this
experiment, not a validated flight envelope. An input outside that domain is
rejected by the active shaper; it is not silently clipped into qualification.
A preceding effective command outside the state cap prevents bumpless entry:
bypass shaping and log the reason until an in-domain entry can occur.

## Consumers of the active output, traced at the pinned commit

| Consumer | Where | What it does with the shaped setpoint |
| :--- | :--- | :--- |
| P term and feed-forward | `src/lib/rate_control/rate_control.cpp` | error = setpoint minus measured rate; feed-forward gain defaults to zero |
| Integrator | same file | integrates the error, clamped toward zero on axes the allocator reports saturated |
| Anti-windup source | `MulticopterRateControl.cpp`, allocator status | downstream of the setpoint; reads the allocator, not the filter |
| Shaped-setpoint publication | proposed new topic in `MulticopterRateControl.cpp` | would expose the PID input without feedback through `vehicle_rates_setpoint`; it does not yet exist |
| Existing logger and MAVLink `ATTITUDE_TARGET` | [logger topics](https://github.com/PX4/PX4-Autopilot/blob/c9b9e4e25e57e82fdddd5db7283c3b26fd0afa17/src/modules/logger/logged_topics.cpp), [stream](https://github.com/PX4/PX4-Autopilot/blob/c9b9e4e25e57e82fdddd5db7283c3b26fd0afa17/src/modules/mavlink/streams/ATTITUDE_TARGET.hpp) | subscribe to `vehicle_rates_setpoint`, not the proposed shaped topic; they continue to show the raw topic unless explicitly changed |
| Slew and clamp flags | no current publisher or subscriber | diagnostic emission and logging adopted; no control use |

Subscribers for other vehicle types do not run on a multicopter build. The
shadow instance currently has no consumer. A logger subscription for its
proposed output would need implementation and qualification.

## Adopted development contract

The numbers below are selected experiment requirements, not measured vehicle
limits. The original `spec.json`, two generated artifacts, numerical bounds,
results and withheld cases remain frozen.

| Decision | Adopted requirement |
| :--- | :--- |
| 2. Symmetry | Keep both qualified 4/2 rad/s^2 variants as separate shadow research artifacts. Generate a third active variant with symmetric 2/2 rad/s^2 slew, tau = 0.25 s, and the same state/input caps. The common lower slew magnitude avoids increasing either directional limit; it is a development choice requiring handling evaluation, not an optimal limit. |
| 3. Flags | Emit and log slew/clamp flags, selected raw input, shaped state, instance identity, reset cause and input-validity/freshness status. Flags are diagnostic only: no mode, safety or anti-windup decisions use them. Boundary-sensitive flags need not match exact intent; compare against the executed binary32 semantics and retain discrepancies. |
| 4. Reset | Initialize both instances at startup/restart and zero them on disarm. Shadow resets on disarm only thereafter; mode changes do not reset it. Active mode entry/re-entry initializes from the preceding effective PID setpoint, per axis, using a separately specified state-initialization operation. It does not track the new desired input as a substitute for bumpless entry. If the preceding setpoint is non-finite or outside the state cap, bypass active shaping and record entry rejection. Log every reset; do not insert resets to satisfy an error bound. |
| 5a. Source-defined ignored offboard axis | Preserve PX4's measured-rate substitution without active lag on that axis. Bypass its active shaper while ignored and reinitialize from the preceding effective setpoint when the axis becomes commanded. A non-finite measured rate is a rejected input, never a numerical reference. |
| 5b. Invalid commanded axis | Reject non-finite commanded values, including manual axes and offboard values that are not source-defined ignored sentinels. Do not step either filter with NaN/Inf. Hold the last finite effective setpoint for that tick, record rejection and retain the pinned host's commander/failsafe authority. If no finite value exists, do not enable shaping. This is a software qualification response, not a flight-safety claim. |
| 5c. Missing, stale or reordered message | A rate tick without a new message can step the held, valid pre-shaping command while the source remains valid under the pinned host. Never feed a shaped output back as the held source. Reject timestamp regressions and expose source age; do not reset age by republishing. On host-declared source loss, bypass active shaping and preserve the host's mode/failsafe handling. Derive host freshness thresholds from the pinned code before wrapper tests rather than inventing a new timeout. |
| 6. Acceptance | Use 1.065e-3 rad/s as the selected numerical next-state error ceiling against exact intent over a 30-minute continuous active segment, with no artificial resets. It is the proposed gyro-count reference scale, not a proved sensor specification or safety tolerance. Qualify the new variant's propagated bound for all registered dt/input histories; simulations alone do not establish a universal bound. If the argument exceeds this ceiling, report failure rather than widen it. Zero signs may differ; finite values and zero-sign-insensitive consumers are required. No exact-intent flag identity or target bit identity is claimed. |
| 7. Compiler | Option A: a separate strict library target. Verify effective compile commands, warning overrides, arithmetic flags and LTO behavior in the pinned PX4 target build and linked artifact. The host probe alone is insufficient. |

The active initializer must return the preceding in-range setpoint unchanged
at the transition boundary; the first ordinary update occurs on the next
accepted rate tick. Register saturation, ignored-axis transitions, domain
rejection, dropout and mode/disarm precedence before collecting results.
Check the PID integrator response explicitly. Diagnostic flags do not drive
allocator anti-windup, but shaping changes the integrator's rate error.

## Execution and admission

Start with a separate specification and development qualification for the
third variant, preserving original artifacts and their 256-step admission.
Then qualify the target build and wrapper on registered message histories.
A bound failure, unsupported host behavior or invalid consumer assumption is
a result to resolve before admission. Wrapper scaffolding and directed tests
are authorized; target integration is admitted only after these prerequisites
pass. No extra broad random campaign is needed to decide these requirements.

Use the adopted Claude AI technical review protocol with non-blind provenance
stated; human review remains deferred. New variant final cases must be separate
from exposed development cases, and neither old nor new final cases may be
opened as part of this task. Physical runs, flight release and claims about
hardware timing remain outside this authorization.
