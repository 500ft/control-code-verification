# Roadmap

## Finish line

Qualify a stateful control-prototype module against independent requirements
and a strong B2B baseline, then qualify a reviewed integration wrapper. Size a
small generated-port pilot only after those gates. Generation and verification
are separate factors. This staging task does not authorize a public repository.

## Current step

Core numerical comparisons and analytic checks executed; see the
[result](evidence/results.json). Branch uncertainty touches functional
thresholds. Resolve branch-use requirements with the second reviewer before
qualifying integration. Public successor naming also awaits the owner.

## Remaining gates

- Review the branch requirement issues and any wrapper's admission, reset,
  state initialization, stale/absent/reordered-message and timestamp semantics.
- Qualify the reviewed wrapper on frozen message traces. Keep final cases
  withheld until implementation and requirements are frozen for final review.
- Attempt PX4 replay only after full topic, publisher, timestamp and pinned-build
  qualification, including a known-good repeat. Recorded-rate replay cannot
  establish hardware deadlines. Keep the core result if this gate cannot pass.
- Size a pilot from independent ports and module variation. Do not treat
  deterministic reruns or time samples as additional ports.

The old failsafe study stays paused pending an explicit release or closure
choice. No new decision is inferred about hardware, funding or physical tests.
