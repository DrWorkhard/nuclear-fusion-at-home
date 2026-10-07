# Prospective flux-label grid for the interior continuation

**Decision:** whether the candidate that recovered the shallow core wells in the
[#26 comparison](ISSUE26_INTERIOR_WELLS.md) supplies a numerically qualified nominal
flux-label grid for later launch matching. The new candidate result is the reason
to reuse the completed #48 estimator. No fit, optimization, adaptive tracing,
threshold change or revision of the original #25 results is proposed.

Freeze the exact #26 continuation snapshot, SHA256
`73972fc86375fcffa67a44833d1c87016e7ff9d070857aac97acc1dcf335bb97`, from local
archive `2205e4dfd2716028e04682f738346a1e4ea925ac`,
`evidence/issue26-shallow-wells-v1/raw/run/continuation-snapshot.json`.
It represents pjckoch's public `interior-pass-headroom-continuation/candidate.json`
(SHA256 `521ed4e7ac5b3c0a343545287d05bd1872ed87634939b68ba2e84f9be235dfb4`),
with frozen maximum absolute current 305178.2427715842 A. Use the original
reference401 Wout SHA256
`83dc45b911a1e8290c3e97c7e28d4de28fcff6021b93d55df2f91d6dd3751c5e`, committed
reference input and target flux −0.03141592653589793 Wb. No regenerated Wout.
The Wout remains external; snapshot and code will accompany this study's archive.

Reuse the estimator, analytic controls, independent A-line check and qualification
from prior #48 archive `2ee186bb347245072c98d983a42b06f8e02a16a9` unchanged.
The shared coil intake, curve mapping and tracing helpers are byte-identical;
the fitter's later optimizer compatibility change is outside this measurement.
Unused historical helper commands are omitted; their estimator/control functions
are unchanged. The driver changes the frozen identity, protocol binding, study
restriction/labels and reserves 1 MiB for supervision. Commit before execution.

Run one reference-target arm at all 20 nominal launches: s=0.1,0.25,0.5,0.75,0.9,
with geometric theta=0,pi/2,pi,3pi/2 at phi=0. Use direct 512-node fields, tol=1e-10,
tmax=4800 and a 321-transit stop. Pool phi=0/pi crossings only after field/potential
half-period covariance and axis checks within 1e-12. Keep prefixes of 160/320/640
crossings, alternating subsets, interval Gauss orders 4/8 and 24 radial nodes.

Require at least 320 transits and 640 crossings; final-prefix and subset label
changes <5e-4, maximum angular gap <0.4 rad, held-out radius error <1e-4 m,
full/subset quadrature changes <1e-5, full-contour relative Stokes error <1e-5 and
independent A-line label error <1e-10. Every analytic control must pass; dense
sampled-target reconstruction error <5e-4, edge Stokes error <1e-5, original
Fourier flux error <1e-6 and polar-edge magnitude error <1e-5. Separate-plane
checks remain diagnostic, not new gates. Nominal-label equality is not required.

One attempt, 1,800 s total including imports, intake and all diagnostics; one native
thread, 256 MiB aggregate output including logs/receipts, 3/2 GiB initial/live disk
reserve and 5 s wall/monotonic agreement. An outer supervisor enforces these limits,
checks exact clean source and frozen input/environment identities before/after,
and preserves incomplete outputs. Prior full-grid arms took about 990 s; this
budget is feasible without changing grid coverage. No retries or extensions.

A surface gets qualified offset/spread statistics only if all four phases and
controls pass. Preserve every point and failure. Only a complete qualified 20-point
grid supports later common-label launch search; any failure directs a bounded
reconstruction diagnosis first. Offsets and phase spreads are descriptive, not
new physical gates. Archived #25 reference labels provide context, not a rerun.

Geometric theta is not PEST alpha. Spline/pooling assumptions do not prove a
single nested surface, island absence, confinement, common action coordinates,
continuum-filament convergence or benefit transfer. This does not close #48.
Agent review is not external peer review. Full evidence stays in a separate local
archive; publication requires separate authority.
