# PX4 timestamp-domain development result

This separately registered analysis also fails the unchanged active-variant
`0.001065 rad/s` continuous next-state ceiling. It does not replace the
[broader registered failure](../README.md), amend the adopted consumer
contract, or admit a wrapper. The [specification](spec.json), [directed cases](directed.json)
and [registration](registration.json) were committed as `d18ba3e` before this
run. The [result](results.json) is the numerical source for this analysis.

At pinned PX4 commit `c9b9e4e25e57e82fdddd5db7283c3b26fd0afa17`,
`MulticopterRateControl::Run` updates only after a new
`vehicle_angular_velocity` message. It computes `now` from
`timestamp_sample`, constrains `(now - _last_run) * 1e-6f` to
`0.000125f` through `0.02f`, and stores `_last_run = now`. It then updates
control mode and selects or holds `_rates_setpoint`. The proposed insertion is
after that selection, before `RateControl::update(rates, _rates_setpoint,
angular_accel, dt, ...)`; this call receives the same local `dt`. The header
initializes `_last_run` to zero, so the first sample normally clamps to the
upper endpoint. The visible disarm branch resets the PID integrator and gain
compression, but does not reset `_last_run`. Startup and future shaper resets
are separate from a normal `Run` dt. The binary32 endpoint bit patterns are
`0x3903126f` and `0x3ca3d70a` (little-endian byte strings in the spec).
The relevant [pinned C++ source](https://github.com/PX4/PX4-Autopilot/blob/c9b9e4e25e57e82fdddd5db7283c3b26fd0afa17/src/modules/mc_rate_control/MulticopterRateControl.cpp)
and [header](https://github.com/PX4/PX4-Autopilot/blob/c9b9e4e25e57e82fdddd5db7283c3b26fd0afa17/src/modules/mc_rate_control/MulticopterRateControl.hpp)
are the source of those placement statements.

The seven short controls exercise the compiled lower and upper dt endpoints,
state-binade crossing, slew-to-lag transition, reversal, saturation, and
variable steps. A separate control verifies reset and zero-dt hold calls and
rejects zero, below-minimum, and above-maximum dt before the core. These
controls passed their directed numerical ceiling checks; they do not prove a
continuous bound. The eighth sequence alternates timestamp gaps of 125 and
126 integer microseconds, using the pinned expression's binary32
`1e-6f` multiplication. With initial state `5/4 rad/s` and alternating
commands `+8/-8 rad/s`, strict compiled C first exceeds the ceiling at
step 80,161 after about 10.06 seconds. The retained failed first execution
is [first-attempt.json](first-attempt.json); it reached the same failure but
stopped before the remaining short controls. The second execution ran all
short controls first and then the long adversary. Both runs stop at the first
observed failure. No 1,800-second simulation or final case ran.

The independent [closed-form check](check_closed_form.py) derives a 17-ulp
rounded decrease per pair while the exact decrease is smaller, and verifies
the last compliant prefix and first crossing against the saved result. The
states remain in the same binade; both slew branches remain selected. Strict
C and the explicit binary32 reference agree on every executed update. The
trace shows a propagated error from independent exact and rounded histories,
not a compiler/reference mismatch. These 125/126 microsecond timestamp gaps
are permitted by the traced expression, but no PX4 sensor schedule or hardware
trace was measured to establish that this pattern occurs operationally.

An isolated sparse PX4 checkout at the pinned commit was obtained under
`/Users/redhose/.cache/control-code-verification/px4-pinned` with a clean
working tree. Its `MulticopterRateControl.cpp` SHA-256 is
`e9c3291ec6ec6d1b82e88bde2f0186bb1ba887321253155ac72968ebc240a911`;
the header SHA-256 is
`6b1268ffd4af3d4606112ffad95e88a89e944512da99e024612ff1fa7ffb40f8`.
The pinned module CMake source SHA-256 is
`8e40038ca55c6bdee2386c511349ab6beb517d0c7646ef465c6b3fd26f674a59`;
its common-flags source SHA-256 is
`20de4da22f4f639f2f27c7a0af6aaf374b6d7a9ca2a6c82245a01cf48255cdca`.
`command -v arm-none-eabi-gcc` exited 1 and `docker info` could not connect
to the daemon. Consequently no pinned fmu-v6c configuration or build ran,
and there are no effective target compile/link flags, target library hash,
verified compiler-option-A isolation, or linked LTO findings to claim. The
prior host-only probe remains [separate evidence](../../evidence/consumer-build/README.md).
The source shows common `-Werror` and `-Wfloat-equal`, but source flags alone
are not an effective target command. No PX4 source was changed.

Run with the repository's pinned compatible Python environment and host C
compiler:

```sh
python active/px4_domain/run.py
python active/px4_domain/check_closed_form.py
```

The result records exact commands, hashes, dt bit patterns, compiler version,
case counts and control outcomes. The generated host probe and shared library
stay under ignored `build/px4-domain`. A decision on changing the adopted
broad-domain requirement or algorithm remains necessary before admission;
this narrower source-permitted domain also failed the current ceiling. The
consumer wrapper, publisher, logging and integrator tests were not started.
