# Independent VMEC tracing cross-check — preregistered 2026-09-09

The v1 action experiment passed its integration and refinement screens. It still
relies on a shared published tracer. Before additional runs, freeze this check:

Implement a separate reader/reconstruction for stellarator-symmetric VMEC wouts.
Interpolate full-grid R/Z coefficients and half-grid lambda, B and iota linearly
in s; omit the half-grid dummy row. Solve theta+lambda(theta,phi)=alpha+iota*phi
with bounded Newton steps and verify the residual independently after solving.
Reject unsupported asymmetry, failed roots and out-of-grid interpolation.

Compute arc length from the geometry derivatives, not B/B^phi:
`theta'=(iota-lambda_phi)/(1+lambda_theta)` and
`dl/dphi=sqrt((R_phi+R_theta*theta')^2+(Z_phi+Z_theta*theta')^2+R^2)`.
Integrate with trapezoidal quadrature. The two reconstructions share source
Fourier data but have independent coordinate inversion and arc-length formulas.
Conventions can be checked in the pinned SIMSOPT vmec_diagnostics.py (commit
a79006b0bc1e6df8ab48de284e3457d39a49b995); do not execute its tracing implementation.

Before real-data execution, test a circular torus with known theta and dl/dphi.
Reject inconsistent/nonfinite input and require coordinate residual <=1e-10.

Use the immutable v1 raw traces for every nfp=1,2,3 and s=0.25,0.5,0.75 at
(nphi,nalpha,periods)=(401,16,2),(801,16,2),(1601,16,2). Retain the frozen v1
Bstar arrays and compare all five pitches. No case or pitch selection after results.

Checks for every case/surface/resolution:

- pointwise relative B difference <=1e-8;
- max absolute cumulative-length difference / max legacy length <=1e-3;
- identical per-alpha complete-well counts and every ordered-well action
  relative difference <=1e-3, plus complete-alpha coverage 100%.

These are diagnostic agreement tolerances, not proof of physical correctness.
If a difference survives refinement, report its floor and investigate VMEC
radial staggering, tracer formulas and coordinate conventions before any waiver.
Persist all failures, source/input hashes and error maxima. No thresholds will
be changed in this experiment. Shared wout errors, contour topology, branch
identity and maximum-J qualification remain outside this comparison.
