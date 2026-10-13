# Bounce-action fidelity in the halved-margin coil field

**The better field reproduces the target's bounce action more closely, but the wide
diagnostic is still incomplete.** In the coil set with the lowest boundary error
under [acceptance v2](../validation/ACCEPTANCE_V2.md), the narrow action-variance
score is 27% lower than in the #35 reference fit, and 8 fewer launch lines fail. The
innermost surface still has no required well on any line. Recorded 13 October 2026
for [issue #89](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/89);
exploratory, not physical acceptance.

## Question and method

Does the halved-margin coil set ([#70 arm M](ISSUE70_CONSTRUCTION_MARGINS.md),
reference401, snapshot SHA-256 `4eab51eb…`) complete the Step 3 diagnostic where the
[#35 reference fit](ISSUE25_MATCHED_TARGETS.md) could not? As preregistered in #89,
`scripts/measure_coil_bounce.py` ran with the defaults #35 used (801 toroidal
samples, 16 field-line labels, two field periods, 600 s budget, one thread) on main
`44beb11` with the archived reference401 Wout. Field lines start at target
coordinates; #70's direct tracing (10 lines, 200 transits, all confined) serves as
the surface check. Failed launch lines were counted with the registered rule (exactly
two complete wells per line at q = 0.03); the same count reproduces #35's 32.

## Result

| Diagnostic | Ideal target | #35 reference fit | #70 arm M |
| --- | ---: | ---: | ---: |
| Narrow action-variance score | 1.157e-5 | 4.255e-5 | **3.086e-5** |
| Wide action-variance score | 2.382e-4 | incomplete | incomplete |
| Surface score s = 0.5 / 0.75 / 0.9 | 3.4 / 2.1 / 2.1e-4 | 37 / 22 / 20e-4 | 18 / 14 / 15e-4 |
| Failed launch lines, s = 0.1 / 0.25 | 0 / 0 | 16 / 16 | 16 / 8 |
| Lowest B on any s = 0.1 line (well threshold 1.02566) | — | 1.02938 | 1.02652 |

The run completed in 9 s at frozen current 307,521.9 A; the coil-to-target mapping
checks agree to 6e-16 in position.

## Reading and recommendation

- The arm M field is closer to the target on every surface, but outer-surface
  scores remain 5–7× the ideal, and at s = 0.1 the field minimum along every line
  stays 0.0009 above the q = 0.03 well threshold. The wide domain fails for the
  same reason as in #35, with a smaller margin.
- **Do not run a matched halved-margin fit of the improved target yet.** It could
  not resolve benefit transfer while the wide domain fails at s = 0.1, and target
  launch labels are not realized flux labels (#48 shows they drift). Qualify
  realized-field labels and the shallow-well behaviour first
  ([programme](STEP4_RESEARCH_PROGRAMME.md), step 3); revisit when a coil set
  completes the wide domain.

**Update (same day):** on the improved target, the interior-weighted continuation's
field completes the wide domain ([Step 3 record](STEP3_V2_METHODS.md)).

Limits: one coil set, vacuum field, target-coordinate launch labels, one resolution.
Raw outputs: maintainer's ignored `artifacts/issue89-bounce-armM/`.
