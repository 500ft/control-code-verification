# Development computation design

This is a bounded extension of the existing finite numerical domain. The
[design](design.json) fixes strata, seeds, budgets, comparison rules and stopping
criteria before outputs are observed. It does not qualify integration or adopt
a branch-use contract. PR #4 remains the prerequisite source/use review.

Directed cases cover signed zero, hold/reset precedence, limit neighbors,
positive and negative slew thresholds with adjacent binary32 inputs, and
subnormal arithmetic. Random traces use independent deterministic seeds per
variant and stratum. Reset-anchored threshold traces give permitted states
without consulting execution outcomes. Smooth small-input traces expose
rational denominator growth. All data is development data. No withheld set is
created or read, overriding the skill's usual reserved-set phase for this task.

Before numerical comparison, benchmark exact intent on the smooth-growth pilot
traces and run the existing independent analytic checks. If the pilot passes,
use its measured cost to apply the registered scaling rule. The maximum random
budget is an upper limit, not a requested count of independent implementations.

Record inputs before execution and retain compressed raw output externally.
Store the generator, design, corpus and implementation hashes in the freeze
record. A C/reference bit disagreement, including sign-of-zero, blocks scaling
until classified. A difference between exact and rounded branch flags within
the numerical bound is a requirement finding, not automatically an error.

Host controls check nearest-even, gradual underflow and a contraction-sensitive
expression. A separate ARM Linux/QEMU result requires an executable compiler,
sysroot and emulator; a macOS ARM64 run alone does not establish that result.
No install, daemon startup or host change is needed to report unavailable tools.
