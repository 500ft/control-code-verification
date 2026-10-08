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

## Figure

![Executed filter trajectories and numerical errors for both semantic variants](evidence/core-qualification.png)

The panels use shared rate and log-error scales across variants. Circles identify
compiled output and absolute state error; dashed purple lines show exact intent
or the analytical bound. Crosses mark threshold uncertainty, not observed branch
failures. Bounds are deterministic and are not confidence intervals. The selected
reversal and constant-input traces remain unchanged.

[Download SVG](evidence/core-qualification.svg) · [Full trace CSV](evidence/traces.csv) ·
[Figure inputs, output hashes and Matplotlib version](evidence/figure.json).
Regenerate only the figure with `python3 plot.py` in an environment with
Matplotlib. No qualification runner or withheld cases are read. This restyling
uses the owner's enclosure scientific reference at commit
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
