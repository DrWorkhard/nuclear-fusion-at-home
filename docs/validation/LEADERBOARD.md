# Coil leaderboard, acceptance v2

Updated 14 October 2026. [Validation index](README.md) · [Acceptance v2](ACCEPTANCE_V2.md) ·
[Entries and results](../../submissions/leaderboard-v2.json)

**Nine coil sets pass acceptance v2, four on the original and five on the improved
target.** They come from three methods and their combinations: halved margins,
@pjckoch's interior field term (as the headroom continuation or inside the active
fitter) and the order-8 fit of #53's configuration. On both targets a combination
ranks first: halved margins with the interior term, plus order 8 on the improved
target ([combination record](../optimization/ISSUE102_COMBINED_METHODS.md),
[Step 3 record](../optimization/STEP3_V2_METHODS.md)). None passes the original v1
limits. Passing v2 accepts the field
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
  `scripts/check_coils.py` at main `44beb11`, the improved-target order-8 set at
  `fb7756d`, the continuation at `3f769ce` and the #98 arm I candidate at `49dd45e`
  (same check behaviour); the other rows use
  their stored completed runs. `scripts/acceptance_v2.py` then gives both verdicts.
- **Ranking:** v2 passes first, then the worst v2 ratio: the largest of
  mean/0.0018, maximum/0.013 and interior/0.01. A ratio of 0.90 means all three
  field limits could tighten by 10% before the set fails. Lower is better.
- **Original contributor:** who made the coil set or the configuration and code that
  produced it. "Maintainer run" means the maintainer executed a contributor's
  configuration.

## Terms

- **Targets:** reference401 is the original Goodman plasma; selected401 is our
  improved [Step 3](../steps/README.md#step-3-vacuum-plasma-diagnostic) plasma.
  Errors against different targets are not directly comparable.
- **Halved margins:** the fitter penalizes coils before they reach an acceptance
  limit. Halved margins move each penalty threshold halfway to the unchanged limit
  (length 3.44 → 3.47 m, coil–coil 0.07 → 0.065 m, coil–plasma 0.09 → 0.085 m,
  curvature 10 → 11 /m): more freedom, thinner safety margins
  ([#70](../optimization/ISSUE70_CONSTRUCTION_MARGINS.md)).
- **Order 8:** coil shapes with Fourier order 8 instead of 5 (306 instead of 198
  coefficients; [#53](../optimization/ISSUE53_COIL_FREEDOM.md)).
- **Headroom continuation:** 327 further optimizer iterations with an added
  interior-field term ([#12](../../submissions/interior-pass-headroom-continuation/README.md)).
- **Interior term:** the same interior-field term inside the active fitter, weight
  0.05 ([#98](../optimization/ISSUE98_INTERIOR_TERM.md)).

<!-- leaderboard:start -->
### Original Goodman target (reference401)

| Rank | Coil set | Original contributor | Record | v2 | v1 | Boundary mean | Boundary max | Interior RMS | Other checks | Worst v2 ratio |
| ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: |
| 1 | [Interior term with halved margins](../../submissions/interior-term-halved-margin/README.md) | @pjckoch | #98 arm I, #100 | **pass** | fail | 0.00150 | 0.0083 | 0.00184 | pass | 0.836 |
| 2 | [Halved-margin six-coil fit](../../submissions/halved-margin-six-coil/README.md) | @DrWorkhard (maintainer) | #70 arm M, #88 | **pass** | fail | 0.00143 | 0.0081 | 0.00902 | pass | 0.902 |
| 3 | [Headroom continuation with passing interior](../../submissions/interior-pass-headroom-continuation/README.md) | @pjckoch | #12 | **pass** | fail | 0.00168 | 0.0095 | 0.00200 | pass | 0.931 |
| 4 | [Order-8 six-coil fit](../../docs/optimization/ISSUE53_COIL_FREEDOM.md) | @pjckoch (configuration and code; maintainer run) | #53 arm P, rerun on 9ecdf27 | **pass** | fail | 0.00146 | 0.0083 | 0.00949 | pass | 0.949 |
| 5 | [Current-margin six-coil fit](../../docs/optimization/ISSUE70_CONSTRUCTION_MARGINS.md) | @DrWorkhard (maintainer) | #70 arm C | fail | fail | 0.00153 | 0.0085 | 0.01012 | pass | 1.012 |
| 6 | [Matched reference401 fit](../../docs/optimization/ISSUE25_MATCHED_TARGETS.md) | @DrWorkhard (maintainer) | #35 | fail | fail | 0.00163 | 0.0091 | 0.01072 | pass | 1.072 |
| 7 | [Millimetre ranking counterexample](../../submissions/millimetre-ranking-counterexample/README.md) | @alexanderlehner | #44 | fail | fail | 0.00171 | 0.0095 | 0.01139 | pass | 1.139 |
| 8 | [Length-headroom six-coil fit](../../submissions/length-headroom-six-coil/README.md) | @DrWorkhard (maintainer) | headroom study v3 | fail | fail | 0.00171 | 0.0094 | 0.01148 | pass | 1.148 |
| 9 | [Constraint-aware shape 52](../../submissions/constraint-aware-shape52/README.md) | @DrWorkhard (maintainer) | constraint-aware study | fail | fail | 0.11123 | 0.5153 | 0.31232 | pass | 61.796 |
| 10 | [Base-coil translation sweep](../../submissions/server-public-exploration-001/README.md) | @alexanderlehner | #5 | fail | fail | 0.21546 | 0.5980 | 0.37124 | pass | 119.699 |
| 11 | [Public starter coils](../../examples/clear-coil-samples-v1/README.md) | @DrWorkhard (starter) | starter | fail | fail | 0.21547 | 0.5980 | 0.37124 | pass | 119.708 |

### Improved Step 3 target (selected401)

| Rank | Coil set | Original contributor | Record | v2 | v1 | Boundary mean | Boundary max | Interior RMS | Other checks | Worst v2 ratio |
| ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: |
| 1 | [Interior term, halved margins and order 8 on the improved target](../../docs/optimization/ISSUE102_COMBINED_METHODS.md) | @pjckoch (interior term and order 8; maintainer run) | #102 arm A | **pass** | fail | 0.00140 | 0.0082 | 0.00174 | pass | 0.778 |
| 2 | [Interior term with halved margins on the improved target](../../docs/optimization/ISSUE102_COMBINED_METHODS.md) | @pjckoch (interior term; maintainer run) | #102 arm I | **pass** | fail | 0.00147 | 0.0080 | 0.00182 | pass | 0.815 |
| 3 | [Halved-margin fit on the improved target](../../docs/optimization/STEP3_V2_METHODS.md) | @DrWorkhard (maintainer) | #92 arm M | **pass** | fail | 0.00143 | 0.0080 | 0.00890 | pass | 0.890 |
| 4 | [Headroom continuation on the improved target](../../docs/optimization/STEP3_V2_METHODS.md) | @pjckoch (method and code; maintainer run) | #94 | **pass** | fail | 0.00169 | 0.0096 | 0.00200 | pass | 0.937 |
| 5 | [Order-8 fit on the improved target](../../docs/optimization/STEP3_V2_METHODS.md) | @pjckoch (configuration and code; maintainer run) | #93 | **pass** | fail | 0.00147 | 0.0086 | 0.00981 | pass | 0.981 |
| 6 | [Current-margin fit on the improved target (control)](../../docs/optimization/STEP3_V2_METHODS.md) | @DrWorkhard (maintainer) | #92 arm C | fail | fail | 0.00152 | 0.0086 | 0.01014 | pass | 1.014 |
| 7 | [Matched improved-target fit](../../docs/optimization/ISSUE25_MATCHED_TARGETS.md) | @DrWorkhard (maintainer) | #35 | fail | fail | 0.00165 | 0.0093 | 0.01089 | pass | 1.089 |
| 8 | [Length-headroom coils on the improved target (control)](../../submissions/length-headroom-six-coil/README.md) | @DrWorkhard (maintainer) | #35 control | fail | fail | 0.00172 | 0.0094 | 0.01363 | pass | 1.363 |
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
