# Technical review of commit 7ea09b9: active symmetric qualification

**Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`). I can't see a session ID. This was a non-blind review: I was told the expected finding beforehand. It is an AI review, not a human or independent one, and it does not admit anything.

**How I checked:** I only read files. I ran nothing, did not rebuild, did not compute hashes and did not use git. Each claim below is labelled:
- **[S]** read directly in the source
- **[C]** my own exact calculation by hand
- **[U]** not verified (target, PX4, hashes or ordering claims)

---

## 1. Independent derivation (positive tie case; the negative case is a mirror)

**Inputs and domain [C]:**
- x₀ = 1, u = 8, h = 513·2⁻²⁵.
- All three are exactly binary32.
- h ≥ dt_min = 512·2⁻²⁵, and h ≤ 1/16.
- |u| = 8 is within the inclusive limit (`active/boundary.py:24`).
- Note that h sits one part above dt_min. At exactly dt_min, 2h would be exactly 256 ulps and there would be no tie.

**C recurrence [S, C]**, from `active/generated/active_symmetric.c:66-99`:
- `a07 = 0.25f + h` is exact: (2²³ + 513)·2⁻²⁵, which needs 24 bits.
- alpha = RN(513/8389121) ≈ 6.115e-5.
- RN(8 − x) is in [6.25, 7].
- delta ≈ 3.8e-4 to 4.3e-4, which is much larger than `a12 = 2h = 513·2⁻²⁴ ≈ 3.058e-5`. That value is exact.
- So the strict test `a12 < a07` (line 78) is true and `a07 < a09` (line 74) is false.
- The increment is 2h + 0. The if-else sum adds an exact zero, so it changes nothing.

**State addition [C]:**
- Write x = M·2⁻²³ with M even, x in [1, 2).
- Then x + 2h = (M + 256.5)·2⁻²³. That is a tie, and ties-to-even gives M + 256, which is still even.
- So the C state after n steps is 1 + n/32768 for as long as x < 2.
- At n = 24576 the state is 1.75, so it stays in the binade and the cap test at lines 86–90 never fires.
- C flags are [1, 0].

**Exact intent [S `core.py:28-33`, C]:**
- The slew branch is active exactly when 8 − x > 2(τ + h) = 0.5 + 2h.
- The exact state goes up to 1 + 24576·513/2²⁴ = 3587/2048 ≈ 1.7515, so the condition holds throughout.
- Exact state after n steps: 1 + 513n/2²⁴.
- Error after n steps: n/2²⁴.

**First crossing [C]:**
- ceiling × 2²⁴ = 0.001065 × 16777216 ≈ 17867.74, so the least n with n/2²⁴ > ceiling is **n = 17868**.
- Error at n = 17868: 17868/2²⁴ = **4467/4194304**.
- Exact state: **6485875/4194304**.
- C state: 1.5452880859375 = 0x3FC5CC00, which matches the little-endian hex `00ccc53f`.
- Elapsed time: 2291571/8388608 s ≈ 0.2732 s.
- At n = 12288 and n = 24576 the errors are 3/4096 and 3/2048.

All of these match `active/results.json:196-287`.

**Negative case [C]:** Ties-to-even is symmetric in sign. The `a09 = -2h` branch (lines 72–75) gives −1 − n/32768.

**The arithmetic claims hold. The disputes below are about what was measured and what it is claimed to prove.**

---

## 2. Findings

### F1. The measured quantity doesn't clearly match "next-state error" — **Material; needs clarification under a new registration**

- `active/spec.json:16` defines the quantity as "absolute numerical **next-state** error against exact intent".
- `active/qualify.py:92-100` instead runs two separate open-loop chains: an exact chain from x₀ and a C chain. It measures how far apart they drift over time.
- If the term means one-step (local) error, i.e. exact intent applied to the current C state, the per-step error here is 0.5 ulp = 2⁻²⁴ ≈ 6e-8 [C]. **On that reading nothing is refuted.**
- The original `spec.json:12` lists "isolated-step B2B" and "stateful B2B" separately, which makes the ambiguity real.
- The `duration_s` and `reset_policy` fields point toward the cumulative reading, which is how the implementer read it.

**Disposition:** The refutation is valid only under the accumulated-trajectory reading. README lines 9–10 and 26–28, and `results.json:300` (`universal_ceiling_refuted`), should name that quantity explicitly. Fix the definition in a new registration, not by editing the registered spec.

### F2. Under the cumulative reading, a short prefix does refute a pointwise 30-minute ceiling — **Assertion upheld, with two qualifications**

- The prefix starts the segment at x₀ = 1. That is an admissible initializer value (`boundary.py:13`, |x| ≤ 2). It needs no reset, and every input stays in the domain at every step [C].
- So a segment that is exceeded at t ≈ 0.273 s fails a ceiling that must hold at every point of an 1800 s run.

Two qualifications:
- **(a)** It must be a *prefix*. Placed mid-segment, the exact and C states would already differ, and the tie parity is no longer guaranteed. The README wording ("contain this prefix") is correct but easy to over-read.
- **(b)** It needs a constant dt ≈ 15.3 µs (about 65 kHz) for 17,868 steps. That is inside the registered domain but far above realistic PX4 rate-loop frequencies [U]. The refutation is of the spec over its declared domain. It says nothing about realistic operation.

### F3. The C/reference agreement never exercised the backward-Euler interior branch — **Evidence gap**

- C and reference were compared bitwise every step (`qualify.py:93-96`), each from its own state. The 0 mismatches are real for the calls that ran [S].
- But in every numerical case, slew or cap decides the state [C]:
  - "unslewed": delta = 1/129 > 2h = 1/256.
  - cap cases: 1/17·6 > 1/32.
  - tie cases: shown in §1.
- So the state output only ever exercised `x + (±2h)` and the clamp. The `a13 = a07` interior path (lines 80–81) and alpha's rounding never reached the state. They only affected the flag comparisons.
- The README (lines 15–17) admits the "unslewed" names are wrong. But "agreed on every executed directed call" (lines 12–14) should be scoped: **interior-branch agreement is not shown.**

### F4. The NaN reject case is true by construction — **Defect (test harness)**

- `qualify.py:80` has `rejected = u == 'NaN' or not valid(...)`. The string comparison short-circuits, so `validate_step` is never called with NaN.
- `invalid_command` (`directed.json:13`) therefore proves nothing about how `boundary.py:21` handles non-finite values.
- Separately, "do not call numerical core" is not instrumented for either reject case.

**Disposition:** Call `validate_step(0.0, float('nan'), ...)` directly.

### F5. The registration pins only two files — **Evidence gap**

- `registration.json:4-7` hashes `spec.json` and `directed.json` only.
- `core.py` (the oracle), `boundary.py`, `generate.py`, `qualify.py` and the generated C are not pinned at registration time.
- `results.json` records the C source and `.so` hashes after the fact. It does not hash the oracle or the harness.
- The claim that the files were registered at e735af5 before generation (README lines 3–5) is [U]. I could not check git history.

### F6. `check_counterexample.py` restates the mechanism rather than checking it — **Minor**

- Line 15 reads `n` from `results.json` rather than deriving it. Line 25 does then confirm minimality, so this is acceptable.
- Line 19 encodes "256 ulps every step" as an assumption. It does not check the parity/tie step by step.
- Line 21 checks only the exact-side slew condition, and only at step n. It never checks the C-side branch condition (`a12 < a07`).
- Line 28 asserts the error at step 24576 without re-checking the slew and cap conditions at that step.
- All of these hold by my calculation in §1, so the conclusion stands. But calling the script "independent" (line 1, README line 19) overstates it: it is a closed-form consistency check that depends on `results.json`.

### F7. The initializer cases check only acceptance — **Minor**

- `qualify.py:76` compares only accept/reject.
- "no update on entry tick" and "bypass active" (`directed.json:5-6`) are not exercised, because no wrapper exists. The output is recorded, though: 7/4 [S].

### F8. Target, LTO and PX4 claims are unverified — **Correctly disclaimed**

- The CMake archive hash, the ThinLTO bitcode, and the PX4 source-path descriptions (README lines 43–66) are all [U].
- ThinLTO bitcode means the final arithmetic is decided at link time. The `.so` that was qualified (`-O2`, no LTO) is not the archive artifact.
- The README already says this is unqualified (lines 50–51, 66–69), and `results.json:301` says the same.

---

## 3. Summary

| Item | Disposition |
|---|---|
| First crossing at n = 17868, all reported values, symmetry | Confirmed [C] |
| Input/state domain and branch conditions on the prefix | Confirmed [C] |
| Refutation of a pointwise 30-minute ceiling | Upheld only under the cumulative-drift reading (F1, F2) |
| C/reference agreement | Exercised and 0 mismatches, but the interior branch is untested (F3) |
| NaN reject | Defect (F4) |
| Registration scope | Gap (F5) |
| Counterexample checker | Minor (F6) |
| Target / PX4 | Unverified, correctly disclaimed (F8) |

No files were edited and no cases or campaigns were run.
