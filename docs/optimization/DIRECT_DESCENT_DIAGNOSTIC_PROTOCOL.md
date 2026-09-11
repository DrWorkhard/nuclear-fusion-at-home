# Bounded linearized-descent diagnostic — 2026-09-11

Retrospective diagnostic after the completed direct SLSQP pilot, before these
new probes. The pilot is not extended or reselected. Use the original promoted
state and the immutable selected proposal 119 from repeat 1. Reconstruct via
explicit physical-coil/current owner mapping and verify their entire 138-row
vectors against the pilot records to normalized 1e-10.

Motivation: the 256-bundle stop is not convergence. Before spending a larger
budget, test whether the selected point's local model still permits descent while
restoring its tiny internal violation. Also record the actual parameter/current
scaling; never infer amperes from names such as Current:x0. A prior read-only
inspection of the already saved original Jacobian found current and geometry
block norms about 61.8 and 75.7, respectively, and underlying current parameters
about 0.02–0.04. This does not support the speculation that uniform 0.01 scaling
freezes unscaled megaampere current variables.

First qualify the selected state's full directional derivative using seed 47
and eps=1e-5,1e-6,1e-7,1e-8; finest normalized error <=1e-6, all rows/steps retained.
If either replay or this derivative screen fails, do not execute descent probes.

For each state solve three small linear model problems, rho=1e-4,1e-3,1e-2,
in the unchanged y coordinates (physical displacement=0.01*p):

    minimize (0.01 grad f)^T p
    subject to g + 0.01 Dg p >= 0,  -rho <= p_i <= rho.

Use all 137 inequalities, no after-the-fact active-set selection or row removal.
SciPy linprog with method highs-ds, presolve enabled, primal/dual feasibility
tolerances 1e-9, time_limit=30 seconds per model. First solve an analytic 2D
control with known solution. Record solver status and validate primal inequalities
and box bounds independently to 1e-8. Infeasible or failed model solves are
retained, not silently interpreted as stationarity or as valid physical steps.

For every valid model solution evaluate its full nonlinear values once, without
an iterative line search or repair. Save every probe's physical array and vector.
Report predicted/actual objective change, full nonlinear constraint margins and
the departure from the linear model. A predicted descent direction does not prove
nonlinear feasibility; these are diagnostic probes, not independently admitted
design candidates. No holdout threshold changes, optimization ranking, convergence
certificate or SoTA claim. Any follow-up search needs a new frozen protocol.
