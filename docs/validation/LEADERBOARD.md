# Coil leaderboard, acceptance v2

Updated 13 October 2026. [Validation index](README.md) · [Acceptance v2](ACCEPTANCE_V2.md) ·
[Entries and results](../../submissions/leaderboard-v2.json)

**Three coil sets pass acceptance v2,** all fitted to reference401: the halved-margin
fit (lowest boundary error), @pjckoch's headroom continuation (lowest interior
error, and the earliest to pass) and the order-8 fit of #53's configuration. None
passes the original v1 limits. Passing v2 accepts the field
and geometry checks only; magnetic surfaces, benefit transfer, pressure and
engineering remain open ([Step 4](../steps/STEP_4_PLASMA_AND_COILS.md)).

## Rules

- **Who is listed:** every distinct coil set with a public record: each public
  candidate in `submissions/`, the public starter, and the selected coil set of each
  recorded research run. Smoke tests, qualification runs and runs that repeat a
  listed coil set or configuration are left out; every run is evaluated in the
  [v2 results](ACCEPTANCE_V2_RESULTS.md).
- **How it is checked:** on the maintainer's machine, with flux-normalized current,
  the 128 × 128 fine boundary grid at both shifts, three interior resolutions and
  continuous geometry. Public candidates and the #53 snapshots were checked with
  `scripts/check_coils.py` at main `44beb11`; the #70 and #35 rows use their stored
  completed runs. `scripts/acceptance_v2.py` then gives both verdicts.
- **Ranking:** v2 passes first, then the worst v2 ratio: the largest of
  mean/0.0018, maximum/0.013 and interior/0.01. A ratio of 0.90 means all three
  field limits could tighten by 10% before the set fails. Lower is better.
- **Original contributor:** who made the coil set or the configuration and code that
  produced it. "Maintainer run" means the maintainer executed a contributor's
  configuration.

<!-- leaderboard:start -->
**Target reference401**

| Rank | Coil set | Original contributor | Record | v2 | v1 | Boundary mean | Boundary max | Interior RMS | Other checks | Worst v2 ratio |
| ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: |
| 1 | [Halved-margin six-coil fit](../../submissions/halved-margin-six-coil/README.md) | @DrWorkhard (maintainer) | #70 arm M, #88 | **pass** | fail | 0.00143 | 0.0081 | 0.00902 | pass | 0.902 |
| 2 | [Headroom continuation with passing interior](../../submissions/interior-pass-headroom-continuation/README.md) | @pjckoch | #12 | **pass** | fail | 0.00168 | 0.0095 | 0.00200 | pass | 0.931 |
| 3 | [Order-8 six-coil fit](../../docs/optimization/ISSUE53_COIL_FREEDOM.md) | @pjckoch (configuration and code; maintainer run) | #53 arm P, rerun on 9ecdf27 | **pass** | fail | 0.00146 | 0.0083 | 0.00949 | pass | 0.949 |
| 4 | [Current-margin six-coil fit](../../docs/optimization/ISSUE70_CONSTRUCTION_MARGINS.md) | @DrWorkhard (maintainer) | #70 arm C | fail | fail | 0.00153 | 0.0085 | 0.01012 | pass | 1.012 |
| 5 | [Matched reference401 fit](../../docs/optimization/ISSUE25_MATCHED_TARGETS.md) | @DrWorkhard (maintainer) | #35 | fail | fail | 0.00163 | 0.0091 | 0.01072 | pass | 1.072 |
| 6 | [Millimetre ranking counterexample](../../submissions/millimetre-ranking-counterexample/README.md) | @alexanderlehner | #44 | fail | fail | 0.00171 | 0.0095 | 0.01139 | pass | 1.139 |
| 7 | [Length-headroom six-coil fit](../../submissions/length-headroom-six-coil/README.md) | @DrWorkhard (maintainer) | headroom study v3 | fail | fail | 0.00171 | 0.0094 | 0.01148 | pass | 1.148 |
| 8 | [Constraint-aware shape 52](../../submissions/constraint-aware-shape52/README.md) | @DrWorkhard (maintainer) | constraint-aware study | fail | fail | 0.11123 | 0.5153 | 0.31232 | pass | 61.796 |
| 9 | [Base-coil translation sweep](../../submissions/server-public-exploration-001/README.md) | @alexanderlehner | #5 | fail | fail | 0.21546 | 0.5980 | 0.37124 | pass | 119.699 |
| 10 | [Public starter coils](../../examples/clear-coil-samples-v1/README.md) | @DrWorkhard (starter) | starter | fail | fail | 0.21547 | 0.5980 | 0.37124 | pass | 119.708 |

**Target selected401**

| Rank | Coil set | Original contributor | Record | v2 | v1 | Boundary mean | Boundary max | Interior RMS | Other checks | Worst v2 ratio |
| ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: |
| 1 | [Matched improved-target fit](../../docs/optimization/ISSUE25_MATCHED_TARGETS.md) | @DrWorkhard (maintainer) | #35 | fail | fail | 0.00165 | 0.0093 | 0.01089 | pass | 1.089 |
| 2 | [Length-headroom coils on the improved target (control)](../../submissions/length-headroom-six-coil/README.md) | @DrWorkhard (maintainer) | #35 control | fail | fail | 0.00172 | 0.0094 | 0.01363 | pass | 1.363 |
<!-- leaderboard:end -->

Boundary values are the larger of the two grid shifts; interior is the largest of
three resolutions; "other checks" are numerical cross-checks, flux and current
limits and continuous geometry. Different targets are ranked separately.

## The order-8 row

@pjckoch's own #53 run 2 reported boundary RMS 0.0017815, maximum 0.00866 and
interior RMS 0.009859; its arrays are on the contributor's machine and the plain
mean was not reported, so it is not ranked directly. The maintainer reran the same
configuration on the contributor's merged code `9ecdf27` (same seed, order 8, 1800 s + 900 s, one
thread; 9,397 trials): boundary RMS 0.0017658, interior 0.00949. An earlier
maintainer run of 6 October gave a coil set within 11 µm of it and the same
verdict. Both are close to the contributor's reported values.

## How to update

In the native environment, `python scripts/leaderboard_v2.py` checks any entry whose
run is missing, re-evaluates every entry and rewrites this table and the results in
the entries file. New public candidates are added through a normal submission PR;
the maintainer adds the entry and runs the native checks, which hosted CI cannot run
yet.
