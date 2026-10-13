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

Both instances sit in `MulticopterRateControl::Run`, at the point where the
module has selected `_rates_setpoint` from its source and before
`RateControl::update`. They step on every rate-loop cycle (default 400 Hz,
`IMU_GYRO_RATEMAX`) using that cycle's `dt`, which PX4 constrains to
0.125 ms to 20 ms. The filter domain is 15.3 us to 62.5 ms, so every PX4 `dt`
is inside it and the `dt = 0` hold path is unreachable from this host.

| Instance | Runs in | Input | Output goes to |
| :--- | :--- | :--- | :--- |
| Shadow (3 axes) | every mode | the selected `_rates_setpoint`, whatever its source | log fields only; no control consumer |
| Active (3 axes) | acro, and offboard with attitude control disabled | the stick-derived or offboard body-rate setpoint | replaces `_rates_setpoint` for the PID and the published setpoint |

The active gate is "manual enabled and attitude disabled" (acro) or "offboard
enabled and attitude disabled" (body-rate offboard). In every other mode the
setpoint comes from the attitude controller and the active instance is
bypassed; shaping there would place the filter's lag inside the attitude loop,
which this contract excludes. The exact flag combination for the offboard case
must be confirmed in the commander at the pinned commit before the wrapper is
written.

Inputs are clipped to the filter's domain, `|u| <= 8 rad/s`, before the
step. The proposal's 160,096-case check found no state or flag change from
that clip within the domain; the acro limit parameters allow up to 1800 deg/s
and offboard commands carry no upstream clamp.

## Consumers of the active output, traced at the pinned commit

| Consumer | Where | What it does with the shaped setpoint |
| :--- | :--- | :--- |
| P term and feed-forward | `src/lib/rate_control/rate_control.cpp` | error = setpoint minus measured rate; feed-forward gain defaults to zero |
| Integrator | same file | integrates the error, clamped toward zero on axes the allocator reports saturated |
| Anti-windup source | `MulticopterRateControl.cpp`, allocator status | downstream of the setpoint; reads the allocator, not the filter |
| `vehicle_rates_setpoint` publication | `MulticopterRateControl.cpp` | the shaped value is published so logs show what the PID tracked; raw sticks stay in `manual_control_setpoint` |
| Logger and MAVLink `ATTITUDE_TARGET` | logger topics, mavlink streams | store and send the float bits |
| Slew and clamp flags | none | no PX4 code can read them |

Subscribers for other vehicle types do not run on a multicopter build. The
shadow instance has exactly one consumer, the logger.

## Decision fields

| Field | Answer for this integration | Status |
| :--- | :--- | :--- |
| State | The next state is the rate setpoint the PID tracks. No threshold-side value selects another action. | derived from the consumer map; adopted with decision 1 |
| Mode | No flag can change a mode, guard or safety action; nothing reads the flags. | derived; adopted with decision 1 |
| Anti-windup | Handled at the allocator from saturation status; the PID integrates error against the shaped setpoint, so shaping cannot wind it up. | derived; adopted with decision 1 |
| Logging | Whether the flags are emitted and logged as new fields, and the caveat that single-sample flags near a threshold are uncertain by the step's error bound. | open: decision 3 |
| Signed zero | No control computation can distinguish the zero sign; PX4 is built with `-fno-signed-zeros`; only ULog and MAVLink serialize the bits. Whether the contract declares the sign unspecified is a choice. | open: part of decision 6 |
| Disposition | The acceptance quantity and tolerance, and the continuous-operation envelope. | open: decision 6 |

## Open owner decisions

These are quoted from the proposal. Recommendations given in chat on
2026-10-13 are not adopted here.

2. Accept the direction-dependent acceleration limits (4 rad/s^2 rising,
   2 rad/s^2 falling) on a symmetric body axis, or require a symmetric variant,
   which reopens the specification.
3. Flags: emit and log them, or do not emit them.
4. Reset: zero_reset on disarm, acro entry and offboard entry, or require a
   bumpless entry, which needs a new variant. The shadow instance also needs a
   rule; the proposal did not cover it.
5. Non-finite input: hold, or substitute the measured rate as PX4's own
   non-acro path does. The manual-control message allows NaN on any channel,
   and offboard writes NaN for every ignored axis.
6. Acceptance quantity, tolerance and continuous-operation envelope.
7. Compiler blocker: PX4 builds with `-Wfloat-equal` under a global `-Werror`,
   `-fno-signed-zeros` and `-freciprocal-math`, and sets no `-ffp-contract`;
   the generated C fails that warning set. Options are a separate library
   target with its own flags, a generator change, or a pragma wrapper.

## What this decision does not do

It authorizes no wrapper implementation, no PX4 build, no simulation and no
hardware run. The roadmap gate stays closed until the open fields above are
answered. Nothing here changes the frozen specification, the generated C, the
numerical bound or any held-out case.
