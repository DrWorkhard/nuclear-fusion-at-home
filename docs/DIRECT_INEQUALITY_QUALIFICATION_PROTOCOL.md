# Direct smooth-inequality baseline qualification — 2026-09-11

Next-stage qualification only; no optimization is authorized by this protocol.
It does not modify the ongoing timed scalar/spatial experiment. Motivation:
the common oracle deliberately squares components that already include squared
penalties. Correct gradients do not guarantee this is an effective feasibility
formulation. A direct-inequality solver would be a new construction problem,
not another objective-equivalent residual representation.

Keep order 8, four unique/sixteen physical coils, original fixed target surface,
currents/regularizations, field quadrature 200, curvature curves 1600 and all
existing physical acceptance limits. Minimize unthresholded raw quadratic flux
with explicit inequalities, rather than pretending a small penalty is feasibility.
Search is deferred until the following measurements and gradients are qualified.

For finite samples x define stable, unnormalized log-sum-exp bounds

    upper_beta(x) = max(x) + log(sum(exp(beta*(x-max(x)))))/beta,
    lower_beta(x) = -upper_beta(-x).

They satisfy max(x)<=upper<=max(x)+log(n)/beta and
min(x)-log(n)/beta<=lower<=min(x). Dividing the exponential sum by n would lose
the required bound and is forbidden. These bound sampled extrema only, not the
continuous curves or surface.

Planned inequalities (nonnegative means passing):

- Unique length: 1-L_reactor/219.9, using original CurveLength quadrature.
- Four curvature bounds: 1-upper_512(kappa_reactor)/0.99 at 1600 points/curve.
- 120 inter-coil pairs: lower_512(reactor distance squared)/(1.10^2)-1,
  over every 200x200 node pair. Squared distances avoid a derivative singularity
  at coincident points; no distance regularization or sample pruning.
- Four unique coil/plasma bounds: lower_512(distance squared)/(1.3^2)-1,
  200 coil points against a fixed 64x64 full-torus target surface.
- Four native mean-squared-curvature and four arclength-variation inequalities
  using the pinned native thresholds and raw metric definitions, not their
  already-squared penalties. Linking number stays a separately required zero
  admission check, not a fictitious differentiable inequality.

Core controls must prove the finite-sample bounds, derivative weights, constant
offset, translation/scaling/permutation behavior, squared-distance gradients and
malformed/nonfinite rejection. Physically qualify the original promoted warm start
and the frozen 128-proposal spatial best (never the running timed candidate).
Require raw metric agreement with native objects and full directional-gradient
checks (seed 46; eps=1e-5,1e-6,1e-7,1e-8; finest normalized error <=1e-6).
Record each raw minimum/maximum, conservative bound, margin, work and all steps.
Any failure remains failed; do not tune tolerances after seeing it.

Only after qualification may a separately frozen SLSQP or other constrained
construction be run. Existing high-resolution flux/geometry and continuous
curvature/inter-coil holdouts are unchanged and remain mandatory. All native
additional constraints must also be checked before any feasible-baseline claim.
