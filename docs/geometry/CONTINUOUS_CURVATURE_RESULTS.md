# Interval-wide curvature qualification — 2026-09-10

Protocol 26d9497 preceded implementation d5eac8b and all real-field enclosure
evaluations. Circle/ellipse/derivative/regularity controls pass; an additional
high-order complex-Fourier check independently verifies derivative algebra and
encloses a dense curvature reference.

At the fixed final N=12,800 grid, maximum curvature intervals (reactor 1/m) are:

| Frozen field | Sampled lower bound | Continuous upper bound | Curvature gate |
| --- | ---: | ---: | --- |
| Rejected original warm start | 0.900363383 | 0.900368293 | Pass |
| Affine L-BFGS-B best | 1.003551769 | 1.003605429 | Fail |
| Affine AL best | 1.031146018 | 1.031298949 | Fail |

The warm start passes already at N=200, with upper bound 0.947655. The affine
L-BFGS-B candidate is **unresolved**, not falsely passing, at N=200, then fails
from N=400 onward. AL fails every level. Node/midpoint witnesses and analytic
interpolation allowances cover the entire parameter interval, not only the
20,000-point grid used in the earlier holdout. All seven levels are retained.

All 16 physical copies are verified as orthogonal transforms of the four unique
bounded Fourier curves. All-level calculations for each field take approximately
0.05–0.06 s on the current host, excluding imports and deserialization.

The analytic enclosure is evaluated in ordinary double precision with padding;
it is **not** a directed-rounding interval proof. The successful original curvature
gate does not repair that field's failed flux or qualify engineering. The affine
candidates remain rejected. This closes a bounded continuum-curvature acceptance
check, not an optimization method or a feasible baseline.

Evidence: `evidence/continuous-curvature-v1.json`.
