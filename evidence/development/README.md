# Development pilot stopped on a signed-zero representation mismatch

A permitted hold from negative zero preserves its sign in the explicit
binary32 reference, while generated C returns positive zero. The exact real
state and emitted flags agree. This breaks the pilot's bitwise comparison
criterion; it does not demonstrate a functional application failure. The
registered first-failure rule stopped scaling. No large randomized comparison
or ARM Linux/QEMU execution is claimed.

The original branch-contact result remains unchanged. This new discrepancy
is a sign-of-zero representation finding, separate from those conservative
threshold contacts and their unresolved consumer requirements.

## Executed scope and cost

The pre-execution [freeze](../../campaign/freeze.json) identifies generator,
runner, design, original implementations and the generated pilot input file.
Commit `6e1b4c1` recorded that freeze before execution. The
[summary](summary.json) is the source for counts, errors, runtime, memory and
raw-output hash. `executed_traces` counts completed traces; `attempted_traces`
includes the partially executed failing trace. Unexecuted inputs remain in
the frozen corpus and are excluded from agreement denominators explicitly.
`invalid_inputs` is zero after admission checking the entire pilot corpus.

Before comparisons, the existing analytic checks and independent arithmetic
controls passed. The [controls](controls.json) exercised nearest-even ties,
gradual underflow and an expression sensitive to FMA contraction. Native FPCR
was read as well. These controls establish only the exercised host environment.

The separate exact-intent cost benchmark evaluated smooth-growth development
traces through their full horizons. Its step count, elapsed time, largest
rational numerator/denominator and peak RSS are under `benchmark` in the
summary. Those are exact-reference evaluations without binary32/C comparisons;
they are not part of the comparison count. No exact subset was substituted
for the unexecuted campaign. The benchmark was affordable, but the correctness
gate failed before scaling. Resource ceilings were never approached.

The campaign used one worker and set BLAS/OpenMP thread variables to one.
The stopped process exited; no background job or resumable campaign is pending.
The summary's `next_trace_index` identifies the failing trace, not permission
to skip it. Counts are development traces/steps, not independent generated
implementations or confirmatory samples.

## Minimal reproducer and source cause

[Original failing input and observation](failure.json) preserve the first
failure before shrinking. The original trace's later update was deleted;
then the unused command input was simplified to zero. A single hold update
from negative zero remains. Removing that update leaves no observation.

The [standalone C replay](../../campaign/replay_zero_hold.c) calls both unchanged
generated functions directly, bypassing Python and ctypes. At both recorded
optimization levels it reproduces the sign change; the flags remain inactive.
[Replay outputs, commands and binary hashes](replay.json) retain the result.
Its successful exit means the known discrepancy was reproduced, not that the
bitwise comparison passed.

The reference's [hold return](../../core.py#L41) returns its binary32 state
unchanged. In [zero-reset C](../../generated/zero_reset.c#L99), the selected
hold value is added to the zero from the inactive update arm. The analogous
[tracking-reset expression](../../generated/tracking_reset.c#L110) also adds
the inactive arm. Under nearest-even, negative zero plus positive zero becomes
positive zero. The generator's conditional-selection expression therefore
preserves the real-valued map here but loses the reference's zero sign.
The direct replay and unoptimized build exclude Python transport and an
optimization-only explanation for this reproducer. No upstream defect claim
or general portability conclusion follows.

The exact-rational intent has no signed zero, so its zero error alone cannot
settle this bit-level mismatch. No supplied consumer establishes a functional
need for the sign. Neither canonicalizing zeros nor requiring sign-preserving
selection is adopted here. No semantic repair or tolerance widening was made.
A follow-up needs an explicit representation requirement and reviewed response
to this mismatch before resuming the blocked comparison domain.

## Conditional ARM comparison

The [environment inspection](environment.json) records actual commands and
exit status. Host `gcc` resolves to Apple Clang, so it is not an independent
compiler. No QEMU user-mode executable or ARM Linux cross-compiler was found
on PATH. Docker's client exists but its daemon socket is unavailable, so no
runnable container/sysroot could be inspected. No tool installation, daemon
startup or host setting change was attempted.

The executed target is native macOS ARM64. It supplies no ARM Linux OS-ABI/QEMU,
Cortex-M, PX4 FPU, scheduling or hardware timing result. A runnable pinned
Linux compiler/sysroot/QEMU environment is the exact missing prerequisite for
that conditional comparison.

## Reproduce and retained raw data

From the repository root, with its pinned numerical dependencies:

```sh
python campaign/generate_cases.py pilot 2 /tmp/control-pilot-inputs.jsonl
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  python campaign/run.py /tmp/control-pilot-inputs.jsonl /tmp/control-pilot-run
```

The output directory must not exist. Compare the input hash to the freeze and
the scientific fields to the summary; timing, binary identity and compressed
file bytes can vary between executions. The runner intentionally stops at the
known representation mismatch. The exact commands for the standalone replay
and arithmetic controls are in their linked records. CI replays the minimal
case and controls, with explicit assertions preserving the known discrepancy;
it does not start the blocked campaign.

Raw input JSONL, compressed per-step outputs, binaries, LLVM, benchmark/progress
log and original first-failure record are retained externally under the audit's
`implementation/compute-tasks-20261011/receipts/control-pilot*` paths. Compact
outputs and hashes are committed here. All original traces, generated sources,
figures and evidence from the prior study remain unchanged. Final outcomes
were neither read nor generated. Functional branch use and the independent
human reviewer remain unresolved before wrapper qualification.
