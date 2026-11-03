# PX4 wrapper development registration

Parent main `d0386507a2f59dccec0134b0d407d52286051791`; host PX4
`c9b9e4e25e57e82fdddd5db7283c3b26fd0afa17`. This registration precedes
the integration patch, module results, and simulator attempts. It uses
development histories only; all final cases remain closed.

The baseline is the unmodified pinned `px4_sitl_default` rate module. The
experiment must be opt-in and disabled by default. Compare its disabled path
to the baseline at the effective PID rate setpoint, published raw setpoint,
integrator status, and torque setpoint. For an enabled in-domain path, compare
the active state and publication to the admitted persistent-binary64 C core
with the same binary32 commands and dt; compare flags to its emitted semantics.
Each registered history is one scenario, not one sample per tick. The admitted
numerical ceiling concerns a summed-positive-dt segment, not simulator wall
time. A simulator trace cannot establish a universal bound or Cortex-M timing.

The pinned source's commander checks manual setpoint `valid` and
`COM_RC_LOSS_T` (default 0.5 s); offboard availability uses the timestamp on
`offboard_control_mode` and `COM_OF_LOSS_T` (default 1.0 s). The rate module
only receives `vehicle_control_mode` and `vehicle_rates_setpoint`; the latter's
timestamp is not the offboard heartbeat. A tick without a new message may use
the held raw command while the host still declares that source valid. Reject
source timestamp regressions. Expose age from the last accepted source stamp;
do not refresh it from a shaped publication. A separate rate-setpoint age
timeout is **not specified** by the pinned host or adopted contract. Do not
invent one. On commander-declared source loss/mode transition, bypass the
active shaper. Manual source validity requires `valid`; mode and arming flags
still govern actuation. The exact source-loss transition must be observed in
SITL before wrapper admission.

| ID | Directed history | Required observation |
| :--- | :--- | :--- |
| baseline | Feature disabled across startup, commands, disarm, restart | Raw topic, PID input, integrator and torque agree with unmodified pinned run, subject to identical simulator stimuli. |
| startup | No source, then first finite manual command | No active publication until valid entry; entry output equals preceding effective PID input; update starts next accepted rate tick. |
| disarm | Active command and simultaneous disarm, then rearm | Disarm has precedence; active publication stops and state resets to zero; later entry is explicit, with no artificial segment reset. |
| mode | Acro, offboard BODY-RATE, other offboard, attitude/position, then return | Active only when armed, rates enabled, attitude disabled and manual or offboard body-rate source is selected; every rate-loop mode with valid inputs runs independent shadow state. |
| ignored | Offboard ignored sentinel on one axis, then finite commanded axis | Ignored axis uses measured rate without lag; other axes retain active state; re-entry initializes from preceding effective PID input. |
| entry | Preceding effective PID input at cap and outside cap | In-domain entry is bumpless; out-of-domain entry is rejected with bypass and cause; no clipped entry. |
| invalid | NaN/Inf commanded manual/offboard axis, NaN/Inf measured ignored axis | Reject commanded nonfinite values; hold last finite effective input if present. Ignored-axis nonfinite measured value rejects that axis. Never step core with nonfinite values or publish rejected output. |
| messages | No-new-message ticks, stale/absent/reordered messages, source loss, mode transition | Held raw input remains distinct from shaped output; age reflects source timestamp; reordered stamp rejects; source loss bypasses without making a new timeout. |
| feedback | Deliberate raw-topic feedback control against separated publisher | Only known-defect control writes shaped output into the subscribed raw topic; normal path never does. Defect label follows publisher-separation requirement, independently of numerical comparison. |
| logging | Valid, rejected, held, bypass and reset cycles | Log raw, shaped, effective PID input, shadow outputs, state, flags, cause, validity, freshness and source identity; logger subscribes to separate shaped topic. |
| integrator | Same measured/commanded history with feature disabled/enabled, reset, allocator positive/negative saturation | Observe actual `rate_ctrl_status` integrator and torque with shaped error, no flag authority; saturating allocator clamps the appropriate sign and disarm resets. |

Module histories may be mocked but must be labeled as such. Actual SITL
qualification requires a running pinned simulator, a known-good baseline,
mode/source messages and recorded uORB/ULog outputs. If the simulator cannot
build or run, retain the exact command/error and completed module checks;
do not claim SITL or wrapper admission. Record setup and execution cost
separately. The scoped Claude AI technical review is required before wrapper
admission, with reviewed commit, model/session, prior exposure and per-finding
dispositions recorded.
