# Two routes to a passing 4-hour search (#109)

[Active coil research](README.md) · [Acceptance v2](../validation/ACCEPTANCE_V2.md) ·
[Issue #109](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/109)

**Both routes give a 4-hour search that passes acceptance v2, but neither clears
the preregistered benefit bar of 0.739.** On the improved Step 3 target
(selected401), arm W, a 4-hour search with the current margins, reaches a worst v2
ratio of 0.761. Arm S, the latest geometry-certified point of #105's halved-margin
search, reaches 0.765. #102 arm A has 0.778. Both arms pass continuous geometry;
W now ranks first on selected401 and S second. Recorded 14 October 2026; field and
geometry acceptance only, not physical acceptance or benefit transfer.

## Question and method

In [#105](ISSUE105_SEARCH_BUDGET.md), a 4-hour search of #102 arm A (interior term,
halved margins and order 8) lowered the field errors by 9%. Its continuous geometry
stayed unresolved, because the certificate's allowances outgrew the 30 mm length and
5 mm coil–coil headroom that halved margins leave. #109 preregistered two routes
with one rule per arm. A benefit needs a v2 pass, continuous geometry and a worst v2
ratio ≤ 0.95 × 0.7779 = 0.739. The comparator is arm A (0.7779), not rerun.

- **Arm W (wider margins):** the same 4-hour search with the current margins
  (penalties at 3.44 m and 0.07 m), which leave 60 mm and 10 mm of headroom:
  `scripts/fit_coils.py --order 8 --margins current --interior-weight 0.05
  --seconds 14400 --check-seconds 900` on main `e8d9099`. This main records
  search-relative times ([#107](https://github.com/DrWorkhard/nuclear-fusion-at-home/pull/107)).
- **Arm S (certified selection):** no new search. The selection never feeds back
  into the optimizer, and #105 reproduced A bit for bit, so a fresh halved-margin
  run would retrace L.
  - [`scripts/certified_selection.py`](../../scripts/certified_selection.py)
    ([#110](https://github.com/DrWorkhard/nuclear-fusion-at-home/pull/110), main
    `a90c8d1`) re-reads L's recording. It takes the fitter's best-so-far eligible
    point at every 500th completed bundle and at the end.
  - It certifies these points backward from the end, with the check's own
    continuous geometry function and levels, and selects the first `pass`.
  - `scripts/check_coils.py --seconds 900` then checks the selected point.

Both arms used #92's seed (`db836feb…`), the archived selected401 Wout (`8cd6bebf…`)
and its input (`6bec3483…`). They ran on one thread under `caffeinate -is`, one
after the other, with no other heavy job. Provenance is clean, and every recorded
source matches before and after each run.

## Result

| Diagnostic | A: 30 min (#102) | L: 4 h (#105) | W: 4 h, current margins | S: certified point of L |
| --- | ---: | ---: | ---: | ---: |
| Selected bundle (time into the search) | 8,168 (1,795 s) | 66,653 (14,395 s) | 66,041 (14,394 s) | 10,994 (≈ 2,374 s) |
| Boundary RMS | 0.0017078 | 0.0015537 | 0.0016626 | 0.0016814 |
| Boundary mean (worse shift) | 0.00140 | 0.00128 | 0.00137 | 0.00138 |
| Boundary maximum (shift 0 / 0.5) | 0.0079 / 0.0082 | 0.0073 / 0.0075 | 0.0079 / 0.0079 | 0.0072 / 0.0075 |
| Interior RMS (three levels) | 0.00174 / 0.00172 / 0.00172 | 0.00156 / 0.00153 / 0.00153 | 0.00168 / 0.00165 / 0.00165 | 0.00171 / 0.00169 / 0.00169 |
| Interior on the objective's own surfaces | 0.00157 | 0.00144 | 0.00157 | 0.00157 |
| Worst ratio of the three field limits | 0.778 | 0.709 | **0.761** | **0.765** |
| Continuous geometry (finer level) | pass | unresolved | pass | pass |
| Coil–coil bound / sampled (m; limit 0.06) | 0.0601 / 0.0649 | 0.0596 / 0.0648 | 0.0646 / 0.0698 | 0.0601 / 0.0650 |
| Length bound / sampled (m; limit 3.5) | 3.495 / 3.470 | 3.509 / 3.470 | 3.478 / 3.440 | 3.496 / 3.470 |
| Coil–plasma bound (m; limit 0.08) | 0.148 | 0.146 | 0.151 | 0.147 |
| Curvature upper bound (/m; limit 12) | 11.07 | 11.11 | 10.07 | 11.45 |
| Frozen current (A) | 305,428 | 305,417 | 305,421 | 305,413 |
| Acceptance v2 | pass | fail (geometry) | **pass** | **pass** |

For W and S, the numerical cross-checks and the flux and current limits pass; v1
fails (boundary RMS and maximum). The boundary mean binds the worst ratio in all
four columns. Against the preregistered rules:

- **Arm W: benefit not shown.** W passes v2 and continuous geometry, but
  0.761 > 0.739. It is 2.2% below A. The disclosed guess was 0.75–0.77.
- **Arm S: benefit not shown.** S passes v2 and continuous geometry at 0.765, 1.7%
  below A. The latest certified checkpoint is bundle 10,994, about 2,374 s into L.
  To clear 0.739 it would have had to reach about bundle 18,900, as disclosed.
- **Validation gates: passed.** The rebuilt snapshot and geometry report reproduce
  A's selected trial 8,168 (pass) and L's selected trial 66,653 (unresolved) exactly.
  For S, `check_coils.py` reproduces the certification's geometry report exactly.

### Arm S: where the certificate is lost

- **Budget:** 113 checkpoints were certified in 1,318 s of the 1,800 s budget, about
  11.5 s each. The first 112, from the end back to bundle 11,493, are
  unresolved; the next, bundle 10,994, passes.
- **What binds:** every unresolved checkpoint misses the coil–coil limit (lower
  bounds 0.0589–0.0598 m). From bundle 15,496 on (104 checkpoints), the length bound
  is above 3.5 m as well. No sampled value violates a limit.
- **The selected point:** its allowances are 25.8 mm for length and 5.2 mm for
  coil–coil.
  - The length headroom is 30 mm.
  - The coil–coil allowance exceeds the 5 mm headroom, but the binding pair sits
    5.3 mm above the limit, so its bound clears 0.06 m by 0.07 mm.
  - Its maximum curvature is the highest of the four sets (sampled 11.40 /m at 4,096
    nodes, bound 11.45 /m), still inside 12 /m.
- **Time estimate:** L carries no recorded times, so the selected time is index ×
  14,395 s / 66,653 bundles. The true certification boundary lies between bundles
  10,994 and 11,493.
- **Field mapping:** the checked boundary mean is 1.095 times the search-grid mean,
  close to the 1.10 disclosed for A and L.

### Arm W: secondary measurements

- **Search:** 66,043 bundles were attempted and 66,041 completed, with 49,596 solver
  iterations. The run stopped on the time budget with the last completed bundle
  selected, so even 4 hours did not converge. As in L, two trials failed: trial 11
  (degenerate unit flux) and the bundle the deadline cut.
- **Geometry:** the allowances are 37.7 mm for length and 5.4 mm for coil–coil,
  inside the 60 mm and 10 mm of headroom. The bounds therefore clear the limits by
  22 mm and 4.6 mm. The coils' derivative bounds (second 309, third 9,833) lie
  between A's (235 and 7,152) and L's (323 and 10,551). The coarser check level is
  unresolved, as for A.
- **Field mapping:** the checked boundary mean is 1.103 times the search-grid mean.
- **Cost:** 4 h 0 min wall time for the fit and 8.4 s for the bounce diagnostic;
  490 MiB retained output (recording v3).

Best-so-far eligible point in W's recording (search-grid metrics), at #107's
recorded `search_elapsed_end_s`. L's boundary mean is shown for comparison; its
times are estimated from the bundle index.

| Time | Bundle | Selection value | Boundary mean | Boundary RMS | Interior RMS | L: boundary mean |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1,800 s | 8,000 | 1.733e-6 | 0.001365 | 0.001823 | 0.001697 | 0.001273 |
| 3,600 s | 15,980 | 1.606e-6 | 0.001308 | 0.001754 | 0.001651 | 0.001230 |
| 7,200 s | 32,447 | 1.481e-6 | 0.001255 | 0.001684 | 0.001573 | 0.001166 |
| 14,394 s | 66,041 | 1.444e-6 | 0.001242 | 0.001663 | 0.001568 | 0.001158 |

- **Gain per doubling (boundary mean):** 4.2%, 4.1% and 1.0%; RMS 3.8%, 3.9% and
  1.3%; selection value 7.3%, 7.8% and 2.5%.
- **Total:** over three doublings the boundary mean fell 9.0% and the RMS 8.8%, as
  in L. Again the last doubling gave the least.
- **Cost of the current margins:** at every time W's boundary mean is 6–8% above
  L's. #92's 30-minute arms (order 5, no interior term) had suggested about 6%.

## Bounce diagnostic (exploratory)

`scripts/measure_coil_bounce.py` with its defaults, as in #102 and #105.

| Diagnostic | Ideal target | A | L | W | S |
| --- | ---: | ---: | ---: | ---: | ---: |
| Failed launch lines, s = 0.1 / 0.25 | 0 / 0 | 0 / 0 | 0 / 0 | **0 / 0** | **0 / 0** |
| Wide score | 2.12e-4 | 1.84e-4 | 1.69e-4 | 1.71e-4 | 1.82e-4 |
| Narrow score (×10⁻⁵) | 1.10 | 1.87 | 1.49 | 1.56 | 1.72 |
| Lowest B on any s = 0.1 line (threshold 1.02566) | — | 1.01095 | 1.01103 | 1.01100 | 1.01094 |

Coil/ideal score ratios at s = 0.1, 0.25, 0.5, 0.75 and 0.9:
- W: 0.16, 0.55, 0.90, 1.15 and 1.11;
- S: 0.16, 0.58, 0.98, 1.24 and 1.16.

As for L, a lower wide score than A means a larger mismatch on the inner surfaces,
not a better plasma. No benefit-transfer claim: launch labels are target coordinates
([#48](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/48)).

## Reading

- **A long search can pass, but it gains little.** Both routes recover a passing
  set, and both lead the selected401 board. However, the gain over A is 2.2% (W) and
  1.7% (S), well short of the 5% bar.
- **Halved margins keep a long search certifiable for only about 40 minutes.** After
  that, the optimizer holds the sampled coil–coil distance at the 0.065 m penalty
  while the coil shapes sharpen. The certificate's allowance then exceeds the 5 mm
  headroom. S therefore keeps about a sixth of L's search time and of its
  boundary-mean gain over A.
- **Current margins keep the certificate but cost about 7% field error,** which
  absorbs most of the 9% that the longer search gains.
- **Untried variants:** a margin preset between the two, or a penalty on the
  certificate's bound instead of the sampled value. Either would be a new
  preregistered change. The pinned priorities
  ([#116](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/116)) put
  plasma quality first, so no further coil-budget arm is planned.

Limits:
- one seed and one machine;
- W's curve comes from one run;
- S's 500-bundle checkpoint spacing (about 108 s) limits how close to the
  certification boundary it selects;
- v2 is benchmark-relative and was calibrated with the reference401 results known;
- vacuum field.

Raw outputs are in the maintainer's ignored `artifacts/budget-v2/`. The selected
snapshots are W `99629fce…` and S `c4eef1cf…`.
