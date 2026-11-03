# Pinned wrapper input ambiguity

The pinned PX4 rate-controller input cannot distinguish an ignored offboard
yaw axis from an invalid commanded yaw value. This blocks the registered
three-class invalid-input requirement at the intended insertion point. No
wrapper was installed or admitted, and no final case was opened.

The parent PX4 commit is
`c9b9e4e25e57e82fdddd5db7283c3b26fd0afa17`. In
`src/modules/mavlink/mavlink_receiver.cpp:1856-1938`, body-rate offboard
messages with roll and pitch enabled and thrust supplied create a
`vehicle_rates_setpoint`. Its yaw is assigned `(float)NAN` when the MAVLink
`ATTITUDE_TARGET_TYPEMASK_BODY_YAW_RATE_IGNORE` bit is set; otherwise the
supplied yaw float is copied without a finiteness check. The type-mask bit is
not copied. `msg/versioned/VehicleRatesSetpoint.msg` has yaw, timestamp,
thrust and reset fields but no per-axis ignore or source-validity fields.
`src/modules/mc_rate_control/MulticopterRateControl.cpp:184-188` subscribes
to that topic and substitutes measured rate for every non-finite yaw. The
commander can report BODY-RATE mode in both cases. The offboard heartbeat
timestamp is held in `offboard_control_mode`, not in the rate setpoint.

The [compiled development reproducer](ignored_axis_alias.c) mirrors the
pinned yaw assignment with the MAVLink ignore-bit value from
`common.xml:4231`. With the yaw-ignore bit set and a finite unused payload,
and with the bit clear and a canonical NaN payload, it emits the same full
rate message. The [executed output](alias-result.json) records identical yaw
bits `7fc00000` and message equality. This is a focused source-mapping
reproducer, not execution of the full PX4 MAVLink receiver. The source
itself proves the alias for the chosen payload. No deterministic downstream
wrapper that receives only this message can apply ignore/bypass to one and
invalid-command rejection to the other.

Source SHA-256: `mavlink_receiver.cpp`
`a4f7327e92c6c698e1f40a8601191bb55b144160a3afd6ed451ebee3d8e683b0`,
`VehicleRatesSetpoint.msg`
`ffd2818487ed90b95908a20b967a6ec4357a922aa59ca00919b01638f06a6c58`,
`MulticopterRateControl.cpp`
`e9c3291ec6ec6d1b82e88bde2f0186bb1ba887321253155ac72968ebc240a911`.
The original pinned worktree is unchanged; the isolated integration worktree
contains no edits to these three files.

Run from this repository root:

```sh
mkdir -p build/integration
cc -std=c11 -O2 -Wall -Wextra -Werror integration/ignored_axis_alias.c -lm -o build/integration/ignored_axis_alias
build/integration/ignored_axis_alias
```

Apple Clang 16 compiled and ran the repro. The combined compile/run took
`0.09 s` wall time in one local `/usr/bin/time -p` observation; this is
local reproduction cost, not a simulator measurement. The isolated pinned
PX4 source worktree was expanded from sparse checkout. A baseline
`px4_sitl_default` CMake configure took `35.5 s` and could not generate
because the GPS devices submodule was missing. After checking out that
recorded submodule, `px4_sitl_sih` configured in `7.8 s`; its unmodified
baseline build stopped during an external Micro-XRCE-DDS configure because
its submodule source was absent. That submodule was then checked out, but
the build was not resumed after the input ambiguity became the primary
blocker. No SITL or rate-module history was run. The failed attempts are
retained outside the repository under
`/Users/redhose/.cache/control-code-verification/`:

| Log | SHA-256 |
| :--- | :--- |
| `px4-integration-baseline-build.log` | `af7f1397e66fb4d9917def6521381e9bc5af9fc2a2f3b06518c2b62fadeecfcb` |
| `px4-integration-baseline-config.log` | `c936bd3c19350f64335c88b4015f5af853c4aeeab1c8161f2997521d1885d64e` |
| `px4-integration-baseline-sih-config.log` | `960e7ca4b0a5ab58fa4f27f2b7457b2a37977ad07afec172804539d86551e504` |
| `px4-integration-baseline-sih-build.log` | `1fc568cadb13cb4030d9ee099a4d667a1e7dcbee6583e1c2930709f105f00724` |

The missing input is an explicit per-axis ignored/commanded provenance
contract on the rate-setpoint path, including how every supported publisher
sets it. Equivalently, the owner could revise the adopted requirement to
treat all non-finite offboard yaw values alike, but that is a different
functional contract and has not been approved. After that choice, register
the updated consumer semantics and continue the wrapper histories and SITL
build. No conclusion about integrator response, publisher separation,
source-age handling or target runtime arithmetic follows from this result.
