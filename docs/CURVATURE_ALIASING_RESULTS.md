# Off-grid curvature violations independently confirmed

Retrospective witness protocol and tested implementation e9fde75 preceded this
check of both frozen affine candidates. Three analytical test groups cover the
position-only method. The earlier independent Fourier-derivative holdout is
unchanged; no candidate is repaired or reoptimized.

SIMSOPT's compiled curvature reproduces both the 200-point and 20,000-point
holdout maxima within the declared 1e-10 relative tolerance. At the fine-grid
witness (zero-based unique coil index 2 for each), three-point circumcircle
curvature independently confirms the violation from positions alone:

| Candidate | Witness t | Compiled curvature, reactor 1/m | Position-only h=1e-5 | Position-only h=3e-6 |
| --- | ---: | ---: | ---: | ---: |
| L-BFGS-B | 0.17845 | 1.00355069 | 1.00355028 | 1.00354632 |
| AL | 0.17175 | 1.03114211 | 1.03114164 | 1.03113769 |

Both final step estimates exceed 1/m and agree with compiled local curvature
within relative 4.36e-6, below the declared 1e-4 tolerance. All six step sizes and
their exact coordinates are recorded. Error is not monotone at the smallest h:
the finer position subtraction is more affected by roundoff. No step was removed.

This provides violating points, not a rigorous global maximum or a feasible-design
certificate. The coarse-grid zero penalty misses narrow curvature peaks between
nodes. More effective optimization has exposed a discretization weakness that
must be controlled in future searches; changing the acceptance threshold would
hide it rather than establish feasibility.

Evidence: `evidence/affine-feasibility-v1-curvature-witnesses.json`.
