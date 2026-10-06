# Saved-contour quadrature diagnosis

**The two fixed-spline method checks pass.** Uniform angular quadrature was
insufficiently converged for the selected theta=0 interpolant; integrating each
spline interval gives mutually consistent line and area flux. This diagnoses a
numerical integration problem, not physical mismatch. The
[stopped matching pilot](ISSUE48_MATCHED_LAUNCHES.md) remains inconclusive.

| Estimated normalized flux | Reference theta=0 | Improved-target theta=0 |
| --- | ---: | ---: |
| Uniform 4096 angular points | 0.749961416274 | 0.749965051128 |
| Uniform 8192 angular points | 0.749961426188 | 0.749922512444 |
| Interval Gauss order 8 | 0.749961428845 | 0.749920710869 |

The selected spline's minimum knot gap is 2.12e-5 rad, versus 7.67e-4 rad uniform
spacing at 8192 points. Interval orders 4/8 agree within 4.09e-15 normalized flux;
finest A-line/B-fan and independent NumPy filament line-integral discrepancies
are each at most 3.32e-16. These observed agreements are not bounds on every error.

## Frozen method and limits

Use only the two final 640-crossing theta=0 contours from matching round 2, with
unchanged raw hits, snapshots, center and edge denominator. Integrate each cubic
spline interval with Gauss orders 4/8 and the radial fan with 24 nodes. Analytic
uniform-field circles and exact polynomial integration of half the squared spline
radius provide controls with irregular knots. Controls pass 1e-10; required
normalized order/Stokes agreement is 1e-5, independent line agreement 1e-10.
The independent calculation uses the same frozen 512-node coil discretization.

The clean producer `34d0a013546b2f76adcfd8ce6122f62399f0392c` completed both cases in
13.63 s, inside the 600 s / 256 MiB cap and 660 s supervisor, one thread, with 3 GiB initial/
2 GiB live reserve. The prospective method is committed at `3354fadb`; its first
attempt failed analytic-control JSON serialization before either native coil case.
That failure remains archived; the producer fixes scalar serialization and adds
its regression without changing numerical rules. Input/source hashes are stable.

## Evidence and next use

Prepared local archive `evidence-issue48-knot-quadrature-v1`, commit
[`c7623cb`](https://github.com/DrWorkhard/nuclear-fusion-at-home/commit/c7623cbbade5b031562cc3d1b1df0ec7ccbd16bb).
Publication is pending. The archive includes reports, controls, failure, commands,
hashes and the exact source tree. Its README reproduces the pair using the
[matching archive](ISSUE48_MATCHED_LAUNCHES.md), without original Wouts or tracing.
[Driver](../../scripts/diagnose_flux_quadrature.py) ·
[Integration](../../src/fusion_baselines/flux_labels.py).

This qualifies quadrature of two chosen interpolants. Other phases, prefixes and
alternating subsets remain untested by the new method. A future estimator must
reapply all reconstruction checks under a separately declared protocol; no
retrospective pass, nesting, equal-alpha action benefit or physical admission follows.
