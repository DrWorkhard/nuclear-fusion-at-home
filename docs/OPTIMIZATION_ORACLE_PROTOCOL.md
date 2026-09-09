# Common budgeted coil oracle — qualification protocol, 2026-09-09

This is a counting/gradient/determinism qualification, NOT a method ranking or
claim of feasible design. Preregister before new real-coil evaluations.

## Shared setup

Start from the serialized LPQA v1.1 L-BFGS-B field (SHA-256
7ae1b1968b8ca34fa94cc0e67cfad41577219ed43bcd902b695c7b7cc04ecd2e).
Preserve currents and coil geometry while zero-padding the four unique Fourier
curves from order 4 to order 8, using 200 points per curve and the original
nfp=2 stellarator symmetries. Check promoted field against source at the first
64 points of the common 32x32 half-period target grid: max relative vector-field
difference <=1e-10 (normalize by max source |B|).

Use the pinned StellCoilBench LPQA v1.1 terms and reactor-scale thresholds,
including buffered centerline clearance 1.1 m. Capture its constructed context
before optimization; no external source modification. Reuse this identical
prepared problem for both arms. Record the shared preparation wall time and its
field-equivalence check separately from optimization, as allowed by the method
protocol. This is not an exact rerun of either complete upstream optimization
wrapper: the two arms share a new explicitly defined oracle.

## Oracle and stopping rule

One high-fidelity evaluation = the **whole** vector of current constraint/flux
values and its full analytic Jacobian at one x. Map local gradient columns by
unique named degrees of freedom, never by silently padding/truncating arrays.
Use pinned context.constraint_scaling for every vector component (default 1).
Both arms see the same vector and Jacobian, with no method-specific weights.
These components include upstream nonnegative penalties and thresholded flux;
the norm of this vector is not by itself a physical feasibility certificate.

Cache only the most recent successfully evaluated exact float64 x. Repeated
value/Jacobian requests at the cached x cost zero additional bundles. Changing
away and back recomputes and costs another bundle. Count failed attempts, all
Taylor probes, line-search proposals, initialization within the solver, and
post-step requests. Never call the backend after the cap is reached. Record
request/cache/attempt counts, input hashes, success/error, wall time and every
completed vector. Best candidate means minimum 0.5*||vector||^2 among completed
bundles, not last mutated solver state. Save that candidate without reevaluation;
later validation has a separately declared cost and cannot feed back into search.

## Qualification runs

Run four arms: L-BFGS-B twice and pinned SIMSOPT augmented Lagrangian twice,
each from identical x0 with a **150-bundle cap**. Before each arm's solver, charge
a central finite-difference gradient check to that same cap: x0 and +/-eps*h,
eps=[1e-4,1e-5,1e-6], h a normalized seed-42 normal direction. Finest componentwise
directional derivative error <=1e-6*max(1,abs(analytic derivative)); record all
three resolutions and abort this qualification on failure, retaining evidence.
This is a bounded derivative screen; nonsmooth threshold crossings are not waived.

L-BFGS-B minimizes 0.5*||vector||^2, analytic gradient Jacobian.T@vector,
maxiter=10000, maxls=40, maxcor=30, ftol=1e-15, gtol=1e-15. AL uses the pinned
implementation with zero primary objective, common vector equality constraints,
MAXITER=100, MAXITER_lag=20, mu_init=10, verbose=False and its pinned seed-1
multiplier initialization. Internal stops may return before the cap; never
pad counts or call unlike budgets equal. Report stop reasons independently of
upstream success flags. The cap is a controlled common maximum.

Identical repeats must have the same attempted-x hashes and constraint vectors
within rtol=1e-12, atol=1e-14, and the same stop status/counters. This is one warm
start, not the multiple-initialization comparison required for a method ranking.

Before real runs test exact stop/no overshoot, cache behavior, failed evaluation
accounting, invalid/nonfinite outputs, defensive copies, and complete gradient
column mapping (including deliberately permuted local names). Store raw best x,
serialized field and provenance with hashes; refuse overwrite. Freeze and commit
the implementation before real-coil execution. Feasibility at refined geometry,
actual high-budget convergence, physical force/stress/current bounds, and robust
Pareto comparisons remain separate gates regardless of this pilot's outcome.
