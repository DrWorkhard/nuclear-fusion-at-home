# Prospective full nominal launch grid for issue #48

**Question:** how large are realized enclosed-flux offsets and geometric-phase
spreads across both original frozen issue #25 fits? The successful
[saved-contour transfer](ISSUE48_ESTIMATOR_TRANSFER.md) covers one adjusted surface
and a control. This new study measures the full issue #48 nominal grid, without
optimization or launch matching. It can decide whether subsequent common-surface
work needs label matching throughout the domain or first needs a reconstruction
diagnosis at specific failed points. It cannot measure plasma-benefit transfer.

## Frozen inputs and single measurement

Use the original reference401 and selected401 issue #25 snapshots and original
401-surface Wouts, with the SHA-256 identities enforced by
[`measure_flux_labels.py`](../../scripts/measure_flux_labels.py) and the shared
target intake. Currents, target flux, coils and targets remain frozen. These Wouts
are maintainer-local, not included in a normal checkout. Explicit `--target-input`
accepts only the original hash-bound target JSON. No regenerated Wout substitution.

Each arm launches once at all 20 points: nominal VMEC s = 0.1, 0.25, 0.5, 0.75, 0.9
and geometric theta = 0, pi/2, pi, 3pi/2 at phi=0, in that order. Launch scales are
one. Use direct 512-node Biot-Savart, tolerance 1e-10, tmax=4800 and a 321-transit
stop. Verify half-period B/A covariance to 1e-12 and equal target axes before
pooling phi=0/pi crossings; retain raw paths/hits and attempted launch coordinates.

Use the existing interval estimator (Gauss orders 4/8, 24 radial nodes), prefixes
160/320/640 pooled crossings, and disjoint alternating subsets. Final qualification
requires at least 320 transits and 640 crossings, last-prefix and subset label
changes below 5e-4, maximum angular gap below 0.4 rad, held-out radial error below
1e-4 m, full/subset quadrature and relative Stokes errors below 1e-5, and independent
NumPy A-line label agreement below 1e-10. The independent calculation is required
on the final 640-crossing prefix only. There is no equality-to-nominal-label gate:
the offsets are the measurement. Preserve separate-plane diagnostics without
making them an additional gate. Analytic controls must pass; reconstruction error
on 160 seeded samples of each dense target contour must be below 5e-4, edge Stokes
error below 1e-5, original Fourier flux error below 1e-6 and polar-edge magnitude
error below 1e-5. Save dense control contours for array-only replay.

## Budget, outputs and decision

Run reference then selected serially, once each, with `--full-grid --half-period
--crossings 320 --seconds 1800`. This is a new fixed 1,800 s per-arm driver budget:
the earlier five-line traces took about 218 s before the added diagnostics, making
900 s marginal for 20 lines. Use the existing reviewed archive supervisor with
a fixed 1,860 s per-arm external limit, one native thread, 256 MiB output ceiling
per arm, and 3/2 GiB initial/live disk reserves. Include initialization and all
diagnostics. Record UTC and monotonic clocks, exact producer/input hashes and
commands; a clock discrepancy above 5 s prevents a budget-completion claim.
External host load is unverified. No retries, adaptive skipping, extra turns,
launch adjustments, relaxed thresholds or post-result budget extensions.

Retain every attempt, failure and incomplete arm. After confirmed process cleanup,
still attempt the other arm once. Software completion, numerical qualification
and physical acceptance are separate. A surface gets qualified offset/spread
statistics only when all four phases and controls pass; otherwise report its
individual observations and failures without a qualified aggregate. Report every
surface's maximum absolute offset and phase spread, flagging spreads above 0.005
as a descriptive indicator, not a new physics acceptance threshold. Original
matching-study verdicts remain unchanged. Any failed point directs the next
bounded diagnosis; a complete qualified map supports label-matching work over
the full domain. Neither outcome closes issue #48's action-comparison request.

Geometric theta is not PEST alpha. Symmetry pooling may mix island components;
spline agreement does not establish nestedness, island absence, confinement,
continuum-filament accuracy or physical acceptance. Archive the full evidence
under an immutable annotated tag; keep only this short summary on the active
branch. Agent review is not external physics validation.
