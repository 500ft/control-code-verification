# Consumer contract: PX4 rate-setpoint shaping, shadow and active

Owner decision 2026-10-13 (chat): for this repository, adopt "the combination
layered controller idea". That is the layered placement discussed the same
day: one shadow filter instance per axis in every flight mode, logging only,
plus one active instance per axis that shapes the rate setpoint in acro mode
and in offboard body-rate mode. This settles decision 1 of the external
proposal. Decisions 2 to 7 remain the owner's and are listed below as open.

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
startup initialization, bypass and re-entry resets need wrapper tests. This
placement does not settle their reset or stale-input policy.

Unadopted output cap as a command requirement. The frozen variants clamp the state at
2 rad/s (114.6 deg/s). An active instance therefore limits commanded body
rates to that value regardless of the acro rate parameters, which allow up to
1800 deg/s. This is a handling requirement the owner must accept explicitly
for the active path; numerical equivalence does not establish it. The shadow
instance imposes no such limit on the vehicle.

The frozen filter admits `|u| <= 8 rad/s`. Clipping larger selected inputs
before the step is a proposed, unapproved wrapper rule. Acro parameters and
offboard input can exceed this domain. The active output cap remains an
owner-held handling decision.

## Consumers of the active output, traced at the pinned commit

| Consumer | Where | What it does with the shaped setpoint |
| :--- | :--- | :--- |
| P term and feed-forward | `src/lib/rate_control/rate_control.cpp` | error = setpoint minus measured rate; feed-forward gain defaults to zero |
| Integrator | same file | integrates the error, clamped toward zero on axes the allocator reports saturated |
| Anti-windup source | `MulticopterRateControl.cpp`, allocator status | downstream of the setpoint; reads the allocator, not the filter |
| Shaped-setpoint publication | proposed new topic in `MulticopterRateControl.cpp` | would expose the PID input without feedback through `vehicle_rates_setpoint`; it does not yet exist |
| Existing logger and MAVLink `ATTITUDE_TARGET` | [logger topics](https://github.com/PX4/PX4-Autopilot/blob/c9b9e4e25e57e82fdddd5db7283c3b26fd0afa17/src/modules/logger/logged_topics.cpp), [stream](https://github.com/PX4/PX4-Autopilot/blob/c9b9e4e25e57e82fdddd5db7283c3b26fd0afa17/src/modules/mavlink/streams/ATTITUDE_TARGET.hpp) | subscribe to `vehicle_rates_setpoint`, not the proposed shaped topic; they continue to show the raw topic unless explicitly changed |
| Slew and clamp flags | no current publisher or subscriber | emission and consumer meaning remain open |

Subscribers for other vehicle types do not run on a multicopter build. The
shadow instance currently has no consumer. A logger subscription for its
proposed output would need implementation and qualification.

## Decision fields

| Field | Answer for this integration | Status |
| :--- | :--- | :--- |
| State | If integrated as proposed, the active next state becomes the rate setpoint the PID tracks. No current code consumes the filter's threshold-side flags. | placement adopted; wrapper behavior untested |
| Mode | The proposed filter flags do not select a commander mode or safety action. | traced at the pinned source; wrapper behavior untested |
| Anti-windup | PX4's anti-windup uses allocator saturation status downstream of the setpoint. Filter flags do not drive it. Shaping can still change the rate error and integrator update; test this in a future wrapper. | source traced; functional effect untested |
| Logging | Whether the flags are emitted and logged as new fields, and the caveat that single-sample flags near a threshold are uncertain by the step's error bound. | open: decision 3 |
| Signed zero | The pinned common flags include `-fno-signed-zeros`; existing logger and MAVLink subscribers do not see the proposed shaped topic. Trace any bitwise observer after publication is implemented. | open: part of decision 6 |
| Disposition | The acceptance quantity and tolerance, and the continuous-operation envelope. | open: decision 6 |

## Open owner decisions

Only layered placement and the compiler engineering route are adopted. The
following physical and functional decisions remain open. Recommendations in
the external proposal are not owner approvals.

2. Accept the direction-dependent acceleration limits (4 rad/s^2 rising,
   2 rad/s^2 falling) on a symmetric body axis, or require a symmetric variant,
   which reopens the specification.
3. Flags: emit and log them, or do not emit them.
4. Reset: zero_reset on disarm, acro entry and offboard entry, or require a
   bumpless entry, which needs a new variant. The shadow instance also needs a
   rule; the proposal did not cover it.
5. Invalid input has separate cases. The [MAVLink receiver](https://github.com/PX4/PX4-Autopilot/blob/c9b9e4e25e57e82fdddd5db7283c3b26fd0afa17/src/modules/mavlink/mavlink_receiver.cpp)
   writes NaN for ignored offboard axes; the rate module substitutes measured
   rate on those axes. A non-finite manual-control value has no equivalent
   guard in the acro branch. A rate tick without a new source message leaves
   the previous `_rates_setpoint` held; commander mode and failsafe logic is
   separate. These cases require distinct rules and wrapper tests. Feeding a
   substituted measured rate through a lagged active filter would change the
   original ignored-axis behavior.
6. Acceptance quantity, tolerance and continuous-operation envelope.
7. Compiler option A is selected as the engineering route: a separate strict
   library target for the unchanged generated C. A [host build-only probe](evidence/consumer-build/README.md)
   demonstrates target-local warning and arithmetic overrides with optimization
   and LTO. The pinned PX4 target build and execution remain unqualified.

| Open choice | Recommendation for owner review | Basis and missing evidence |
| :--- | :--- | :--- |
| Active symmetry, output cap and input range | Qualify a separate symmetric, bumpless active variant before use; retain the qualified 4/2 variants only in shadow. Select limits from handling requirements, not the numerical campaign. | The frozen variants cap at 2 rad/s and have asymmetric slew; no handling acceptance or physical envelope is supplied. |
| Flag emission | Log flags with the new shadow and active outputs, with a threshold-uncertainty note; do not use them for control yet. | No current PX4 consumer exists; the review found boundary-sensitive flags. |
| Reset and re-entry | Specify initialization at startup and explicit reset on disarm and mode entry, then test bypass and re-entry against held setpoints. | The rate module can retain a preceding-mode setpoint and the frozen variants have distinct reset semantics. |
| Ignored, non-finite and stale inputs | Preserve PX4's ignored-axis measured-rate substitution without active lag; reject or bypass non-finite manual input; expose freshness and hold behavior separately. | Only the ignored-axis substitute is source-defined here. Fault response and stale-input envelope need an accepted requirement. |
| Signed zero and acceptance | Keep the registered numerical bound unchanged. Choose any bit-identity, flag and continuous-operation rule after identifying actual observers and a duration requirement. | A gyro count is only a reference scale; no functional tolerance or long-duration validation is established. |

## Proposal under decisions 2 and 4, not adopted

The shadow instance affects nothing the pilot feels, so it can run the
qualified 4/2 variants in every mode and supply the integration-boundary
evidence on the artifact that was actually qualified. The active instance
does affect handling. If the owner wants symmetric limits and bumpless entry
there, the clean route is a third semantic variant (symmetric, initialized
from the preceding effective setpoint, with a rule for a preceding value
outside the admitted range) generated by the same generator and qualified by
the same campaign, with its own final cases. That keeps the qualified
variants intact as research artifacts and follows the repository's one
artifact per variant rule. Shadow reset proposal: disarm only, plus startup
and restart initialization, every reset logged so continuous-duration claims
can be checked.

## What this decision does not do

It authorizes no wrapper implementation, simulation or hardware run. The
bounded host build-only probe does not qualify a PX4 target build. The roadmap
gate stays closed until the open fields above are
answered. Nothing here changes the frozen specification, the generated C, the
numerical bound or any held-out case.
