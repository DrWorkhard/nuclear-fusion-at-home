# Guarded feasibility construction v1 — 2026-09-10

Declared before new search. Purpose: seek a genuinely admissible LPQA candidate,
not isolate a single causal change or rank algorithms against previous studies.

## Fixed construction problem

Use the tracked rejected warm-start field, same order-8 promotion, four unique
coils, currents, regularizations, 200-point field quadrature and 32x32 target
surface. Keep the eight-component named-DOF oracle and affine x=x0+0.01*y.
Change only these **internal search targets**, never the acceptance limits:

- Total length search target 219.9 reactor m, acceptance <=220 m.
- Flux search cut-in 8e-9, acceptance <=1e-8 using independent unthresholded flux.
- Curvature penalty evaluated on separate 1600-point curves sharing the exact
  physical DOFs, at target 0.99 reactor 1/m; acceptance remains <=1/m and now
  additionally requires the continuous enclosure at N=12,800.
- Other vector terms and scales remain as constructed by the pinned upstream
  context; the buffered optimization coil clearance stays 1.10 m versus the
  existing 1.06 m acceptance floor.

Replace only the curvature component by the sum of the same upstream Lp (p=2)
curvature integrals on the finer curves. Bind gradients by the original base
curve DOF names, checking shared DOF identity, order and state. The field itself
keeps 200 points: finer geometry must not silently increase B evaluation cost.

The tighter length target makes the starting field infeasible even geometrically.
Recompute one shared initial full bundle and freeze normalization by its norm.
This is intentionally a changed construction problem, not equal-objective
comparison with the affine study. No previous candidate is substituted as x0.

## Solver and qualification

Run SciPy least_squares(method='trf', tr_solver='exact', loss='linear', x_scale=1)
twice from y=0. Use callable full analytic Jacobian, ftol=xtol=gtol=1e-15 and
max_nfev=100000; the independent physical oracle stops at **3000 bundles** per
run including the original seven gradient probes. Log actual work, cache hits,
best physical candidate and stop; no infeasible 'success' is accepted.

Reference for the dense exact trust-region subproblem and callable Jacobian:
[SciPy least_squares documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html).
The installed pinned SciPy 1.18.1 is the executing implementation; record source
hashes. This is a standard solver, not a claim of a novel algorithm.

Require identical repeat proposal histories/counters, values to rtol=1e-12,
atol=1e-14, and the original physical directional-gradient tolerance. Before
search, qualify the active refined-curvature gradient on both frozen violating
affine fields: sum-of-four-curves seed-43 direction, eps=1e-4,1e-5,1e-6,
finest error <=1e-6*max(1,abs(analytic)). Record its seven geometry-only requests
per field separately; do not count them as full common-vector bundles.

## Acceptance and limits

Run the existing serialized-field flux/geometry holdout unchanged, then apply
the continuous curvature and inter-coil distance enclosures. All physical
acceptance tests must pass; no boundary tolerance or grid waiver. Unresolved
continuum curvature is not passing. Both original affine failures remain intact.
Reserve choices and validation grids are known: this is a frozen post-search
check, not an unseen test set. No validation feedback enters these runs.

Even a successful bounded geometry/flux candidate would not certify mechanical
loads, finite-build self-intersection, current limits, QI, free-boundary robustness
or SQuID-C transfer, and would not constitute a SoTA advance without comparison.
