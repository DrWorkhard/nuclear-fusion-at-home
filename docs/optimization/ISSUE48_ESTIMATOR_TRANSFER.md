# Interval-estimator transfer to the frozen matched launches

Prospective method check; no new result yet. The [two-contour diagnosis](ISSUE48_KNOT_QUADRATURE.md)
resolved uniform-grid integration error for two chosen splines. The decision now
is whether its numerical estimator works on **all** saved round-2 launches, or
whether reconstruction still requires new tracing. This is a new exploratory
method assessment, not a retrospective pass for the stopped matching pilot.

## Inputs and bounded calculation

Use matching archive `896180e939b0234aea29ab33621a73aad6c5d20a`, manifest SHA256
`6b35f5634e7fea8f5a353bbaaad7fd367eed63d5378917caa883ef4a6c9494ab`.
Pin both frozen snapshots, all ten raw traces and original reports. Keep the
recorded centers, currents, 512-node coil discretization and edge denominators.
No launch moves, secants, optimizer calls or retracing. Original Wouts and target
inputs are hash-bound by `coil_check.TARGETS`; they remain maintainer-local.

For each five-line arm, exclude launch events, order pooled phi=0/pi crossings by
time and recompute prefixes of 160/320/640 crossings. Require the recorded symmetry
check and trace completion. Integrate the periodic polar spline on each interval
using Gauss orders 4/8 and 24 radial fan nodes. Recompute both disjoint alternating
subsets, including their separate order convergence and held-out radial residuals.
Compute an independent NumPy A-line sum for every full prefix. Retain any failed
prefix/subset; no failed line disappears from the denominator.

Recheck the edge denominator using 2048 target-contour knots and interval order 8.
Reconstruct the original s=0.25/0.75 target controls with the identical seeded
160-point sample; compare each to its dense 2048-knot interval integral. Reuse the
analytic uniform-field circle and polynomial-spline-area controls. These control
surfaces are numerical checks, not evidence of realized invariant surfaces.
Save their dense contours and sampled indices so numerical control replay does not
require the local Wouts; rebuilding those contours still does.

One paired run: **600 s / 256 MiB**, one native thread, 3 GiB initial / 2 GiB live
reserve, external 660 s supervisor. Include input checks and all controls. Record
both monotonic elapsed time and UTC timestamps; avoid agent-controlled overlapping
heavy jobs and make no controlled-throughput claim. On failure, retain outputs;
no extension or numerical retry within this protocol.

## Frozen gates and interpretation

All three prefixes must be calculable. Reapply the original final-prefix gates:
320 turns / 640 crossings, last-two-prefix label change below 5e-4, angular gap
below 0.4 rad, alternating-subset label spread below 5e-4, held-out radial error
below 0.1 mm, order/Stokes discrepancies below 1e-5 normalized flux. Additionally
require each final subset's order convergence below 1e-5 and final independent
line agreement below 1e-10. The four moved launches must each lie within 5e-4 of
0.75; the unchanged s=0.25 control is not forced to that label.

Require target-control label errors below 5e-4, edge change and edge Stokes below
1e-5 normalized flux, and both analytic controls below 1e-10. Both five-line arms
must pass before calling the pair **numerically qualified under this estimator**.
Software completion and numerical qualification are recorded separately.

Pass: no further retracing is justified solely by the old quadrature failure;
proceed to the still-unqualified common flux/straight-field-line phase mapping.
Fail: identify the failed reconstruction/label checks; do not repeat integration
to manufacture a pass. An interrupted calculation is inconclusive. Neither outcome
proves nesting, island absence, equal PEST alpha, confinement, benefit transfer or
physical acceptance. Symmetry pooling can mix island components. Original studies
retain their original producers and verdicts.

Run [the driver](../../scripts/qualify_saved_flux_labels.py) with `--archive` pointing
to the matching payload, `--native-inputs` to a root containing the exact original
Wouts/target JSON paths, and a fresh `--output`. Source and input hashes are saved
before and after; final evidence will identify the exact committed producer.
