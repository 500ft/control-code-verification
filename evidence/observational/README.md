# Completed descriptive development comparison

The full registered randomized budget completed with exact-reference coverage
at every step and no observed numerical-bound violation. Exact intent and
rounded implementations sometimes returned different branch flags. The
supplemental pilot also retained the known signed-zero mismatch. The
[generated result table](table.md) gives separate trace and step counts for each
stage and mechanism; its linked JSON files are the numerical sources.

This is a separate [observational protocol](../../campaign/observational-design.json).
The [original stopped pilot](../development/README.md), criterion and outputs
remain unchanged. No bitwise acceptance, zero canonicalization, tolerance
change, functional contract or human approval was adopted.

## Domain, exposure and trajectories

The original [specification](../../spec.json), parameter variants and finite
horizon remain unchanged. The [existing generator](../../campaign/generate_cases.py)
covers variable dt, saturation/ULP neighbors, reset-anchored slew thresholds,
reset precedence, smooth rational growth and tiny values. The original seed
rule and strata are preserved. The supplemental
[freeze](../../campaign/observational-freeze.json) predates its pilot, and the
[scale registration](../../campaign/scale-registration.json) records the actual
corpus hash and resource projections before the full run. Only development
inputs were generated or read. No reserved corpus was created or opened.

Exact intent, explicit binary32 and C retain their own states for each entire
trace. Each step also evaluates C on the binary32 prior state. Common-input
comparisons separate implementation differences from consequences of earlier
state differences. Nothing resets a divergent history except a reset already
present in that trace. Initial states are restored only between independent
input traces.

All executed steps have exact stateful intent and local exact-intent checks;
no sampled exact subset stands in for the rest. The unchanged deterministic
bound recurrence is checked on both rounded histories. The original strict
bitwise failure remains recorded even when numeric values coincide. Signed
zero, numeric value, returned branch, bound and unclassified differences are
separate counters, including zero counts. Category counts can overlap.

## Independent checks and discrepancy interpretation

Before scale, an independent rounding oracle reconstructed binary32 operations
using exact fractions and adjacent representable candidates. It checked every
directed pilot step and each sixteenth random pilot step, under the
prospectively recorded selection rule. The [audit](pilot-audit.json) also records
the existing independent closed-form checks. This oracle uses a separate
rounding implementation from NumPy; shared discrete update requirements still
limit the independence claim.

A [separate raw-output recount](independent-review.json) recovered every
classification and its affected traces. First representatives of each observed
branch transition were reduced by contiguous deletion and verified to be
single-deletion minimal, without optimizing scalar inputs. An independent
rounding replay and exact operand derivation verify each retained example.
The JSON includes full minimized inputs, original trace/step, replay counts,
outputs, threshold and exact signed gap. These examples do not enumerate all
possible disagreement mechanisms.

In the minimized branch examples, the exact operand lies strictly beyond the
threshold, while the rounded operand equals it. The strict rounded predicate
therefore returns inactive. These are observed exact-versus-rounded flag
differences, distinct from the earlier conservative contacts where flags agreed.
C and binary32 agree on branch flags in this exercised corpus. Functional
consequences depend on a consumer requirement that remains unspecified.

The later [Claude AI technical review reconciliation](../review/README.md)
reproduced reverse-direction slew flips in separate targeted development
cases. Those cases are outside this frozen corpus and do not alter its counts.

Signed-zero differences remain those in the preserved
[one-step reproducer](../development/replay.json). Source inspection found no
signbit, copysign, reciprocal-state, or other sign-sensitive functional consumer
in the core/generator. The division denominator is positive under the admitted
update domain, and branch predicates treat either zero sign equally. Bitwise
verification observes the sign difference. Exact fractions identify both zeros
as the same rational value. No external application has been supplied, so this
source audit does not establish that future consumers can discard zero signs.

The later [focused review replay](../review/reproduced.json) also found a
tracking-reset and underflowing-update path to the same reference/C zero-sign
difference. The original first-failure record remains the hold case.

## Executed ARM Linux compiler/emulator comparison

The [cross registration](../../campaign/cross-registration.json) pins inputs,
source hashes, compiler flags, image digest, package versions and target before
execution. The [standalone C driver](../../campaign/cross_runner.c) transports
binary32 values as hexadecimal bits and retains a native stateful history
alongside a common-reference-input call. It consumed the original registered
public traces, independently of the large randomized run.

[Cross results](cross-summary.json) show byte-identical output for native
macOS Apple Clang, native ARM Linux GCC and QEMU user mode. The independent
rounding oracle also checked those outputs. The preserved signed-zero hold was
then replayed separately on QEMU and still produced positive zero; its count is
separate from the original-corpus agreement denominator.

The executed target is ARMv8-A, `aarch64-alpine-linux-musl`, ELF64 with the musl
interpreter. GCC and QEMU versions plus installed package identities are in the
[environment record](cross-environment.log). [ELF metadata](cross-elf.txt),
[binary hashes](cross-binary-hashes.txt) and [input hashes](cross-input-hashes.txt)
are retained. The displayed ELF metadata has trailing whitespace removed; the
original command output remains external. Optimization is `-O2`, contraction is off, fast math is disabled,
and signed zeros are enabled. Native and QEMU arithmetic controls exercised
nearest-even ties, gradual underflow and a contraction-sensitive expression;
FPCR reported zero, including no flush-to-zero. This describes the exercised
arithmetic environment, not every possible floating-point operation.

QEMU used `-cpu cortex-a53 -L /`. This is a Linux user-mode OS-ABI comparison,
not Cortex-M/PX4 or hardware timing qualification. Deterministic compiler builds
do not increase the number of independent generated implementations.

## Resources and reproduction

Each native stage used one worker and one BLAS/OpenMP thread. Pilot timing and
storage projections justified the existing full budget without consuming the
allowance unnecessarily. The summaries record runtime, peak process RSS,
artifact bytes, source hashes, per-stratum counts and raw-output hashes.
Per-trace progress and periodic checkpoints were written externally. Both runs
completed, so no resume index is pending.

The isolated [VM identity](vm-identity.json) records one CPU, limited memory,
reused cached image and a pinned Alpine container. The first root-disk size
attempt failed before execution because it was smaller than the image; its log
was preserved. A supported larger virtual disk succeeded within the physical
artifact allowance. The existing VM profiles and global Docker context were
unchanged. Container and VM were stopped after the comparison. No privileged
host change or security bypass was used.

With the pinned Python dependencies, from the repository root, substitute an
empty external output directory for each run:

```sh
python campaign/generate_cases.py pilot 2 /tmp/observed-pilot.jsonl
python campaign/observe.py /tmp/observed-pilot.jsonl /tmp/observed-pilot
python campaign/audit_observation.py /tmp/observed-pilot.jsonl /tmp/observed-pilot/rows.jsonl.gz
python campaign/generate_cases.py campaign 512 /tmp/observed-campaign.jsonl
python campaign/observe.py /tmp/observed-campaign.jsonl /tmp/observed-campaign
```

`observe.py` sets numerical-library thread variables before importing NumPy.
For the independent recount, arrange the input/output files as in the recorded
external receipt, then run `campaign/summarize_observation.py` and
`campaign/explain_examples.py`. Regenerate only the Markdown table with
`python campaign/render_summary.py`.

For the cross comparison, create the hex inputs with `campaign/cross_inputs.py`,
compile the standalone driver with the recorded flags and sources, and execute
it with redirected input. [cross-build.sh](cross-build.sh) preserves the exact
Linux compile/control/native/QEMU commands; the image and explicit package
pins are in the registration. The independent known-zero input has its own
[prospective diagnostic record](cross-zero-registration.json). The external
receipt retains installation, failed startup, execution and shutdown logs.

Raw corpora, compressed outputs, full discrepancy indexes, binaries, LLVM and
checkpoints live in the external audit's `implementation/goal-compute-20261011`
directory. Committed summaries and minimized inputs are sufficient to inspect
the findings; corpus hashes permit regeneration. These results support only
the exercised development corpora and environments. Human reviewer assignment
and functional branch/representation requirements remain gates to wrapper
qualification; no wrapper or integration run occurred.
