# The passing coil methods on the improved Step 3 target

**All three methods that pass acceptance v2 on the original target also pass on the
improved Step 3 target; a matched control does not.** The field of @pjckoch's
interior-weighted continuation is the first of seven measured coil fields to complete
the wide bounce diagnostic. Recorded 13 October 2026 for issues
[#92](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/92),
[#93](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/93) and
[#94](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/94); field and
geometry acceptance only, not physical acceptance or benefit transfer.

## Question and method

Three methods produced coil sets that pass [acceptance v2](../validation/ACCEPTANCE_V2.md)
on reference401, the original Goodman plasma: halved construction margins
([#70](ISSUE70_CONSTRUCTION_MARGINS.md)), Fourier order 8
([#53](ISSUE53_COIL_FREEDOM.md), configuration and code by @pjckoch) and the
interior-weighted headroom continuation
([#12](../../submissions/interior-pass-headroom-continuation/README.md), by @pjckoch).
Do they also pass on the improved Step 3 plasma (selected401)? Its only earlier fit
([#35](ISSUE25_MATCHED_TARGETS.md), 300 s search) failed on interior RMS.

As preregistered, every arm used selected401 through the archived Wout
(`8cd6bebf…`) and input (`6bec3483…`), and started from the length-headroom coils
normalized to selected401 (#35's seed, `db836feb…`). All runs were sequential on
the maintainer's machine with one thread:

- **C (control)** and **M (halved margins):** order 5, `scripts/fit_coils.py` on
  main `3f769ce`, 1800 s search and 900 s checks.
- **P (order 8):** the same seed lifted with exact zeros, on the contributor's
  merged `9ecdf27` (current main would stop at the output ceiling, #90); same
  budgets.
- **X (continuation):** `continue_fit.py` at `bf51e3a` with #12's arguments
  (`12 327 100000`), changed only to accept the selected401 input; checked with
  `scripts/check_coils.py --target selected401` on `3f769ce`. First, as an
  environment check, the unchanged reference401 continuation was rerun with the
  archived Wout (`83dc45b9…`; #12 used a Wout the contributor regenerated). Its
  coefficients differ from the committed #12 candidate by at most 0.74 mm (RMS
  0.28 mm), and its verdicts and errors agree (v2 pass, worst ratio 0.929 against
  0.931).

Verdicts come from `scripts/acceptance_v2.py`.

## Result

| Diagnostic | C: control | M: halved margins | P: order 8 | X: continuation |
| --- | ---: | ---: | ---: | ---: |
| Search | 1795 s, budget | 1796 s, budget | 1796 s, budget | 327 iterations, 256 s |
| Boundary RMS | 0.0018244 | 0.0017154 | 0.0017778 | 0.0020658 |
| Boundary mean (worse shift) | 0.00152 | 0.00143 | 0.00147 | 0.00169 |
| Boundary maximum (shift 0 / 0.5) | 0.0085 / 0.0086 | 0.0079 / 0.0080 | 0.0083 / 0.0086 | 0.0096 / 0.0096 |
| Interior RMS (max of 3) | 0.01014 | **0.00890** | **0.00981** | **0.00200** |
| Acceptance v2 / v1 | fail (interior) / fail | **pass** / fail | **pass** / fail | **pass** / fail |
| Length / coil–coil / coil–plasma bound (m) | 3.482 / 0.0610 / 0.137 | 3.491 / 0.0602 / 0.149 | 3.465 / 0.0649 / 0.145 | 3.474 / 0.0681 / 0.134 |
| Curvature upper bound (/m) | 10.03 | 11.02 | 10.08 | 10.04 |
| Frozen current (A) | 307,933 | 307,610 | 307,831 | 305,301 |

All arms pass the numerical cross-checks, flux and current limits and continuous
geometry. The preregistered ratios of boundary RMS to the control are
**M/C = 0.940** (#70 on reference401: 0.942) and **P/C = 0.974** (#53: 0.964).
Retained outputs were 207, 204 and 246 MiB, below the 256 MiB ceiling. P's coil
set, rechecked with current main for the leaderboard, gives identical values.

## Bounce diagnostic (exploratory)

`scripts/measure_coil_bounce.py` with its defaults, as in [#89](ISSUE89_V2_COIL_BOUNCE.md).
Failed launch lines use the registered rule (exactly two complete wells per line at
q = 0.03).

| Diagnostic | Ideal target | #35 fit | C | M | P | X |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Narrow action-variance score (×10⁻⁵) | 1.10 | 4.04 | 3.43 | **2.79** | 3.07 | **1.84** |
| Wide score | 2.12e-4 | incomplete | incomplete | incomplete | incomplete | **2.51e-4** |
| Failed launch lines, s = 0.1 / 0.25 | 0 / 0 | 16 / 16 | 16 / 16 | 16 / 8 | 16 / 16 | **0 / 0** |
| Lowest B on any s = 0.1 line (threshold 1.02566) | — | 1.03005 | 1.02904 | 1.02694 | 1.02842 | 1.01004 |

## Reading

- **All three routes carry over.** Their ratios to the control match those on
  reference401, and the continuation again trades boundary error for interior
  error: from its start coils (the #35 control: interior 0.01363) boundary RMS rises
  2.4% while interior RMS falls 6.8×. By the script's own rule its best eligible
  point is the start, which fails v2. The worst v2 ratios leave 2% (P) to 11% (M)
  headroom.
- **Margins are thin.** M's continuous coil–coil bound is 0.2 mm above its 0.06 m
  limit; M and P needed the finer geometry level to pass.
- **Budget matters for the control.** With 1800 s instead of #35's 300 s, the same
  configuration lowers boundary RMS from 0.001953 to 0.001824 and interior RMS from
  0.01089 to 0.01014, just above the limit.
- **Only the low interior error completes the wide diagnostic.** In X's field every
  launch line has the required wells; the wide score is 1.19× and the narrow score
  1.67× the ideal target's. In the three fits the s = 0.1 field stays above the well
  threshold, as for reference401 in #89.
- **Benefit transfer is still unresolved.** Launch labels are target coordinates,
  not realized flux labels ([#48](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/48)),
  and the same method's field on reference401 has not been measured, so there is no
  matched comparison yet.

Limits: one seed, one budget and one machine per arm; v2 was calibrated with
reference401 results known; vacuum field; launch labels in target coordinates.
Errors against different targets are not directly comparable. Raw outputs:
maintainer's ignored `artifacts/step3-v2-methods/`.
