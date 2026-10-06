# Saved-contour quadrature method check

**Prospective exploratory question:** is the remaining launch-matching failure
caused by uniform angular quadrature missing features between uneven spline knots?
The decision is whether integration over individual spline intervals is suitable
for a future label estimator. The [stopped matching pilot](ISSUE48_MATCHED_LAUNCHES.md)
remains inconclusive regardless of this separate diagnostic.

Use only the final 640-crossing theta=0 contour from each round 2 arm: selected is
the failed case and reference the qualified control. Freeze raw hits, snapshots,
center and edge-flux denominator by hashes. No tracing, coil/current change,
launch correction, alternate contour or threshold change is permitted.

Integrate each periodic cubic-spline interval with Gauss-Legendre orders 4 and 8.
Compare A line integrals and B radial-fan integrals (24 radial nodes), plus the
existing uniform 4096/8192 results. For the finest interval line integral, recompute
A with the independent NumPy filament implementation at the same 512 coil nodes.
Use analytic uniform-field circle controls and exact polynomial integration of
half the squared spline radius as a separate area control, including irregular
knots. Require circle error below 1e-10; same-spline area agreement below 1e-10;
normalized interval-order/Stokes differences below 1e-5; independent normalized
line-integral difference below 1e-10. Preserve any failures and stop after this pair.

One thread, 600 s total (660 s supervisor), 256 MiB retained output, 3 GiB initial / 2 GiB
live disk reserve. Record source/input hashes, environment, timings and all values.
This assesses quadrature of one chosen spline, not whether the trajectory defines
an invariant surface. No reclassification of the original pilot or action benefit
claim follows, even if interval quadrature passes. Archive the small result and
one short conclusion before any future use in a launch-matching protocol.
