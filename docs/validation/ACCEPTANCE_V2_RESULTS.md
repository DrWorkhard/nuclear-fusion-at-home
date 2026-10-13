# Field acceptance v2: first evaluation

Evaluated 13 October 2026, after [acceptance v2](ACCEPTANCE_V2.md) was frozen in
`8a36051`. [Validation index](README.md)

**One coil set passes acceptance v2:** the halved-margin fit of the
[construction-margin probe](../optimization/ISSUE70_CONSTRUCTION_MARGINS.md) (arm M,
reference401, selected snapshot `4eab51eb…`). It is the first coil set in this
project to pass a complete field and geometry acceptance. No coil set passes the
original v1 limits. This is not Step 4 or physical acceptance: magnetic surfaces,
benefit transfer, pressure and engineering remain open.

## Method

Every completed fit or check run on the maintainer's machine with saved fine-grid
arrays was evaluated, without selection, by
`python scripts/acceptance_v2.py <run>` in the native environment. The evaluator
first checks that the saved arrays reproduce each run's recorded boundary RMS.
Contributor-held runs (for example the order-8 probe of #53) are not on this machine
and were not evaluated.

## Results

All seven runs pass the numerical cross-checks, flux and current limits and
continuous geometry; boundary values are given at grid shifts 0 / 0.5.

| Run (raw outputs under `artifacts/`) | Boundary mean | Boundary maximum | Interior RMS (max of 3) | v1 | v2 |
| --- | ---: | ---: | ---: | --- | --- |
| Length-headroom control (`issue70…/seed-check`) | 0.00170 / 0.00171 | 0.0094 / 0.0092 | 0.01148 | fail | fail (interior) |
| #70 arm C, current margins | 0.00153 / 0.00153 | 0.0085 / 0.0084 | 0.01012 | fail | fail (interior) |
| **#70 arm M, halved margins** | **0.00143 / 0.00143** | **0.0081 / 0.0080** | **0.00902** | fail | **pass** |
| #35 reference401 fit (`issue25-matched-v1`) | 0.00163 / 0.00163 | 0.0091 / 0.0088 | 0.01072 | fail | fail (interior) |
| #35 reference401 control | 0.00170 / 0.00171 | 0.0094 / 0.0092 | 0.01148 | fail | fail (interior) |
| #35 improved-target fit | 0.00165 / 0.00166 | 0.0093 / 0.0090 | 0.01089 | fail | fail (interior) |
| #35 improved-target control | 0.00172 / 0.00172 | 0.0094 / 0.0092 | 0.01363 | fail | fail (interior) |

v2 limits: mean ≤ 0.0018, maximum ≤ 0.013, interior ≤ 0.01. Every run passes the
v2 boundary limits; the unchanged interior limit decides.

## Reading

- **v2 was set with these results known.** Our fits already ranked near the best 10%
  of the benchmark; that the boundary limits pass is expected, not a new discovery.
- **The passing coil set has thin margins.** Its continuous coil–coil bound is 0.6 mm
  above the 0.06 m limit, and its length bound passed only at the finer level.
- **It fits reference401, not the improved Step 3 target**, and traced field lines
  (10/10 for 200 transits) do not prove nested surfaces. Benefit transfer is unresolved.
- **The interior field is now the binding criterion** for the fixed-target fits;
  looser construction margins lowered it below 0.01 in this one run.
