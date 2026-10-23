# FPSCR boot-path trace for the pinned fmu-v6c target

The [binary64 proof](../PROOF.md) assumes IEEE binary64 arithmetic with
nearest-even rounding and gradual underflow. On Cortex-M7 those properties are
runtime state: FPSCR.FZ (flush-to-zero, bit 24), FPSCR.DN (default NaN,
bit 25) and FPSCR.RMode (bits 23:22) can be changed by firmware, and FPDSCR
supplies the default FPSCR when the processor creates a floating-point
context automatically. This trace asks whether anything on the pinned boot
path, task-start path or firmware link sets those bits. The
[registration](registration.json) was committed at `1ab4ce7` before the
result and pins the question, sources, method and decision rule. The
[result](results.json) owns every file, line, bit, hash and count.

Conclusion: no FZ, DN or non-nearest RMode setting was found on the traced
path. The pinned NuttX reset entry (`stm32_start.c`) calls `arm_fpuconfig()`,
which sets CONTROL.FPCA, clears FPCCR.ASPEN and FPCCR.LSPEN and grants
CP10/CP11 access; it never writes FPDSCR, and `NVIC_FPDSCR` is defined but
unreferenced. Every task and pthread created through
`nxthread_setup_scheduler` receives an initial exception frame with
`regs[REG_FPSCR] = 0`, which sits in the hardware-stacked extended frame and
is loaded into FPSCR by the first exception return into that task; software
context switching moves only S16-S31. The only `vmsr fpscr` in the traced
NuttX directories is `longjmp` restoring the value `setjmp` saved. PX4 has no
FPSCR or FPDSCR write (the CMSIS `__set_FPSCR` in `gyro_fft` has no caller and
that module is not in the fmu-v6c build), compiles without `-ffast-math`,
`-funsafe-math-optimizations` or `-Ofast`, and links the flat firmware with
`-nostartfiles -nodefaultlibs -nostdlib`. The pinned toolchain's startfile
spec adds `crtfastmath.o` (which ORs FZ into FPSCR) only under one of those
three flags and only when startfiles are linked at all; `-###` probes with the
pinned link flags produce no `crtfastmath.o` even with `-ffast-math` added,
while the control without `-nostartfiles` does. In the linked archives, only
the newlib `fenv` functions in `libm.a` write FPSCR, and no source references
them; `libgcc.a` has none. The cached pinned configure has no translation
unit with a fast-math trigger flag.

Sources are sparse checkouts at the exact SHAs (PX4
`c9b9e4e25e57e82fdddd5db7283c3b26fd0afa17`, NuttX
`6e8169b9e1d571df4fbe2282aadc0541092253c6`, the gitlink verified at the PX4
commit) and the official Arm GNU 13.2.rel1 toolchain recorded in
[target-build.json](../target-build.json). The result lists each cited file
with its SHA-256 and line numbers, the grep hits, the toolchain `-###`
counts, the `crtfastmath.o` disassembly and the `vmsr` functions in `libm.a`.

Limits. This is a source and toolchain trace, not a target readout: no
register was read on hardware or in an emulator, and no firmware was
executed. The FPDSCR reset value and the ASPEN dependence of FPDSCR loading
come from Arm documentation, not from source. A whole-firmware instruction
scan was not performed: the full `px4_fmu-v6c_default.elf` link in the cached
build directory failed on this host (`flock` is absent for the NuttX apps
archive step, and the partial apps archive then left `nsh` symbols
unresolved); the cached checkout was not cleaned. The idle thread keeps the
hardware reset FPSCR and is not traced; no PX4 module runs on it. The
`config_sha256` in `target-build.json` could not be matched to a file in the
cached build directory, which was reconfigured after the restored CMake file;
the relevant configuration symbols are checked directly. A traced write that
sets FZ, DN or RMode, a firmware link without `-nostartfiles` under a
fast-math flag, a referenced `fenv` function, or a target readout showing such
bits in the rate-control thread would change the conclusion.

To reproduce, check out both repositories at the pinned SHAs, grep the traced
directories for `fpscr|FPSCR|FPDSCR|FPCCR|CPACR|vmsr|fesetround|fesetenv|feenableexcept|ffast-math|funsafe-math|Ofast|crtfastmath|nostartfiles`,
read the hits listed in the result, and run with the pinned toolchain on the
PATH:

```sh
arm-none-eabi-gcc -dumpspecs | grep -A1 '^\*startfile:'
arm-none-eabi-gcc -mcpu=cortex-m7 -mthumb -mfpu=fpv5-d16 -mfloat-abi=hard --specs=nosys.specs -nostartfiles -nodefaultlibs -nostdlib -### dummy.o -o a.elf 2>&1 | grep -c crtfastmath
arm-none-eabi-objdump -d "$(arm-none-eabi-gcc -mcpu=cortex-m7 -mthumb -mfpu=fpv5-d16 -mfloat-abi=hard -print-file-name=crtfastmath.o)"
arm-none-eabi-objdump -d "$(arm-none-eabi-gcc -mcpu=cortex-m7 -mthumb -mfpu=fpv5-d16 -mfloat-abi=hard -print-file-name=libm.a)" | grep -B40 vmsr | grep '^[0-9a-f]* <'
```
