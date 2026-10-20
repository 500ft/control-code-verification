# Scoped Claude AI technical review: persistent binary64 active core

**This is not a human or external peer review.**

| Item | Value |
|---|---|
| Reviewer | Claude Opus 5.5 (`claude-opus-5-5`), Claude Agent SDK session. Session ID not known. |
| Reviewed SHA | `797bb9d6beb09de94ff0a7ed299eaa3d01fb9d43`, branch `development/active-binary64-20261019`. The session snapshot showed HEAD at `797bb9d` with a clean tree. I did not check this or the registration hashes with git. |
| Tools used | Read, Glob and Grep only. I ran no Bash, compiler, Python or binary, and changed no files. I opened no reserved or final cases and did not read `active/review/report.md`. |
| Prior exposure | Non-blind. Before this session I had no exposure to the repo. During it I read the author's claims, both prior binary32 failure summaries and the reported results before forming my conclusions. |
| Evidence labels | **[D]** I derived it by hand (not executed). **[I]** I checked it by reading the code. **[C]** It is the author's claim and I have not verified it. |

## 1. Checks I derived myself (all unexecuted)

**D1. The exact map never increases the distance between two states, including at branch changes. [D] Confirmed.**
- Write α = h/(τ+h) and g(x) = x + clip(α(u−x), −2h, 2h).
- The inner clip changes with x at a rate of −α or 0. So g changes at a rate of 1−α = τ/(τ+h) on the lag branch and 1 on a slew branch.
- g is continuous, piecewise linear and non-decreasing, with every rate in (0,1]. That means g can never move two states further apart (it is 1-Lipschitz).
- The outer clip to [−2, 2] is also 1-Lipschitz, so F = clip∘g is too.
- This matches `core.py:28-33`, because max(x−2h, min(x+2h, target)) = x + clip(target−x, ±2h).

**D2. Per-step rounding error, in the order the code does the operations (`generated/…state.c:30-43`). [D] Confirmed, and the stated bound is conservative.**
- **Error per operation:** with U = 2⁻⁵³ and A = 2⁻¹⁰⁷⁵, one nearest-even binary64 operation is off by at most max(U·|z|, A) ≤ U·|z| + A. A covers subnormal results (half of 2⁻¹⁰⁷⁴). Overflow cannot happen on this domain.
- **`d = 0.25 + h` is exact.** h is binary32 and at least 2⁻¹⁶, so its last bit is at least 2⁻³⁹. The sum is below 1/2, so its binary64 spacing is 2⁻⁵⁴. The sum therefore fits exactly, E_d = 0, and the proof's E_d = (5/16)U + A is a safe overestimate.
- **Quotient `a = h/d`:** the exact α is at most 1/5. Following the proof's own steps: 2·E_d + (1/2)U + A = (9/8)U + 3A. ✓
- **Product `delta = a·v`:** â·v̂ − α·v = v̂(â−α) + α(v̂−v). With |v̂| < 11 and α ≤ 1/4, the error is at most 11·E_a + (1/4)·E_v + (11/2)U + A. That gives (99/8 + 5/2 + 11/2)U = 20.375U ≤ 21U, and 34.25A ≤ 35A. ✓
- **`lo` and `hi`:** ±2h is exact (doubling a binary32 value in binary64). Clipping to an exact interval cannot enlarge an error.
- **`r = x + q`:** |x + q| ≤ 17/8, so this adds (17/8)U + A.
- **Total:** at most 23.125U + 36A ≤ 24U + 36A. ✓
- **Why the errors simply add:** compare the computed step from the computed state with the exact step from the exact state. The difference is at most (rounding of one step from the computed state) + (distance between the two states). The second term does not grow, by D1. This needs the computed state to stay in [−2, 2], which the final cap guarantees.

**D3. Update count and margin. [D]**
- 1800 × 65536 = 117,964,800 positive updates. ✓
- Accumulated state error: N·24U = 2,831,155,200 / 2⁵³ ≈ 3.1432e-7. The 36A term adds only about 1e-316.
- Converting to binary32 for publication adds at most 2⁻²⁴ ≈ 5.960e-8. That is half a binary32 unit on [1, 2]; subnormal outputs round by at most 2⁻¹⁵⁰.
- Whole-output bound ≈ 3.739e-7 rad/s, about **2848× below** the 0.001065 ceiling.
- The bound stays under the ceiling for any N up to about (0.001065 − 2⁻²⁴)/(24U) ≈ **3.997e11 updates**. So the count argument does not depend on whether the 1800 s means the sum of dt values or wall-clock time.

**D4. The retained binary32 failures cannot recur in this core. [D]**
- In the tie case and the PX4 125/126 µs case, every slew increment 2h is a multiple of at least 2⁻³⁶, and the states stay below 2.
- So each binary64 sum fits in 37 bits or fewer and is exact. The state error should be exactly 0.
- The tie case should show a publication error of exactly 2⁻²⁴, because the half-unit tie reappears when converting to binary32.
- Both match the claims in `results.json:57-58,69-70` **[C]**.

**D5. The horizon case accumulates no rounding at all. [D]**
- With x₀ = 5/4, u = ±8 and h = 2⁻¹⁶, every step is on a slew branch, and x ± 2⁻¹⁵ is exact.
- So the final state is 5/4, and the checksum is 2 × 117,964,800 = 235,929,600 (the flag values +3 and +1 alternate).
- This checks the count, flags and termination. It does not test error accumulation.

## 2. Findings

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| **B64-01** | Info / confirmed | The proof in `PROOF.md` holds for the emitted operation order, under strict binary64 nearest-even with gradual underflow (D1–D3). | No change needed. Optionally note in `PROOF.md` that `d` is exact and that the margin covers N ≤ about 4.0e11. |
| **B64-02** | Medium (wrapper contract) | **Re-initializing from the core's own published output feeds binary32 rounding back into the state.** `active_double_init` only takes a `float`. If the core is active and the "preceding effective setpoint" is its own published value, each re-entry adds up to 2⁻²⁴. About 17,868 such events would exceed the ceiling (0.001065 × 2²⁴ ≈ 17,867.7). That is the same mechanism and threshold as the prior binary32 failure. Section 6 of `CONSUMER.md` assumes no resets, but nothing yet forces every init to be logged as a reset that ends the continuous segment. | Add a registered wrapper requirement: every init is a logged reset that ends the segment, and a test shows no init happens while active without a real mode or axis transition. Do not treat this as a core defect. |
| **B64-03** | Minor | **A failed init leaves the core runnable on stale state** (`state.c:6`). On rejection, `initialized` and `x` are untouched; the `init_beyond_cap_rejected` control (`run.py:102`) even asserts this. A wrapper that ignores the −1 return would keep stepping from the previous segment's state, against `CONSUMER.md:107` ("bypass"). | Either clear `initialized` on failure in a separately registered successor variant, or add a wrapper test that a rejected entry never calls step. |
| **B64-04** | Minor | **A rejected call returns `published = 0.0f`** (`state.c:19-22`). Using it would cause a jump to 0 rad/s instead of the "hold last finite" behavior in `CONSUMER.md:109`. | Wrapper must ignore `published` when `status == -1`. Register a test for this. |
| **B64-05** | Minor | **`reset` sets `initialized = 1`** (`state.c:14`). After disarm the core will step from 0 without an entry init. This may be intended, but whether disarm or entry comes first is the wrapper's call. | Add a wrapper ordering test. |
| **B64-06** | Minor | **Horizon evidence is weaker than labeled.** `elapsed_s` is hard-coded in `printf` (`horizon.c:17`), so the check `elapsed_s == 1800` at `run.py:119` can never fail. The path is also exact (D5). | Compute elapsed time exactly from steps × dt, and label the case as a count/flag/throughput check only. The README already says it is not the universal argument. |
| **B64-07** | Minor | **The `published_output_not_state` control cannot fail** (`run.py:110-112`). ctypes returns a copy of the struct. **[I]** By inspection, `state->x` is written only at `state.c:7`, `:14` and `:43`, and `published` is never read back. So the claim holds structurally, but not because of this test. | Relabel the control and cite the structural check. |
| **B64-08** | Minor | **Gaps in directed-case coverage.** Nonzero state error was compared against exact intent on only 3 + 3 + 64 steps. Never exercised: subnormal states (reachable: with u = 0 and h = 1/16 the state shrinks by 0.8 per step and reaches subnormals after about 3,300 steps), Inf, negative or −0.0 dt, init at exactly −2, and NaN init. | Not needed for the math, since the bound comes from the proof. Optionally add these as separately registered development cases. |
| **B64-09** | Medium (target) | **Target arithmetic evidence is compile/link-only and an excerpt** (`target-build.json:55-62`). It lists 6 f64 instructions. It does not show the absence of fused instructions (`vfma/vfms/vfnma/vfnms.f64`), the `vcvt.f32.f64` publication, or the comparisons. It comes from a `-nostartfiles -e main` probe, not the PX4 archive object or firmware. **[I]** The compile command applies the strict overrides after the PX4 flags (contract off, reciprocal off, trapping on, signed zeros on, `-O2` after `-Os`), with no `-ffinite-math-only` or `-fsingle-precision-constant`. | Record a full `objdump` of `active_double_step` from the archive object, with a negative grep for fused operations. Firmware link and LTO stay open until the core is linked into firmware. |
| **B64-10** | Minor (runtime, not verified) | **FPU runtime state on NuttX/STM32H7 is not established:** the FPSCR rounding mode, flush-to-zero (FZ) and default-NaN bits, and double-register context saving. **[D]** Effect on the ceiling is small. Flush-to-zero adds at most about 2⁻¹⁰²² per operation. Directed rounding at most doubles the per-step bound to about 48U, so the total would be about 6.3e-7 + 1.2e-7 rad/s, still far below the ceiling. Effects on other claims: bit-identity with the host would be lost, and under FZ a subnormal binary32 dt would be treated as 0 and take the hold path (status 1) instead of being rejected. | Add an FPSCR read to the target/wrapper qualification, or cite the pinned NuttX source. Treat target bit-identity as not claimed, as in `CONSUMER.md:111`. |
| **B64-11** | Info | `effective_flag_order` leaves out `-fno-trapping-math`/`-ftrapping-math`, `-fno-math-errno` and `-Os`/`-O2`. The command itself looks correct when I read it. | Extend the recorded list. |
| **B64-12** | Info | `reference.py` repeats the C operation order. Agreement between them shows the host compiler is faithful, not that the specification is right. The independent check is the comparison against exact rational intent. | Wording only. |
| **B64-13** | Info | "Exact intent" uses the binary32-quantized dt (including PX4's `1e-6f` product and its [0.000125, 0.02] clamp), not physical time. Timing quantization is outside this claim. | State this explicitly in `PROOF.md`/README. |

I found no counterexample to the numerical bound across branch changes, initialization, reset/hold, invalid calls (rejected before arithmetic, state unchanged **[I]**), double-state persistence, type promotion (**[I]** every float→double conversion is explicit and exact, and the comparisons stay float), or output feedback inside the core.

## 3. Admission recommendation

**Admit the numerical core**, meaning the generated C read as a strict IEEE binary64 nearest-even program, under its declared domain and arithmetic assumptions. There are no blocking findings. The bound is mathematically conditional on IEEE behavior, and the ceiling has about 2800× margin. That margin also covers modest departures from the assumptions (D3, B64-10).

This does **not** admit the target build, any firmware, or the wrapper. B64-02 through B64-05 must become registered wrapper requirements, and B64-09 and B64-10 must be resolved in target qualification.

## 4. Still unverified

- **What I did not execute:** none of `run.py`, `proof.py`, `horizon.c` or the CMake builds ran in this review. All numbers in `results.json` and `target-build.json` remain author claims (registration and binary hashes, case errors, controls, toolchain identity, disassembly).
- **History and identity:** that `f5bf59a` registered the spec, proof and cases before generation (not checked in git), and that the working tree matches `797bb9d` byte for byte.
- **Target build:** the full target disassembly (absence of fused operations, the publication conversion), firmware link, LTO in the firmware link, and the FPSCR state and FP context saving at runtime.
- **Not run on hardware:** any Cortex-M execution, CPU timing, or hardware behavior.
- **All wrapper behavior:** publisher separation, freshness, the invalid-input classes, ignored-axis bypass, bumpless re-entry, disarm/entry ordering, logging, and PID integrator response.
