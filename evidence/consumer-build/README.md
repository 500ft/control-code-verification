# Build-only compiler probe

This probe uses the unchanged `generated/zero_reset.c` and
`generated/tracking_reset.c`. It reproduces the relevant [pinned PX4 common
flags](https://github.com/PX4/PX4-Autopilot/blob/c9b9e4e25e57e82fdddd5db7283c3b26fd0afa17/cmake/px4_add_common_flags.cmake)
on the host, then places strict arithmetic and a narrow `-Wno-float-equal`
override on this library target. `-Werror` remains in force. The previous
[compile failure](../review/README.md) with `-Wfloat-equal -Werror` is
preserved; the generator and frozen specification are unchanged.

Reproduce from the repository root:

```sh
cmake -S evidence/consumer-build -B build/consumer-build -G Ninja \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build/consumer-build --verbose
find build/consumer-build/CMakeFiles/control_core.dir -name '*.o' -exec file {} +
```

The executed host build used AppleClang 16.0.0.16000026 on macOS arm64,
CMake/Ninja, and produced `libcontrol_core.a` (SHA-256
`e3f2e3a51817a71b33d9924ebe7825ee91f346e82a898de6d199d8712fcf58cb`).
The generated sources hashed
`dd8d0095e4f7d0b548410d69f2da2cad4c3a0f3d1cc50e2fae3fd7a043d34333`
and `19411d66fa6fbb46f7e6e4430d5e2ba68bd92ba6e194e714edee45429e3ac9be`,
respectively. The actual `compile_commands.json` shows `-std=c99`, `-O3` followed by
`-O2`, `-flto=thin`, the PX4-like common flags, then
`-fno-fast-math -fsigned-zeros -fno-reciprocal-math -ffp-contract=off
-Wno-float-equal` on both source files. The resulting objects are LLVM bitcode
wrappers, and `nm` finds both generated entry points in the archive. This
checks option ordering and LTO object creation, not linked or executed
floating-point behavior. The archive hash describes this one host build.

The local full PX4 checkout is at `d6f12ad1c4f70ad3230afd7d86e971421e02fef4`,
not the chosen `c9b9e4e25e57e82fdddd5db7283c3b26fd0afa17`, and
`arm-none-eabi-gcc` is absent from `PATH`. A pinned `fmu-v6c` build could not
be run here. The chosen PX4 module's [CMake source](https://github.com/PX4/PX4-Autopilot/blob/c9b9e4e25e57e82fdddd5db7283c3b26fd0afa17/src/modules/mc_rate_control/CMakeLists.txt)
currently compiles the rate module, not this proposed isolated numerical
library. Target compilation, LTO linking and runtime arithmetic remain open.
