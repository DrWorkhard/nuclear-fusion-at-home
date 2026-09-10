# Fixed affine-coordinate feasibility experiment v1

Preregistered 2026-09-10 after the failed normalized study, before new evaluations.

## Hypothesis

Normalized L-BFGS-B proposed merit 1.38e18 then returned exactly to x0 and
terminated. The physical coordinate step and severe nonlinear penalties may
contribute. Test a fixed smaller coordinate scale; this experiment cannot identify
a unique cause or establish general method superiority.

Keep the entire NORMALIZED_FEASIBILITY_PROTOCOL.md problem and acceptance tests:
same tracked rejected warm-start fixture, promotion, currents, regularizations,
surface, eight-component common vector, one shared normalization bundle, 1500
full-bundle cap per arm, solver options and physical gradient probes. No constraint
or objective is relaxed. Do not restart from the previous AL best.

For both solvers use y=(x-x0)/0.01, hence x=x0+0.01*y and d/dy=0.01*d/dx.
The scalar 0.01 is fixed here, not fitted after seeing this run. Both start at y=0.
This is a bijective coordinate change, not a new geometry or component weighting;
it can change finite-budget solver behavior and stopping criteria. The factor
also changes the meaning of the unchanged numerical gtol in solver coordinates.

The existing full-bundle oracle continues to evaluate, cache, hash and select in
physical x coordinates. Its seven physical-space gradient probes are unchanged
and included in each arm's cap; analytical affine-chain-rule tests independently
validate the coordinate adapter. No hidden extra backend calls are permitted.
Save physical best x and serialized fields, not y interpreted as physical DOFs.
Both methods repeat twice. Require original repeat tolerances and identical
physical proposal histories/counters within each pair. Any failed derivative
screen or solver exception fails qualification; retain evidence without overwrite.

After search, run the unchanged independent normalized-candidate holdout on both
method-best fields. Its grids and thresholds are known from prior experiments;
this is a frozen post-search check, not a previously unseen validation set. No
holdout feedback enters this run. Actual consumed budgets must be reported;
common caps alone do not establish equal work. Improvement in an infeasible merit
does not count as a feasible design improvement or SoTA result.

Predeclared report: bundle counts and solver termination; best physical common
merit and whether it is a probe or solver proposal; flux/length/curvature/distances
and every failed acceptance test. Original normalized evidence stays unchanged.
