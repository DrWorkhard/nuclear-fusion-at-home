# Scientific status and evidence

Updated 26 September 2026.
[Overview](README.md) · [Roadmap](PROJECT_PLAN.md) · [Step results](steps/README.md) · [Public quickstart](validation/PUBLIC_QUICKSTART.md)

## Bottom line

**We have a bounded local research foundation, a numerically improved vacuum
plasma target, and useful coil-validation tools. We do not yet have a new
physically accepted coil design, a completed Step 4, a state-of-the-art advance,
or full SQuID-C readiness.**

Step and milestone statuses, including MS1 and MSX, are kept in the
[roadmap](PROJECT_PLAN.md); this page gives the evidence behind them. Full
[SQuID-C readiness](squid_c/SQUID_C_READINESS.md) has further gates; missing
author data is not the only obstacle.

## Established results and their limits

| Work package | Evidence-backed result | What remains unproven |
| --- | --- | --- |
| Steps [1](steps/STEP_1_FOUNDATION.md) and [2](steps/STEP_2_ITERATION.md): bounded foundation and iteration | Eight foundation gates, six mandatory scientific regressions, two exactly repeated 24-bundle paths and four independent candidate checks | Universal QI/engineering validity; those candidates remain physically rejected |
| [Step 3](steps/STEP_3_PLASMA_TARGET.md): own nfp2 vacuum plasma target | Relative bounce-action variance decreases from 2.3894265674e-4 to 2.1225270715e-4 (11.1700%); narrower-domain gain 4.8506%; all ten final gates pass | Global QI, improved measured confinement, finite pressure, practical coils or plant performance |
| [Step 4](steps/STEP_4_PLASMA_AND_COILS.md) coil initialization | All 12 constructed starting sets pass scoped geometry admission; selected six/eight-base-coil forms retain at least 98.2 mm certified plasma clearance, required 80 mm | Magnetic-field quality or full finite-build engineering |
| [Step 4](steps/STEP_4_PLASMA_AND_COILS.md) field starts | Four cells, eight normal/vector derivative checks, 20 refinements, 768 direct B/A comparisons and 252 flux gates pass numerical qualification | All four fail physical field limits: normal RMS 0.269–0.276 versus 1e-4; inner-vector RMS 0.3615–0.3723 versus 0.01 |
| [Step 4](steps/STEP_4_PLASMA_AND_COILS.md) cumulative geometry bounds | The 52-state qualification passes all required small probes and independent direct checks; 18 larger probes remain uncertified | Uncertified does not mean physically impossible; no field improvement follows from this alone |
| [Step 4A](steps/STEP_4_PLASMA_AND_COILS.md) protected-search controller | Synthetic qualification complete: 108 controller/auditor tests pass; second method review subsequently completed conditionally | Native runner and physical verification; no new protected-fit search has run |
| [Step 4A](steps/STEP_4_PLASMA_AND_COILS.md) event storage | Single-writer POSIX qualification complete: 47 storage tests, 155 with controller/auditor; exact source/artifact identities recorded | Full native source/budget orchestration, physical audit and hardware power-loss guarantees |
| [Step 4A](steps/STEP_4_PLASMA_AND_COILS.md) execution components | 390 synthetic tests and real-data source preflight pass after independently reviewed fixes; four components qualified at `47544d0` | Integrated worker and physical audit; no new field-fit result |
| [Step 4A](steps/STEP_4_PLASMA_AND_COILS.md) integrated cell | Synthetic workflow and saved-graph audit implemented; focused checks and eight historical schema comparisons pass | Committed-source full regression/final qualification, native orchestration and physical reconstruction |

Each linked step page gives the method, full limits, detailed reports and evidence.
“Independent” in these reports refers to the specified numerical/source checks,
not external peer review.

## Failures we retain

- The first plasma design and the first actual-coil pilot were rejected; see
  [Step 3](steps/STEP_3_PLASMA_TARGET.md#failures-kept-on-record) and
  [Step 4](steps/STEP_4_PLASMA_AND_COILS.md#1-first-actual-coil-pilot--all-six-designs-rejected-14-september).
- The best preserved [LPQA coil search](optimization/CURRENT_START_GN_RESULTS.md)
  reaches raw fine flux 8.129882e-8, still above its 1e-8 threshold. Its 0.754% gain
  is real within that comparison, not a feasible-design or convergence claim.
- The extended W7-X file comparison remains 60/63. The selected physics regression
  does not erase the other three differences.
- End-to-end QI/orbit qualification and valid complete mechanics remain open.
  Earlier finite-mesh checks do not certify neighboring elements/full assemblies;
  large linear-deformation outputs were outside the model's valid scope.

Detail: [validation](validation/README.md), [QI](qi/README.md),
[engineering](engineering/README.md), [research log](logbook/README.md).
Older optimistic journal conclusions do not supersede this current assessment.

## Software and release evidence

These checks show that the tools work as specified; they are not physical acceptance.

| Area | Evidence | Not established |
| --- | --- | --- |
| Public starter | 47 public tests and eight copied-tree release checks pass on local Python 3.11/3.12/3.14 at `0d9abcf`; displayed reference/candidate comparisons now use matching 512-node resolution; the unchanged 256-node native check retains its 5e-10 limit | Hosted CI, independent machines, full-surface or physical acceptance; public reports never set physical admission or Step 4 to true |
| Historical research suite | 2,619 passes, 334 warnings, zero failures/errors/skips at `47544d0`; both full console and JUnit retained | A hosted or fresh native rebuild; the strict netCDF4 import warning remains unresolved |
| Publication inventory | About 325 MB of tracked content; 365 tracked files with home-path indicators; no matches for five credential/key patterns | A complete security, privacy or rights review; no history was sanitized or published |

Details: [release evidence](validation/PUBLIC_RELEASE_RESULTS.md),
[storage qualification](optimization/PROTECTED_RUNNER_STORAGE_RESULTS.md),
[execution-component qualification](optimization/PROTECTED_RUNNER_RESULTS.md),
[review fixes](validation/PUBLIC_REVIEW_FIXES.md),
[README review resolution](review/ROOT_README_RESOLUTION.md),
[what public scores mean](validation/PUBLIC_QUICKSTART.md#what-the-report-means),
[publication inventory](validation/PUBLICATION_INVENTORY.md),
[netCDF4 warning](validation/NETCDF_IMPORT_WARNING.md).
Next launch and research steps are in the [roadmap](PROJECT_PLAN.md).
