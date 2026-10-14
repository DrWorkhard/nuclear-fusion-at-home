# Field acceptance v2: evaluation of all runs

Evaluated 13 October 2026, after [acceptance v2](ACCEPTANCE_V2.md) was frozen in
`8a36051`. [Validation index](README.md) · [Leaderboard](LEADERBOARD.md)

**Three distinct coil sets pass acceptance v2,** all fitted to reference401:
@pjckoch's headroom continuation (#12, merged 4 October 2026, the earliest), the
order-8 fit of #53's configuration and the halved-margin fit of #70 (lowest boundary
error). The [leaderboard](LEADERBOARD.md) ranks them. No coil set passes the original
v1 limits. This is not Step 4 or
physical acceptance: magnetic surfaces, benefit transfer, pressure and engineering
remain open. **Update (same day):** all three methods also pass on the improved
Step 3 target ([record](../optimization/STEP3_V2_METHODS.md)). **Update (14 October):**
combinations of them pass too and lead on both targets
([record](../optimization/ISSUE102_COMBINED_METHODS.md)).

**Correction (same day).** The first version of this page (#87) reported one passing
coil set, the halved-margin fit, and called it the first in the project. Both claims
were wrong. That evaluation covered only the seven runs it knew about; it missed four
completed runs on the maintainer's machine and never checked the public candidates.
A complete search, below, and the [leaderboard](LEADERBOARD.md) checks found the
other passing sets.

## Method

Every run directory under the maintainer's `artifacts/` with saved fine-grid arrays
(25) was passed to `python scripts/acceptance_v2.py <run>`, which first checks that
the arrays reproduce the run's recorded boundary RMS. Eleven are completed runs and
are evaluated below, with the later #53 reproduction. The other 14 predate the
completed-run record; their selected coil sets were rechecked with
`scripts/check_coils.py` at main `44beb11` (the [leaderboard](LEADERBOARD.md) also
checks every public candidate this way).

## Completed runs

All pass the numerical cross-checks, flux and current limits and continuous
geometry; boundary values are given at grid shifts 0 / 0.5.

| Run (raw outputs under `artifacts/`) | Boundary mean | Boundary maximum | Interior RMS (max of 3) | v1 | v2 |
| --- | ---: | ---: | ---: | --- | --- |
| **#70 arm M, halved margins** | **0.00143 / 0.00143** | **0.0081 / 0.0080** | **0.00902** | fail | **pass** |
| **#53 arm P, order 8, maintainer run of 6 October** | **0.00146 / 0.00146** | **0.0081 / 0.0083** | **0.00949** | fail | **pass** |
| **#53 arm P, maintainer reproduction on `9ecdf27`** | **0.00146 / 0.00145** | **0.0081 / 0.0083** | **0.00949** | fail | **pass** |
| #53 arm C, order 5, maintainer run of 6 October | 0.00153 / 0.00153 | 0.0084 / 0.0084 | 0.01011 | fail | fail (interior) |
| #70 arm C, current margins | 0.00153 / 0.00153 | 0.0085 / 0.0084 | 0.01012 | fail | fail (interior) |
| #35 reference401 fit (`issue25-matched-v1`) | 0.00163 / 0.00163 | 0.0091 / 0.0088 | 0.01072 | fail | fail (interior) |
| Length-headroom control (`issue70…/seed-check`) | 0.00170 / 0.00171 | 0.0094 / 0.0092 | 0.01148 | fail | fail (interior) |
| #35 reference401 control | 0.00170 / 0.00171 | 0.0094 / 0.0092 | 0.01148 | fail | fail (interior) |
| Refactor smoke fit, 5 s search (`coil-fit-refactor-smoke-20261004`) | 0.00170 / 0.00171 | 0.0094 / 0.0092 | 0.01149 | fail | fail (interior) |
| #37 coil-diagnostic qualification (`issue37-coil-diagnostics-v1`) | 0.00212 / 0.00212 | 0.0100 / 0.0099 | 0.01290 | fail | fail (boundary, interior) |
| #35 improved-target fit | 0.00165 / 0.00165 | 0.0093 / 0.0090 | 0.01089 | fail | fail (interior) |
| #35 improved-target control | 0.00172 / 0.00172 | 0.0094 / 0.0092 | 0.01363 | fail | fail (interior) |

v2 limits: mean ≤ 0.0018, maximum ≤ 0.013, interior ≤ 0.01. The last two rows fit
the improved Step 3 target. The two #53 arm P runs (6 October on an unpublished
integration commit, 13 October on `9ecdf27`, 9,425 and 9,397 trials) selected coil
sets within 11 µm of each other; the 6 October order-5 run repeats #70 arm C's
configuration. The smoke fit repeats the length-headroom coils after a 5 s search.

## Older runs, rechecked

None of the 14 older coil sets passes v2. The closest, the wider-box long run of
the coherent-coil study (`coherent-longrun-v2`), meets all three field limits (mean
0.00168, maximum 0.0106, interior 0.00977) but fails continuous geometry. The two
length-headroom selections (`coil-headroom-v2`, `-v3`) fail only on interior RMS
(0.0117, 0.0115). The other 11 exceed the boundary mean limit by factors of 2 to 93,
and five of them also fail geometry.

## Reading

- **v2 was set with these results known.** Our fits already ranked near the best 10%
  of the benchmark; that the boundary limits pass is expected, not a new discovery.
- **The interior field decides** for the fixed-target fits. The three routes that
  passed differ: a longer local continuation (#12) traded boundary error for a much
  lower interior error; higher coil order (#53) and halved construction margins (#70)
  lowered both slightly.
- **Margins are thin.** The halved-margin set is 0.6 mm above the coil–coil limit;
  several passing sets sit at their length and curvature penalties.
- **All runs above fit reference401** except the two #35 improved-target rows; the
  later [Step 3 reproductions](../optimization/STEP3_V2_METHODS.md) pass too. Traced
  field lines do not prove nested surfaces, and benefit transfer is unresolved.
