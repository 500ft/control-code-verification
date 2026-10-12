# Claude AI technical review reconciliation

The numerical next-state-value claim is admitted for the [declared domain](../../spec.json),
strict binary32 arithmetic and the registered finite horizon. The admitted
claim is that generated C and the explicit binary32 reference stay within the
registered exact-intent value bound. It does not include branch identity,
signed-zero bit identity, a functional consumer, a wrapper or continuous
operation. The [original result](../results.json), [registration](../../registration.json),
generated C, numerical budget and held-out policy are unchanged.

## Review provenance and verification

The original Claude AI technical report remains in the external audit at
`implementation/claude-review-20261012/control-output/REPORT.md`. Its SHA-256,
the reviewer-script hashes, saved output hashes and the recount are in
[compiler-comparison.json](compiler-comparison.json). The report identifies
Claude Opus 5.5 (`claude-opus-5-5`), Claude Code 2.1.296 and session
`ddf3cb92-2db2-4e61-a343-997ae4d2e9b3`. It reviewed technical commit
`64b8887ff84d4625d2369737dbbd1aae8710ca47`; that commit has the same
technical source and evidence as main before this PR. The reviewer had read
the expected outcomes and had earlier found one reverse slew flip, so the
review was not blind. Its exact-fraction model, rounding routine and native
harness were separately written computations. Same-model helper sessions do
not supply independent authorship or external peer review.

I checked the report and scripts against the pinned [specification](../../spec.json),
[source](../../generated/zero_reset.c), [other variant](../../generated/tracking_reset.c)
and [runner](../../qualify.py). The generated-source hashes match the reviewer
copy. I rebuilt its strict harness and reconciled its reverse cases and zero
grid with the repository reference. The portable [focused replay](../../campaign/review_cases.py)
compiles the repository's unchanged generated C with the registered strict
flags, uses an independently written rational increment calculation for the
reverse cases, and compares the original binary32 reference and C by bits.
Its [output](reproduced.json) records the inputs, observed states and flags,
source hashes, host compiler and warning failure. With the pinned
`requirements.txt` installed, reproduce from the repo root:

```sh
python3 campaign/review_cases.py > /tmp/control-review-reproduced.json
python3 review_branch_use.py
git diff --exit-code -- evidence/branch-use.json evidence/branch-use-table.md
```

The verification also ran the review's `sh scripts/build_strict.sh`,
`python3 -I scripts/reconcile.py` and `python3 -I scripts/zero_reconcile.py`
from its external output directory. The zero-grid reconciliation found no
state-bit differences against `core.reference`. Recounting the saved compiler
outputs with `python3 -I scripts/compare_outputs.py` reproduced
[the compact comparison](compiler-comparison.json). These commands use only
development material; the held-out directory was not opened.
The existing branch replay reproduced its retained issue locations without
changing its committed detail or table.

## Findings and disposition

| Finding | Verified disposition |
| :--- | :--- |
| F1 numerical bound | The registered local `32u` bound and nonexpansive state propagation remain the admitted argument under the declared arithmetic assumptions. The report's approximate tighter `3u` estimate was not established as a replacement and is not adopted. The [numerical argument](../../NUMERICS.md#error-bound) is unchanged. |
| F2 original contacts | The [original result](../results.json) and [branch replay](../branch-use.json) retain conservative threshold contacts with matching executed flags. The prior [minimized examples](../observational/independent-review.json) show exact-active to rounded-inactive flags. |
| F3 reverse slew | Record correction resolved: [focused replay](reproduced.json) confirms exact-inactive to rounded/C-active slew flags in both variants and directions. Each input is one step and inside the registered domain. These examples add a missing mechanism; they do not change the earlier campaign denominators. The report's universal claim that reverse clamp flips are impossible is unestablished by its finite search and informal bound, so no such exclusion is admitted. |
| F4 signed zero | Record correction resolved: [focused replay](reproduced.json) confirms hold from negative zero, tracking reset from negative-zero input, and an update whose binary32 increment underflows to negative zero. In these strict builds, the reference returns negative zero and C returns positive zero with matching flags. The update's exact-rational value is a tiny negative nonzero value, so this case is a representation and rounding observation, not exact zero. The select-sum lowering explains the observed strict-build sign loss. No sign contract was adopted. |
| F5 compiler scope | The saved [compiler-output recount](compiler-comparison.json) supports value and flag agreement only on those exercised one-step cases and builds. The Clang relaxed-flag difference is zero sign. The review's Cortex-M7 assembly was compile-only; no Cortex-M execution, pinned PX4-toolchain qualification or task FPSCR observation occurred. The PX4-like arithmetic comparison builds omitted the blocking warning flags to compile; the strict builds retained their registered flags. |
| F6 warning blocker | Unresolved for integration: [local Clang syntax compilation](reproduced.json) with `-Wfloat-equal -Werror` fails on the generated zero-dt equality tests in both variants. The copied pinned PX4 CMake source requests these warnings. This is a reproduced compile blocker, not an executed PX4 build or a numerical error. No exemption or wrapper design was selected. |
| F7 horizon and input boundary | Wording correction resolved: the [specification](../../spec.json) limits each trace to 256 steps. The [runner](../../qualify.py) enforces trace length and restarts its error accumulator on a reset within a trace. The review's phrase “256 steps since last reset” is not the registration and is not adopted. Bare C assumes admitted inputs. |
| F8 evidence labeling | The original stopped pilot and separately registered observational continuation retain their distinct criteria and results. Deterministic builds, ticks and compiler reruns are not independent generated implementations. |
| F9 wrapper boundary | Unresolved: consumer behavior for state, mode, anti-windup, logging and signed zero remains unknown. Message timing, missing/reordered inputs, reset triggering and continuous operation need separate requirements and qualification. |

The review's diagnostic-only flags and unspecified-zero interface is a
proposal, not an owner-approved contract. Human review is deferred for this
scoped Claude AI technical admission and is not an additional gate here.
The next gate is the actual consumer contract and a justified response to the
warning-set compile blocker before wrapper qualification.
