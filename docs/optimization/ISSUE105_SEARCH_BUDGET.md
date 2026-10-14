# A 4-hour search for the best combination (#105)

[Active coil research](README.md) · [Acceptance v2](../validation/ACCEPTANCE_V2.md) ·
[Issue #105](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/105)

**Eight times more search lowers the field errors by about 9% but loses the geometry
certificate, so the preregistered budget benefit is not shown.** With a 4-hour
search instead of 30 minutes, #102's best combination reaches boundary mean
0.00128, maximum 0.0075 and interior RMS 0.00156 on the improved Step 3 target
(selected401). Those field errors alone would give a worst v2 ratio of 0.709,
against 0.778 for #102 arm A. But continuous geometry stays unresolved: the
coil–coil bound (0.0596 m) and the length bound (3.509 m) miss their limits, so the
set fails v2. Recorded 14 October 2026; field and geometry acceptance only, not
physical acceptance or benefit transfer.

## Question and method

The [#102 searches](ISSUE102_COMBINED_METHODS.md) stopped on their 30-minute
budget with the last point selected. Is the best combination budget-limited?
[#104](https://github.com/DrWorkhard/nuclear-fusion-at-home/pull/104) raised the
fitter's search cap to 4 h and its output cap to 1 GiB; objective, selection,
stopping and checks are unchanged.

As preregistered in #105, arm L repeated #102 arm A (interior term, halved margins
and order 8) with only the budget changed: `scripts/fit_coils.py --order 8
--margins halved --interior-weight 0.05 --seconds 14400 --check-seconds 900` on
main `ffdd6a0`, #92's seed (`db836feb…`), the archived selected401 Wout
(`8cd6bebf…`) and input (`6bec3483…`), one thread, under `caffeinate -is`, with no
other heavy job. Provenance is clean and every recorded source matches before and
after the run. The comparator is arm A (worst v2 ratio 0.7779), not rerun. A budget
benefit needs a v2 pass, continuous geometry and a worst ratio ≤ 0.739 (5% below
A). Before the run, #105 disclosed the inspected 30-minute curves and an
extrapolation to about 0.74–0.76.

## Result

| Diagnostic | A: 30 min (#102) | L: 4 h |
| --- | ---: | ---: |
| Search | 1795 s, budget | 14,395 s, budget |
| Bundles / solver iterations | 8,168 / 5,133 | 66,653 / 47,620 |
| Boundary RMS | 0.0017078 | 0.0015537 |
| Boundary mean (worse shift) | 0.00140 | 0.00128 |
| Boundary maximum (shift 0 / 0.5) | 0.0079 / 0.0082 | 0.0073 / 0.0075 |
| Interior RMS (three levels) | 0.00174 / 0.00172 / 0.00172 | 0.00156 / 0.00153 / 0.00153 |
| Interior on the objective's own surfaces | 0.00157 | 0.00144 |
| Worst ratio of the three field limits | 0.778 | 0.709 |
| Continuous geometry (finer level) | pass | **unresolved** |
| Coil–coil bound / sampled (m; limit 0.06) | 0.0601 / 0.0649 | **0.0596** / 0.0648 |
| Length bound / sampled (m; limit 3.5) | 3.495 / 3.470 | **3.509** / 3.470 |
| Coil–plasma bound (m; limit 0.08) | 0.148 | 0.146 |
| Curvature upper bound (/m; limit 12) | 11.07 | 11.11 |
| Frozen current (A) | 305,428 | 305,417 |
| Acceptance v2 | pass | **fail** (geometry) |

Numerical cross-checks and the flux and current limits pass; v1 fails (boundary
RMS and maximum). Against the preregistered rules:

- **Budget benefit: not shown.** L fails continuous geometry and therefore v2. Its
  field ratios alone (0.709) are below 0.739, but the rule needs both.
- **Replication: exact.** All 8,168 completed trials of arm A reappear in L with
  identical objective values and coefficient hashes, so there is no deviating
  index. L's trial 8168 has A's selected value, 1.5198438569785821e-06. L continued
  where A's budget stopped.

Secondary measurements:

- **Search.** Both stopped on the time budget with the last completed bundle
  selected, so even 4 h did not converge.
- **Cost:** 4 h 0 min wall time for the fit and 8.5 s for the bounce diagnostic;
  483 MiB retained output (recording v3), within the 1 GiB cap and close to #104's
  projection.

## How the search improved

Best-so-far eligible point in L's own recording (search-grid metrics). L's trials
carry no timestamps (optional ones were added after the run, in
[#107](https://github.com/DrWorkhard/nuclear-fusion-at-home/pull/107)), so time is
estimated as index × 14,395 s / 66,653 bundles.

| Time | Bundle | Selection value | Boundary mean | Boundary RMS | Interior RMS |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1,800 s | 8,334 | 1.517e-6 | 0.001273 | 0.001706 | 0.001567 |
| 3,600 s | 16,667 | 1.424e-6 | 0.001230 | 0.001653 | 0.001529 |
| 7,200 s | 33,337 | 1.286e-6 | 0.001166 | 0.001571 | 0.001455 |
| 14,395 s | 66,653 | 1.259e-6 | 0.001158 | 0.001554 | 0.001442 |

Gain per doubling of time, for the boundary mean: 3.3%, 5.3% and 0.7% (RMS 3.1%,
5.0% and 1.1%; selection value 6.1%, 9.7% and 2.1%). Over all three doublings the
boundary mean fell 9.0% and the RMS 8.9%. Gains were not steady: the second doubling
gave most and the last least. The 1,800 s row is bundle 8,334, not A's 8,168,
because L averaged slightly less time per bundle.

## Why the geometry is unresolved

The checker certifies continuous geometry from sampled values plus allowances that
grow with the coils' derivative bounds, at 1,024 and then 2,048 coil nodes. Halved
margins put the length penalty at 3.47 m and the coil–coil penalty at 0.065 m, which
leaves 30 mm and 5 mm of headroom for those allowances. In A and in L the selected
point sits on the penalty thresholds (sampled length 3.470 m, coil–coil 0.065 m,
curvature 11.0 /m). L's coils, however, have larger derivative bounds (second
derivative 323 against 235, third 10,551 against 7,152, maxima over coils). Its
allowances, 39 mm for length and 5.2 mm for coil–coil, exceed the headroom; A's,
25 mm and 4.8 mm, fit. No sampled value violates a limit, so the checker reports
"unresolved" rather than "fail"; v2 requires a pass. The check levels are fixed,
and refining them after seeing this result would be a post-hoc change, so the
result stands as checked.

## Bounce diagnostic (exploratory)

`scripts/measure_coil_bounce.py` with its defaults, as in #102.

| Diagnostic | Ideal target | A | L |
| --- | ---: | ---: | ---: |
| Failed launch lines, s = 0.1 / 0.25 | 0 / 0 | 0 / 0 | **0 / 0** |
| Wide score | 2.12e-4 | 1.84e-4 | 1.69e-4 |
| Narrow score (×10⁻⁵) | 1.10 | 1.87 | 1.49 |
| Lowest B on any s = 0.1 line (threshold 1.02566) | — | 1.01095 | 1.01103 |

L's coil/ideal score ratios are 0.12, 0.59, 0.90, 1.09 and 1.06 at s = 0.1, 0.25,
0.5, 0.75 and 0.9 (A: 0.11, 0.65, 0.99, 1.21, 1.12). The narrow score moves toward
the ideal; the wide score moves further below it, which is a larger mismatch on
the inner surfaces, not a better plasma. No benefit-transfer claim: launch labels
are target coordinates
([#48](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/48)).

## Reading

- **More search helps the field but not acceptance.** The disclosed extrapolation
  (0.74–0.76) underestimated the field gain; the geometry certificate, not the
  field, now binds.
- **Halved margins are thin for long searches.** The optimizer keeps the sampled
  geometry on the penalty thresholds while the coil shapes gain sharper features,
  and the certificate's allowance grows with them. A long search that is to pass
  would need more geometry headroom or a selection that requires the continuous
  certificate. Either is a new preregistered change, not a rescue of L.
- **The 30-minute leaderboard entries stand.** A remains the leading set on
  selected401; L is listed as a distinct research run that fails v2.

Limits: one seed, one machine; the curve points come from one run, not independent
repeats; v2 is benchmark-relative and was calibrated with reference401 results
known; vacuum field. Raw outputs: maintainer's ignored `artifacts/budget-v1/`
(selected snapshot `0bbcb986…`).
