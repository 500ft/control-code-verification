# Control code verification

The separately registered symmetric active variant failed the adopted
continuous numerical ceiling on a directed development case. The
[executed result and independent calculation](active/README.md) identify the
rounding mechanism. This blocks active wrapper admission; the original shadow
artifacts and their bounded numerical admission remain unchanged.
The separate [PX4 timestamp-domain development analysis](active/px4_domain/README.md)
also found a ceiling counterexample with source-permitted integer-microsecond
timestamp gaps. Its pinned target build and the wrapper remain unqualified.
The separately registered [persistent binary64 development variant](active/binary64/README.md)
has a prospective whole-output arithmetic bound under strict rounding and
passed directed host comparisons. Its scoped Claude AI technical review and
PX4 wrapper qualification remain open.

The numerical next-state-value claim is admitted for the declared domain,
strict arithmetic and registered trace horizon after [Claude AI technical
review reconciliation](evidence/review/README.md). Compiled CasADi C and the
binary32 reference agree on the original frozen development traces for the
stateful angular-rate filter; exact-rational intent checks pass within the
registered bounds. The
[executed branch-use review](BRANCH_USE.md) explains all nine flagged steps as
threshold ties with no observed flag disagreement. The functional consumer is chosen and
[source-traced](CONSUMER.md). The [development contract](CONSUMER.md#adopted-development-contract) is adopted;
the new variant's continuous ceiling failed, and pinned PX4 build and wrapper
checks have not run. A [host build-only probe](evidence/consumer-build/README.md)
demonstrates the selected isolated-library compiler approach, but does not
qualify target execution or integration. The
original corpus summary remains in [evidence/results.json](evidence/results.json).

The adopted question asks which defects remain after a costed B2B baseline at
numerical, stateful and integration boundaries, and which additional checks
reduce them. This development result starts that work. Source is published at
[500ft/control-code-verification](https://github.com/500ft/control-code-verification).
The existing staging name was used under the owner's delegated implementation
instruction; it was not a separate naming decision. The
[dependency roadmap](ROADMAP.md) separates completed numerical work, current requirement review and conditional
wrapper/corpus/pilot/confirmation work. It contains no execution schedule.

[Specification and bounds](NUMERICS.md) · [Roadmap](ROADMAP.md) ·
[Frozen registration](registration.json) · [Parameters and units](spec.json)

## Reproduce

Use Python 3.13.7 with the pinned [dependencies](requirements.txt) and Clang.
The retained result records its original macOS environment. Reproduce in a separate checkout so the retained evidence
is not overwritten. For example, create an empty sibling worktree with
`git worktree add --detach ../control-core-reproduction HEAD`, then from that
worktree:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python generate.py
.venv/bin/python qualify.py
```

`generate.py` is the generation factor. `qualify.py` compiles its artifacts,
checks compiler IR, executes independent analytic limits and compares isolated
steps and stateful sequences. The exact intent, binary32 reference and C all
consume the same frozen inputs. The verification timer includes compilation
and checks; it is one execution cost, not a latency distribution or fair
comparison against another method. No LLM port campaign ran.

The runner writes the result and [trace table](evidence/traces.csv). Build
products and IR remain in ignored `build/`. Final cases remain in ignored
`withheld/`; only their hash is registered. They were frozen before the first
implementation commit and have not been loaded by the runner. Reproduction
needs only the public development traces. Time samples and repeated runs are
not independent generated ports or confirmatory evidence.

## Hosted reproduction

The [executed hosted run](https://github.com/500ft/control-code-verification/actions/runs/37854170219)
reproduced the retained development result and trace CSV.

The [CI workflow](.github/workflows/qualify.yml) uses Python 3.13.7, the pinned
numerical dependencies and the macOS runner's Clang. It regenerates both C
variants, compiles them, inspects LLVM and executes the registered development
traces. Generated sources and trace CSV must match the retained files exactly;
all scientific result fields, source hashes and branch-requirement findings
must match. Compiler/binary identity and elapsed time describe each run and
are retained in its downloadable `development-evidence` artifact.

CI runs on pushes and pull requests. It uses no repository secrets or private
inputs. A green result reproduces numerical development agreement; it does not
resolve branch-sensitive requirements or qualify integration. The original
[evidence/results.json](evidence/results.json) remains unchanged.

## Supplemental development observation

The [observational continuation](evidence/observational/README.md) completed
1,572,864 randomized development steps with exact-reference coverage and no
numerical-bound violations. It recorded exact-versus-rounded branch differences;
the supplemental pilot retained the signed-zero mismatch. The
[result table](evidence/observational/table.md) separates steps, traces,
mechanisms and comparison types. Both rounded histories were retained throughout.

The original [first-failure pilot](evidence/development/README.md) remains
unchanged. A separately registered descriptive protocol allowed other traces
to execute without adopting bitwise acceptance or changing controller semantics.
The executable ARM Linux GCC/QEMU comparison also completed on the original
registered corpus, with the known zero-sign diagnostic reported separately.

The completed [Claude AI technical review](evidence/review/README.md) adds
targeted reverse-slew and negative-zero reproducers without changing the
campaign counts or bound. Functional consumer requirements are adopted; the new
variant failed its continuous ceiling and the pinned target build remains
unqualified. Human review is
deferred for this scoped development gate. No reserved cases or integration
campaign ran.

## Branch-use review

[Executed review](BRANCH_USE.md) · [Per-step table](evidence/branch-use-table.md) ·
[Exact intervals, rounding and native outputs](evidence/branch-use.json)

Returned flags currently feed verification only. The underlying clipping
comparisons determine the next state. No wrapper or external flag consumer
has been supplied. The conservative issue markers remain; no functional
contract, numerical bound or final case changed. Reproduce the branch detail
with `python review_branch_use.py` before running the qualification command.
CI checks the detail and retains each execution's compiler/binary identity.

## Figure

![Four panels in black ink. (a) and (b): on the reversal trace the compiled C line with circles lies on the dashed exact intent for the zero-reset and tracking-reset variants, with crosses at the two steps where the state reaches the rate clamp. (c) and (d): on the constant-input trace the compiled C error stays far below the dash-dot analytical bound](figures/core-qualification.png)

Numerical core qualification on the frozen development traces; integration is
unqualified. Panels (a) and (b) show the reversal trace for the zero-reset (time
constant 0.125 s) and tracking-reset (time constant 0.25 s) variants: 256 steps
of dt = 1/32 s, input -8 rad/s, then +8 rad/s from t = 4 s. The dashed line is
the exact rational intent and the solid line with circles is the binary32
compiled C output; the two agree at every step, so the solid line lies on the
dashed one. Crosses mark the 2 steps per variant (t = 2 s and t = 5 s) where the
state reaches the rate clamp of 2 rad/s in magnitude. Their uncertainty interval
touches the branch threshold, so the branch requirement stays open; all
implementations took the same branch at these steps. Panels (c) and (d) show the
constant-input trace, 64 steps of dt = 1/32 s at 0.5 rad/s, on a log scale: the
solid line with circles is the absolute error of compiled C against exact intent
and the dash-dot line is the deterministic worst-case bound from NUMERICS.md.
The error stays at least 324 times (zero-reset) and 897 times (tracking-reset)
below the bound. Both variants use slew limits +4 and -2 rad/s² and the same
rate clamp. Each row shares its y axis across the two variants. Source:
evidence/traces.csv (traces reversal and constant_unsaturated) and spec.json.

[Caption](figures/core-qualification.caption.md) ·
[Download SVG](figures/core-qualification.svg) · [Full trace CSV](evidence/traces.csv) ·
[Figure inputs, output hashes and Matplotlib version](figures/figure.json).
Regenerate only the figure with `python3 plot.py` in an environment with
Matplotlib. No qualification runner or withheld cases are read. The Matplotlib
version in the manifest reproduces the committed PNG and SVG bytes.
[figure_style.py](figure_style.py) holds the shared type, line-style, marker and
file settings and an audit that refuses to save when anything printed touches
anything else; [test_figure.py](test_figure.py) checks the plotted values
against the trace CSV and the caption against this paragraph. The canvas
carries only data, axes, panel letters and one legend; every title, condition
and number moved to the caption under the owner's 2026-10-16 figure-rules
instruction. The 2026-10-09 figure stays frozen at
[evidence/core-qualification.png](evidence/core-qualification.png) with its
manifest [evidence/figure.json](evidence/figure.json); the generator it records
is in git history. Numerical values and bounds are unchanged.

## Scope and provenance

This is the owner's authorized software pivot from
[500ft/px4-failsafe-differential-testing](https://github.com/500ft/px4-failsafe-differential-testing),
following the v2 plan and objections review.
The old project's PR #50, typed parameter transport and SITL harness are useful
future integration sources. Their implemented boundaries must be checked
before reuse; no harness is copied as a setup prerequisite.
Study A remains unfinished and paused in the original repository. Existing
failsafe results do not qualify this module.

The local filter boundary includes explicit state, reset and dt. The numerical
value review is reconciled; diagnostic branch use, zero-sign treatment and consumer requirements are
adopted in CONSUMER.md. Implementation and qualification are next.

PX4 replay additionally needs an actually qualified supported build; the old
failsafe firmware pin is not inherited automatically. It needs every consumed
topic at required rate, timestamp and zero-stamp semantics, initialized state, controlled
publishers and a known-good repeat. No replay, SITL integration, hardware
measurement, release or deployment-readiness claim is made here.

[Source and redistribution records](SOURCES.md) describe the published history,
generated-code notices and dependency boundary. Source publication is separate
from a paper release or integration qualification.

## Prior work and positioning (2026-10-09)

Conrad (2009) describes testing-based translation validation of generated
code under IEC 61508. Stürmer, Weinberg and Conrad (2005) survey safeguarding
techniques for automatically generated code. Both already list, qualitatively,
the checks that should follow back-to-back testing of generated code. This
repository cites both and does not present that check list as new. Entries are
in [references.bib](references.bib).

What this repository adds is counting the defects that survive a costed
back-to-back baseline and pricing each extra check. A study of that kind was
not found in the 2026-10-09 review (abstract-level, web search only, forward
citations not searched). An equivalence study of CasADi-generated C was
likewise not found in the 2026-10-09 review (abstract-level, web search only,
forward citations not searched).
