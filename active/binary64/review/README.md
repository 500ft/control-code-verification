# Claude AI technical review reconciliation

The read-only [report](report.md) reviewed technical result commit
`797bb9d6beb09de94ff0a7ed299eaa3d01fb9d43`. The report SHA-256 is
`0c0ad891db80fa470f10029c7da93f657e55d8395c3da8866a4072535329ecbb`.
The original CLI JSON remains in the external audit at
`implementation/audited-next-tasks-20261019/control-review/OUTPUT-READONLY.json`,
SHA-256 `29e10324591983dd03ddddc45420d8914da28e5aafdf8ad73ea5d88fade66a26`.
Its metadata identifies `claude-opus-5-5`, Claude Code 2.1.304, and session
`62d113ee-113e-49da-99d6-f7f1042aa097`. The report said its session ID was
unknown; the ID here comes from CLI metadata. The prompt disclosed the
claimed bound and prior failures, so the review was non-blind. The reviewer
self-reported no prior repo exposure. It used Read, Glob and Grep, made its
own unexecuted arithmetic derivation, and did not compile, run the tests or
inspect final cases. This is Claude AI technical review, not independent human
or external peer review. An earlier attempted CLI run requested Bash approval;
that run was stopped without approval or a report. The completed read-only
session had no permission denials.

I verified the registration hashes and clean technical review commit, reran
`python active/binary64/proof.py`, `python active/binary64/run.py`, the host
CMake/Ninja library build, the two historical counterexample checks, and
compared generated core bytes with the reviewed commit. The pinned PX4
target-build archive, generated config and linked-probe hashes are in
[target-build.json](../target-build.json). The reviewer did not independently
execute those builds. [The post-review supplement](../supplemental-directed.json)
was registered at `285ba77` before its execution and is counted separately in
[results.json](../results.json); it did not change the reviewed generated core.

| Finding | Verified disposition |
| :--- | :--- |
| B64-01 nonexpansive bound | The review independently derived the global 1-Lipschitz exact map and the conservative local `24U+36A` bound. I checked the operation order in the emitted C, the exact-rational calculation in `proof.py`, and the resulting envelope. Admit the numerical core only for finite binary32 inputs/dt, persistent binary64 state, strict nearest-even gradual-underflow arithmetic and the model interval below. |
| B64-02 repeated initialization | Reinitializing from a rounded publication could inject a new rounding error. This is a conditional wrapper risk, not an observed failure or an automatic reset allowance. Every entry/re-entry needs an explicit cause and segment boundary; no silent reinit within a continuous active segment. The owner-adopted bumpless source remains the preceding effective PID setpoint, and the wrapper has not been tested. |
| B64-03 rejected entry | Reproduced by the boundary control: a failed `active_double_init` leaves the old state intact. Its failure return must cause bypass and no subsequent step until a valid entry. That wrapper behavior is unresolved. |
| B64-04 rejected step output | Source inspection confirms that status `-1` returns a zero-initialized output object without mutating state. The wrapper must never publish or consume that output; its three invalid-input classes remain to be qualified. |
| B64-05 disarm ordering | Reset sets state to zero and marks it initialized. The wrapper must prove that disarm blocks active publication and that later mode entry initializes from the preceding effective PID setpoint in the adopted order. No such test ran. |
| B64-06 horizon label | Reproduced harness weakness: the original C probe printed a fixed elapsed value. It now computes `steps * dt`; the runner independently compares this with the registered case and checks the flag checksum. This path is an exact, alternating slew count check. The proof, not this loop, establishes the general envelope. |
| B64-07 persistence control | Reproduced weakness: changing a ctypes output copy could not test feedback. The new control uses the old half-ulp tie, checks that the persistent double differs from its published float and that the next compiled step continues from the double state. Publisher separation in PX4 remains untested. |
| B64-08 missing cases | The separately registered supplement executed a binary64 subnormal decay and additional NaN, infinity, negative-zero-dt and boundary controls. Strict C and the separate binary64 reference agreed. Exact rational intent covers the registered prefix; the arithmetic proof covers the rest. |
| B64-09 target assembly | The complete [object disassembly](../target-assembly.txt) is retained. It includes binary64 arithmetic and binary64-to-binary32 conversion, with no fused double operation or unresolved double helper. The linked probe is separate from firmware; firmware integration and runtime behavior remain open. |
| B64-10 runtime FP state | The pinned NuttX source initializes a task's FPSCR to zero, but no task-level FPSCR read or Cortex-M execution was performed. The review's quantitative assertions for flush-to-zero and directed rounding were not derived against this emitted program and are not adopted. Target runtime arithmetic remains a gate. A subnormal binary32 dt is outside the registered positive-dt domain, so the report's suggested accepted-dt hold scenario does not apply. |
| B64-11 flag record | `target-build.json` now includes the effective `-Os`/`-O2`, trapping and math-errno flag positions in addition to the original strict override ordering. The generated config has `CONFIG_LTO_NONE=y`; no firmware LTO effect is claimed. |
| B64-12 reference independence | The Python binary64 reference deliberately repeats the operation order and checks host C lowering. The separate `core.intent` exact-rational recurrence and the arithmetic proof test numerical correctness against the declared intent. |
| B64-13 time meaning | Exact intent consumes the already binary32-quantized dt. The 1,800-second proof horizon means the sum of admitted positive dt values is at most 1,800 seconds. It does not establish physical elapsed time or sensor timestamp accuracy. The report's claim that update count is independent of this time definition is unsupported and is not adopted. |

The adopted scoped review and focused reproduction admit the **numerical
next-state value and published binary32 value bound** for this new core under
the declared domain, strict arithmetic and summed-dt horizon. The original
binary32 failures remain failures. This admission does not establish target
runtime FP state, firmware linkage, bit or diagnostic-flag identity with exact
intent, wrapper behavior, continuous wall-clock timing, CPU cost, handling or
hardware operation. The next dependency is target runtime/integration
qualification, then the adopted wrapper requirements and directed tests.
