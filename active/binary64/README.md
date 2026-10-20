# Persistent binary64 active development variant

This separately registered precision variant passed its directed host replay
and has a prospective absolute arithmetic bound below the unchanged
`0.001065 rad/s` ceiling over the broad 1,800-second domain. The
[specification](spec.json), [cases](directed.json), and [arithmetic proof](PROOF.md)
were committed at `f5bf59a` before implementation output. The [executed
result](results.json) is the source for case counts and observed errors;
[proof.py](proof.py) calculates the universal arithmetic envelope. This is
development evidence pending the scoped Claude AI technical review and PX4
integration checks, not an admitted wrapper.

The core stores binary64 state between calls. Finite binary32 command and dt
inputs promote exactly to binary64. Startup copies an in-domain preceding
binary32 PID setpoint exactly; disarm resets the persistent state to zero.
Zero dt is a separate hold, while invalid and out-of-domain calls are rejected
without changing state. Positive updates evaluate the named binary64
operations in [the proof](PROOF.md), with symmetric 2/2 rad/s² slew, tau
0.25 s, and the unchanged state/input limits. Slew and clamp flags describe
the binary64 comparisons and remain diagnostic. A binary32 output is rounded
from the capped state for publication, but that rounded value never feeds the
next persistent state. The numerical boundary does not decide source age,
mode, bypass or logger behavior.

The directed host replay includes both retained binary32 failure sequences,
threshold contacts, saturation and reversal, variable-step jitter, boundary
rejection, initialization, reset and hold. Strict compiled C matched a
separately written binary64 reference on all executed calls. Exact rational
intent was evolved for each known counterexample and a finite jitter prefix.
A compiled alternating-input sequence exercised the broad-domain maximum
positive-update count at minimum dt across 1,800 seconds; its final state and
checksum matched its simple exact recurrence. This sequence alone is not the
universal argument. The [proof](PROOF.md) bounds every registered input/dt
history by nonexpansiveness and a local rounding envelope, with subnormal
terms and published binary32 conversion separate. Its whole-output bound is
about `3.74e-7 rad/s` under the stated strict IEEE arithmetic assumptions.
The earlier [broad binary32 failure](../README.md) and [PX4 timestamp-domain
failure](../px4_domain/README.md) remain unchanged. Those failures refute the
registered binary32 implementation, not every possible compensated float32
method.

The [pinned target-build record](target-build.json) describes an isolated
PX4 `fmu-v6c` configure and build with an official Arm GNU 13.2 toolchain.
The generated NuttX config has `CONFIG_ARCH_DPFPU=y` and `CONFIG_LTO_NONE=y`.
The separate strict [option-A library definition](px4_option_a.cmake) was
included in an isolated checkout and compiled with target common flags followed
by strict local overrides. The existing rate module also compiled. A separate
[link probe](link_probe.c) linked that library, and its assembly contains
`vadd.f64`, `vsub.f64`, `vmul.f64` and `vdiv.f64`; no double software-helper
imports remain in that small linked artifact. The adapter was removed from
the PX4 checkout after recording the commands and hashes. The core was not
linked into firmware or executed on Cortex-M. Code size and instructions are
build evidence, not CPU timing or handling evidence. The [STM32H743
datasheet](https://www.st.com/resource/en/datasheet/stm32h743bi.pdf) describes
a double-precision FPU; the generated config and actual compiler command are
the evidence for this particular build's FPU selection.

Reproduce the host numerical result from the repository root with the pinned
compatible Python environment, C compiler, CMake and Ninja:

```sh
python active/binary64/proof.py
python active/binary64/generate.py
git diff --exit-code -- active/binary64/generated
python active/binary64/run.py
cmake -S active/binary64 -B build/active-binary64-cmake -G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build/active-binary64-cmake --verbose
```

The target-build record includes the isolated source/toolchain identity,
generated config hash, effective compile command, flag ordering, archive and
linked-probe hashes. Reproduce that build by placing the official Arm GNU
13.2 toolchain on the PATH for the command only, configuring the pinned PX4
checkout for `px4_fmu-v6c_default`, and temporarily including
`px4_option_a.cmake` from its `src/lib/rate_control/CMakeLists.txt`. Build the
`ActiveDoubleProbe` and `modules__mc_rate_control` targets. Restore the PX4
CMake file after extracting the compile command and artifacts. The adapter
is build-only and has no PX4 runtime consumer.

The next gate is a scoped Claude AI technical review pinned to this actual
result commit. Even if that review admits the numerical core, publisher
separation, freshness, three invalid-input classes, ignored-axis bypass,
bumpless re-entry, disarm-only shadow reset, logging, and PID integrator
response still need independent wrapper qualification. No final case,
physical test, flight or CPU timing measurement was performed.
