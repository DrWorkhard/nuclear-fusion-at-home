# Spatial residual factorization: qualified, not yet an optimization claim

Date: 2026-09-11. Algebra/physical protocol d251721; implementation c436a90.
Two fixed states: original guarded warm start and stored rejected guarded TRF best.

The flux contribution to scalar merit and its exact gradient are unchanged by
replacing the single aggregated residual with 1024 spatial residuals. All seven
other common components, grids, normalization and clipping threshold are unchanged.
The real upstream cut-in is discontinuous; no derivative assertion is made there.

## Physical and algebraic qualification

- Original/guarded common-merit relative errors: 1.111e-16 / 1.499e-14.
- Common-gradient normalized errors: 1.642e-16 / 2.046e-14 (limit 1e-10).
- Independent raw-flux gradient errors <=4.847e-17; relative raw-flux errors
  <=7.493e-15. Final centered directional lifted-residual errors <=3.752e-8
  (limit 1e-6); coarse-step errors are retained, not cherry-picked.
- Effective common-Jacobian ranks at relative threshold 1e-10 change from
  2 to 171 and from 3 to 204. Same scalar function, different Gauss-Newton model.
- Independent closed-form Gram check passes for both stored fields and verifies
  the positive-semidefinite screen for the additional spatial term. Negative
  roundoff eigenvalues are retained. This is not a true-Hessian or convergence proof.
- Canonical-to-runtime DOF permutations and exact archived physical states are
  checked; the prior positional array replay defect is not reintroduced.

The first qualification used 1024 full-surface analytic VJPs per state. Additional
work per state: one original common bundle, seven field-only requests, 1024 VJPs.

## Same derivative matrix with fewer point interactions

Local-point protocol c4a3344 and implementation bf1f5f0 precede the second run.
Each sparse covector is evaluated only at its one active spatial point, explicitly
initializing the current-dependent B cache. The original field point set is
restored even on errors. Core tests exercise this ordering and forced failure.

All entries match the first Jacobian to normalized error 2.221e-16 / 1.111e-16.
All original physical identity/gradient tests pass again. Observed matrix-assembly
times change from 11.1714/11.0893 s to 1.04445/1.04880 s for the two fixed states.
These are single-run timings, not a statistical performance characterization.

The faster route adds 1024 single-point B evaluations as well as 1024 single-point
VJPs per matrix. Reporting only 'one Jacobian' would hide the extra work relative
to the original scalar oracle. Cold common-bundle timings also include setup/JIT
effects and must not be used as representative steady-state costs.

## What follows and what does not

This qualifies a mathematically controlled comparison of residual representations;
it does not demonstrate improved physical feasibility. The separately declared
128-proposal TRF pilot has equal proposal caps but **unequal computational work**.
Its independent high-resolution and continuous geometric checks remain decisive.
No SQuID-C readiness or SoTA advance follows from matrix rank alone.

Evidence: `spatial-flux-factorization-v1.json`, `spatial-flux-local-vjp-v1.json`,
`spatial-gram-check-v1.json`; all underlying matrices/fields/normals are hash-bound.
