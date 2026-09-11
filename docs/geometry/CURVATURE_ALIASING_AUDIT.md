# Retrospective off-grid curvature witness check

Declared 2026-09-10 after the affine holdout showed positive curvature violations.
The optimization vector reports zero curvature penalty at 200 samples, while the
independent 20,000-point audit exceeds the 1/m reactor-scale hard limit.

For both frozen affine candidates, independently evaluate SIMSOPT's compiled
curvature on the four unique coils at 200 and 20,000 points. Require the maxima
to agree with the NumPy Fourier-derivative holdout to relative 1e-10. Freeze the
20,000-grid maximizer as a witness point (not a continuum maximum certificate).

At this point compute three positions at t-h,t,t+h, using periodic coordinates,
for h=1e-3,3e-4,1e-4,3e-5,1e-5,3e-6. Reconstruct curvature as the inverse radius
of the circumcircle: 2*|(p1-p0) cross (p2-p0)| divided by the product of its three
side lengths. This uses positions, not either derivative formula. Require the
last two estimates to agree with the compiled local curvature to relative 1e-4
and both to exceed 1/m after reactor scaling. Record all points and estimates.

Analytical tests cover circles, scaling, straight lines, repeated/nonfinite points
and the known convergence of three-point curvature on a parabola. Preserve all
prior failures. A passing audit confirms a violation witness, not a feasible
design, a directed-rounding certificate, or a global curvature maximum.

The implication for the next optimization protocol is to control curvature
between the coarse nodes (through a qualified bound or refined constraint), not
to relax the final physical limit. No optimizer is changed during this audit.
