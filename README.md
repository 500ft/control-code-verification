# Control code verification

Compiled CasADi C and the binary32 reference agree on the frozen development
traces for the stateful angular-rate filter. The exact-rational intent checks
pass within the derived numerical bounds. Branch-near cases remain requirement
issues, so integration is unqualified. Counts, errors, build identity and case
locations have one result home: [evidence/results.json](evidence/results.json).

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

## Figure

![Four panels. Top: on the reversal trace, compiled C lies on exact intent for both reset variants, with crosses where the state reaches the rate clamp. Bottom: on the constant-input trace, compiled C error stays far below the analytical bound for both variants](evidence/core-qualification.png)

Panels a and b show the reversal trace. Blue compiled C with dots lies on the
dashed orange exact intent. Red crosses mark steps where the state reaches the
rate clamp. Their uncertainty interval touches the branch threshold, so the
branch requirement stays open. All implementations took the same branch at
these steps. Panels c and d show the constant-input trace on a log scale. Blue
is the compiled C error against exact intent. The grey dashed line is the
deterministic bound from [NUMERICS.md](NUMERICS.md). Each row shares its y-axis
across the two variants. Step counts, dt and inputs are printed in the figure.
The selected reversal and constant-input traces remain unchanged.

[Download SVG](evidence/core-qualification.svg) · [Full trace CSV](evidence/traces.csv) ·
[Figure inputs, output hashes and Matplotlib version](evidence/figure.json).
Regenerate only the figure with `python3 plot.py` in an environment with
Matplotlib. No qualification runner or withheld cases are read. The Matplotlib
version in the manifest reproduces the committed PNG and SVG bytes.
[figure_style.py](figure_style.py) holds the shared text sizes, colours and file
settings. The owner asked for this figure-rules pass on 2026-10-09. It builds on
the restyle from the owner's enclosure scientific reference at commit
`bad572fc0902437445a5446bb5bc43098cc6211f`. Numerical values and bounds are unchanged.

## Scope and provenance

This is the owner's authorized software pivot from
[500ft/px4-failsafe-differential-testing](https://github.com/500ft/px4-failsafe-differential-testing),
following the v2 plan and objections review.
The old project's PR #50, typed parameter transport and SITL harness are useful
future integration sources. Their implemented boundaries must be checked
before reuse; no harness is copied as a setup prerequisite.
Study A remains unfinished and paused in the original repository. Existing
failsafe results do not qualify this module.

The local filter boundary includes explicit state, reset and dt. A second
reviewer and branch requirements remain pending before a reviewed wrapper.
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
