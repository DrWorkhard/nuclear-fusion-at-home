# Prospective bounded-step local periodic-return test

Decision: can a trust-region method resolve the same local eleven-period orbit
without leaving the original neighborhood? The archived Newton search stopped at
its first oversized proposal; explicit derivatives changed its magnitude but still
proposed leaving. A bounded-step method can reduce a step before accepting a trial.
This motivates one new solver attempt, not a wider domain, alternative seed or
revision to the completed studies. No success or topology is presumed.

Reuse the exact trace-refinement archive manifest/snapshot/seed inputs from
`d12b01bedbb3d4e89ab891d03a9e6048f0690918`, seed mean of its first eleven-residue
phi=0 sequence. Use unchanged eleven-period direct maps and numerical settings:
512 nodes, DOP853 rtol/atol=1e-10/1e-12; independently restart from the same seed
at 1024 nodes, 1e-11/1e-13. Maximum integration step remains pi/100.

Use SciPy `least_squares(method='trf', tr_solver='exact', loss='linear')` with
u=(RZ-seed)/0.01 and residual (P^11(RZ)-RZ)/0.01. Bounds u in [-1,1] only constrain
the solver's box; the original **Euclidean 10 mm guard** applies before every
field-map evaluation, including derivative probes. A disk violation stops and
preserves the attempt; box corners do not enlarge the physical neighborhood.
Supply central residual derivatives at fixed 5 micrometres in named R/Z. The
identical coordinate/residual scaling cancels in the Jacobian. Set x_scale=1,
ftol=xtol=1e-11, gtol=1e-12; retain SciPy's default 100*n residual-evaluation limit
(200 here, excluding derivative evaluations). Record solver status and all trials.
The wall-clock limit remains the primary computation bound. See the
[SciPy method documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html).

Optimization and qualification stay separate. Reevaluate the final return residual;
require solver success and residual <=1e-9 m, then unchanged one-period separation
>1 mm, root refinement agreement <=1e-7 m, and independent B error <=1e-12 at the
12 orbit points. Only at qualified roots compute full map matrices with 10/5 um
steps and reuse the archived trace/determinant classification. A nonzero minimum,
budget stop or neighborhood violation is inconclusive, not evidence of root absence.
Even a qualified local orbit would not locate an island boundary, qualify a contour,
prove nonlinear stability or change the continuation's original 19/20 verdict.

One attempt, no numerical retuning/retries: 300 s inside the driver after imports,
330 s outer supervision, one thread, 256 MiB, 3/2 GiB reserves, 5 s clock discrepancy.
Preserve all raw trials and partial results; use unchanged owned-process cleanup
and source/environment identity checks. Tests cover a known affine root, a nonzero
minimum with optimizer success, and exclusion of outside-neighborhood field calls.
Freeze and adversarially review before running; review the final evidence before
local integration. This is exploratory, same-machine work; publication is pending.
