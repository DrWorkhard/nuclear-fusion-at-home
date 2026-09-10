# Normalized feasibility continuation — preregistered 2026-09-10

Motivation: the completed unnormalized oracle pilot reproduces premature
L-BFGS-B termination at a merit near 6e-13. Keep that result unchanged. This new
experiment changes numerical scaling and increases the cap; it is not an equal
cost extension of the original experiment and must not be presented as one.

Keep the exact source coils, order-4->8 promotion, 200-point curves, 32x32
half-period target surface, currents, original regularizations and physical
thresholds of OPTIMIZATION_ORACLE_PROTOCOL.md. Use the same named-DOF backend and
all eight pinned context-scaled vector components. No component is dropped.

Before any arm, evaluate the initial full vector and Jacobian **once as shared
preparation**, record that one high-fidelity bundle and its cost, and freeze
k=1/||vector(x0)||_2. Reject a zero/nonfinite norm. Multiply the entire common
vector and Jacobian by k in every arm. This preserves the vector's zero set;
it does not establish physical equivalence of different scalar merit values.
Do not normalize each component individually or adapt k during optimization.

Run L-BFGS-B twice and pinned AL twice from exactly the same x0. Each arm's cap
is **1500 full bundles**, inclusive of the seven directional-gradient probes and
every solver request as in the original oracle protocol. Keep the original
solver options and derivative/repeat tolerances unchanged. A changed scaling
may affect line searches and stopping; record those consequences, do not adjust
options to force a desired outcome. Save the lowest common-merit completed
candidate and the full proposal/value history for every arm.

## Candidate validation after search

Reevaluate each distinct method-best candidate from its serialized field,
without supplying validation information to either optimizer. Record all
validation costs separately. At least:

- Unthresholded quadratic flux on 32x32, 64x64 and 128x128 half-period grids,
  using 200-point then 800-point coil quadrature at the finest surface. Require
  finest flux <=1e-8; finest coil/surface refinement differences must each be
  <=max(1e-10,0.01*previous flux).
- Existing independent Fourier-derivative and full-torus distance audit at
  200,1000,5000,20000 curve points. Reactor-scale unique total length <=220 m,
  maximum curvature <=1/m, minimum coil-coil centerline distance >=1.06 m and
  coil-plasma distance >=1.3 m. Report actual a0 and all refined values.
- Mean-squared-curvature and arclength-variation terms are reported from the
  common vector, but are not called independently certified by this holdout.

No retroactive tolerance on exceeding a hard threshold. A failed holdout remains
failed even if the optimizer declares convergence or returns zero penalties.
This is a **bounded geometric/flux feasibility screen**, not full engineering
admission: solid geometry, force/torque, current margins, nonlinear mechanics,
QI/free-boundary robustness and a strong multi-start baseline remain open.
Identical deterministic repeats are necessary but not multiple independent
initializations. Do not claim a SoTA result or a method ranking from this study.
