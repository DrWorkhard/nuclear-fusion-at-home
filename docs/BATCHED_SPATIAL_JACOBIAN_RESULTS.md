# Batched spatial Jacobian: qualified analytic acceleration — 2026-09-11

Protocol 4544385, implementation 44e3435. First report serialization failed;
the raw first-state matrix remains and is not counted as a complete qualification.
The Python-bool reporting correction d6694f5 precedes the full successful retry.
No numerical formula or tolerance was changed. See BATCHED_QUALIFICATION_FAILURE.md.

## Method and independent checks

The batched implementation analytically differentiates the same ideal-filament
quadrature and contracts per-coil position/tangent sensitivities with the complete
Fourier geometry derivatives. It includes all sixteen physical coils and their
dependent-current derivatives in the explicit global free-DOF basis. It does not
insert finite-build regularization into the surface field or support passive arrays.

Analytic circle-axis field/radius derivative, direct cross-product quadrature,
arbitrary geometry perturbations, dependent current sums/shared geometry/global
DOF order, and singular/nonfinite-input controls pass.

Both fixed physical states pass all original residual/Jacobian/directional
criteria. Compared to the previously qualified single-point VJP reference:

| Metric | Original state | Guarded rejected candidate |
| --- | ---: | ---: |
| Max normalized Jacobian discrepancy | 8.882e-16 | 8.050e-16 |
| Max weighted-field projection discrepancy | 5.009e-17 | 4.576e-17 |
| Relative raw-flux discrepancy | 2.505e-15 | 3.247e-14 |
| Max common-gradient identity error | 1.642e-16 | 2.052e-14 |
| Assembly seconds, all three repeats | 0.31769 / 0.30391 / 0.31236 | 0.32477 / 0.32073 / 0.33655 |

Each state's three matrices and projections are identical across repetitions.
Field evaluation points are unchanged. The candidate's archived coil geometry,
currents and regularizations still match exactly after explicit DOF mapping.
The evidence's inherited `local_vs_full_vjp_error` key here refers to the
batched-versus-local reference named by `reference_qualification`.

Each matrix needs sixteen per-coil contractions, 32 geometry derivative requests
and sixteen current VJPs, with no pointwise B/VJP calls. The qualification performs
three matrices per state; all 48 contractions/96 geometry requests/48 current
VJPs per state are recorded, not counted as a single evaluation. Additional common
bundles and field-only directional checks remain explicit.

## Consequence

Observed assembly time is about 0.3 s, versus about 1.05 s for the qualified
single-point implementation and 11.1 s for the initial full-point implementation.
These fixed-state timings do not establish a statistically general speedup or
improved coil quality. A separately declared 300-second-per-arm study compares
scalar and batched-spatial residuals under equal wall-clock budgets.

The physical problem, weights, clipping and hard acceptance limits remain the
same. This is a derivative implementation improvement, not a feasible-design,
novel-method, SoTA or SQuID-C readiness claim.

Evidence: `spatial-flux-batched-v1-retry1.json`; first-attempt raw data and all
successful state matrices are retained and hash-bound.
