# Claude AI technical review and disposition

The pinned [report](report.md) is the complete reviewer text. Its SHA-256 is
`a948b33a9ae4b9bd6f3ebeebc81f6f1eb41b3cc49e2d26dfc53648e58b295dcf`.
The original CLI JSON is retained outside the repository at
`implementation/active-20261014/review/claude-output.json` with SHA-256
`4f162718d1f1840910b6ddb0e14486b7573ba5156d0e9e1b3ce69aeb68c29be4`.
The CLI metadata identifies model `claude-opus-5-5`, Claude Code 2.1.299,
and session `97c3e385-5884-4fb3-940c-b83cdbf26cea`. The reviewer text said
it could not see its session ID; the ID here comes from the CLI JSON, not the
reviewer's self-report. Reviewed commit: `7ea09b9869288299e724271e33c25ba940f58087`.
The prompt disclosed the expected counterexample and listed the files; the
review was non-blind. The reviewer read files and derived the tie calculation
by hand. It did not execute code, rebuild, independently author the original
cases or inspect the pinned PX4 target. This is Claude AI technical review,
not human or external peer review, and it does not admit the active variant.
The exact prompt is retained with the raw JSON externally.

| Finding | Verified disposition |
| :--- | :--- |
| F1 quantity wording | The reviewer correctly distinguishes a one-step local error from accumulated state-history divergence. The [adopted consumer contract](../../CONSUMER.md#adopted-development-contract) predates the cases and explicitly requires a propagated bound over a continuous segment and all registered dt/input histories. The [result](../results.json) and [explanation](../README.md) now name that quantity. The registered specification was not edited after exposure. The local one-step ceiling was not claimed to fail. |
| F2 continuous ceiling | The reviewer independently derived the exact and nearest-even recurrences and first crossing. I reproduced these with [closed-form code](../check_counterexample.py) and strict compiled C in [results.json](../results.json). The case is in the registered numerical domain, but below the pinned PX4 rate module's dt clamp. It refutes the declared all-input ceiling; no PX4-reachable-subdomain claim follows. |
| F3 interior branch | Reproduced gap: the originally registered numerical cases took slew or cap branches despite two misleading case names. Two [new development cases](../supplemental-directed.json) were [registered](../registration-supplemental.json) before execution. Both exercised the interior branch, with C/binary32 value and flag agreement. They are counted separately from the original ten. |
| F4 NaN rejection | Reproduced harness defect: the original string check short-circuited the validator. [The runner](../qualify.py) now passes a real NaN into `validate_step` and records rejection. It still does not test a PX4 wrapper or host failsafe behavior. |
| F5 registration scope | The initial registration pinned the specification and directed inputs before any active outcome, as git commit `e735af5` shows. It could not pin code written afterward. The later [result](../results.json) now records oracle and harness hashes. There was no frozen final-case run or claim that development code was preregistered. |
| F6 analytic checker | The checker now derives the first crossing from the ceiling and checks exact and rounded branch/cap conditions at crossing and at the registered endpoint. It is an independent closed-form consistency check of the saved output; the reviewer supplied a separate hand derivation. |
| F7 initializer and wrapper | The numerical [initializer](../boundary.py) copies an in-domain preceding PID setpoint and rejects an out-of-domain one. Entry-tick behavior, bypass, message freshness, publisher separation, diagnostic ULog fields and PID integrator response remain unexecuted wrapper requirements. The failed core gate prevents wrapper admission. |
| F8 target build | The reviewer correctly marked the host LTO archive and pinned PX4 claims unverified by its read-only review. The host build was executed locally, but a pinned `fmu-v6c` compile/link and target arithmetic check remain unavailable. The current full checkout is at another commit, `arm-none-eabi-gcc` is absent, and the Docker daemon is unavailable. |

The scientific failure remains after the review corrections. Original shadow
artifacts and all final cases remain untouched. No human-review gate was
restored and no active wrapper was admitted.
