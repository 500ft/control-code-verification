# Separate active variant: directed development result

The [specification](spec.json) and [directed cases](directed.json) were
registered at commit `e735af5` before generating or executing the new core.
[Registration](registration.json) pins both input hashes. The original
`spec.json`, 4/2 shadow generated C, numerical results and final cases were
left unchanged. The later [Claude AI technical review](review/README.md) is
non-blind and its two review-motivated cases were registered separately before
execution.

The [executed results](results.json) show that the adopted continuous
next-state ceiling fails. Both registered half-ULP slew sequences crossed
`0.001065 rad/s` at step 17,868, after about 0.273 s. At step 24,576 the
absolute error was `0.00146484375 rad/s`. Strict AppleClang C and the
independent explicit binary32 reference agreed on every executed directed
call; this is a difference between rounded state recurrence and exact intent,
not an adapter disagreement. The short case IDs containing `unslewed` were
misnamed at registration: their inputs activate the slew branch. They are
retained under their registered names. The separately
[registered review supplement](supplemental-directed.json) exercises the
interior branch in both signs, with C and binary32 reference agreement. The
first NaN rejection result was true by string short-circuit in the harness;
the corrected development replay calls the numerical validator with NaN.

The measured quantity is propagated next-state divergence between two
independently evolved histories from the same initial state. The adopted
[consumer contract](../CONSUMER.md#adopted-development-contract), which
predates this registration, requires a propagated bound over a continuous
segment. The one-step local error on the tie case is smaller; this result does
not claim a local-error violation.

A [separate closed-form check](check_counterexample.py) verifies the cause.
For `x0=1`, `u=8` and `dt=513/33554432 s`, the exact symmetric slew increment
is `2 dt = 513/16777216 rad/s`, or 256.5 binary32 ulps while the state is in
`[1,2)`. Each generated-C addition rounds to 256 ulps by ties-to-even; the
mantissa remains even on the next step. Exact intent advances 256.5 ulps.
Neither the slew nor the state cap stops this prefix. After `n` steps the
absolute error is `n/16777216 rad/s`. The registered first crossing is the
least integer `n` for which that fraction exceeds the ceiling. The negative
sequence is symmetric. A continuous 30-minute run can contain this prefix
without any reset, so a pointwise ceiling for every such segment is refuted.
The entire 30-minute run was not simulated or claimed as executed.
The case uses a `dt` within the registered variant domain but below the
pinned PX4 rate module's `0.125 ms` lower clamp. It refutes the stated
all-registered-input ceiling, not a narrower PX4-tick claim. That narrower
claim has not been qualified or substituted into the adopted contract.

Generate and reproduce with the pinned Python environment from the repository
root:

```sh
python active/generate.py
python active/qualify.py
python active/check_counterexample.py
cmake -S active -B build/active-cmake -G Ninja \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build/active-cmake --verbose
```

The new C source is compiled separately with C99, O2, no fast math or
contraction, warnings as errors. The host-only CMake target applies strict
arithmetic and a narrow float-equality warning override after the PX4-like
common flags. The actual local command includes ThinLTO and produced an LLVM
bitcode object in `libactive_symmetric_core.a` (SHA-256
`35a16845ce84824e14594744c0b6f0789d475eb975ad90355478ded51c7d829d`).
The exact compiler, oracle, harness and source/binary hashes for the executed
directed replay are in [results.json](results.json). This host archive has not
been linked into PX4 or executed on Cortex-M.

Pinned PX4 freshness paths were traced before any wrapper implementation.
The [manual selector](https://github.com/PX4/PX4-Autopilot/blob/c9b9e4e25e57e82fdddd5db7283c3b26fd0afa17/src/modules/manual_control/ManualControlSelector.cpp)
compares `timestamp_sample` to its parameterized timeout; the
[manual-control module](https://github.com/PX4/PX4-Autopilot/blob/c9b9e4e25e57e82fdddd5db7283c3b26fd0afa17/src/modules/manual_control/ManualControl.cpp)
sets that timeout from `COM_RC_LOSS_T`. The [commander's manual check](https://github.com/PX4/PX4-Autopilot/blob/c9b9e4e25e57e82fdddd5db7283c3b26fd0afa17/src/modules/commander/HealthAndArmingChecks/checks/rcAndDataLinkCheck.cpp)
uses the selected setpoint's `timestamp` and the same parameter. Its
[offboard check](https://github.com/PX4/PX4-Autopilot/blob/c9b9e4e25e57e82fdddd5db7283c3b26fd0afa17/src/modules/commander/HealthAndArmingChecks/checks/offboardCheck.cpp)
compares `offboard_control_mode.timestamp` to `COM_OF_LOSS_T`. That is a
control-mode signal check, not a freshness check on each
`vehicle_rates_setpoint`. The [rate module](https://github.com/PX4/PX4-Autopilot/blob/c9b9e4e25e57e82fdddd5db7283c3b26fd0afa17/src/modules/mc_rate_control/MulticopterRateControl.cpp)
holds its selected rate setpoint when no topic update arrives. These source
paths do not justify a new fixed timeout for a future shaper.

The local full PX4 checkout is at another commit and `arm-none-eabi-gcc` is
absent from `PATH`; `docker info` also could not connect to a daemon. Effective
pinned `fmu-v6c` compiler commands, linked arithmetic and target LTO remain
unverified. Because the new core already fails the adopted continuous ceiling,
no PX4 wrapper, shaped publisher, logger subscription, freshness handler or
integrator test was implemented or admitted. The diagnostic flags are emitted
by the generated core but have no PX4 logger consumer. No final case, broad
random campaign, flight or physical run was opened.
