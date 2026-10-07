# Does lower interior error restore shallow target-launched wells?

**Decision:** whether an existing low-interior-error candidate supplies a useful
shallow-well association worth testing in joint optimization. No new fit, geometry
optimization, threshold change or benefit-transfer confirmation is proposed.

Freeze two existing reference401 geometries: the #25 reference fit in
`examples/clear-coil-interior-v1/reference401-candidate.json` (SHA256
`2046cb9f0a7bdd4d0b1aabe9779ab954dfd8d6c8ffae8e62d03c5bca64e81d48`), and
pjckoch's [interior continuation](../../submissions/interior-pass-headroom-continuation/README.md)
(`candidate.json` SHA256 `521ed4e7ac5b3c0a343545287d05bd1872ed87634939b68ba2e84f9be235dfb4`).
The former's qualified interior RMS is 0.01071651709510873; require the latter's
new dense packet check to be ≤0.0021 and below one quarter of the former.
This checks the contrast; it is not a new physical gate or candidate selection.

Use the original reference401 Wout (SHA256
`83dc45b911a1e8290c3e97c7e28d4de28fcff6021b93d55df2f91d6dd3751c5e`) and committed
reference input. Keep B²=1.6293829620247962 T², signed flux
−0.03141592653589793 Wb and all seven registered bounce fields unchanged.
Normalize each shape once using the shared 256-node conversion, then freeze its
signed currents for 512-node fields. Check reference current recovery within
1e-12 relative to 307977.14904565935 A; preserve native mapping checks.
Require native/scalar continuation currents to agree within 1e-12 relative.
Check 64 fixed trace points per surface against the independent field kernel.

Reuse direct `coil_bounce.trace_coils` with rtol=1e-9, atol=1e-11, two field
periods and 16 target-PEST alpha launches on s=0.1,0.25,0.5,0.75,0.9. Trace once
at 1,601 points; take every second point for the nested 801-point diagnostic.
This is sampling/action refinement, not ODE convergence. Use the same ideal
traces as launch definitions and domain controls; every ideal pitch/surface
cell must have all required wells at both grids. No failed cell is discarded.

Retain each full trace, every pitch's cell result, failed-line well counts,
censoring/period crossings and each period's minimum B−Bbounce. Classify only the
two existing scientific failure messages (missing/extra/censored wells or period
crossing) after validating trace shape, finiteness and monotone arc length.
Malformed traces, solver failures or unexpected exceptions are inconclusive.

Before interpreting improvement, reference failed cells must be exactly
{(s=0.1,q=0.03),(s=0.25,q=0.03)} at both grids. Both arms' failed-cell masks must
be stable. On every successful cell, every alpha and both period families,
require max |J1601/J801−1| ≤1e-3. A **promising shallow-well association** requires
the interior contrast, restoration of both core cells and no new failed cells
relative to reference at either grid. Stable, numerically qualified failure to
restore them means **lower interior error was insufficient for this candidate**.
Other cases are inconclusive. Partial changes remain visible without promotion.

One attempt, 900 s total including imports/intake/dense check/diagnostics/IO,
one native thread, 64 MiB output, 3 GiB initial / 2 GiB live disk reserve and
5 s wall/monotonic agreement. Freeze code and external input hashes before running;
check clean source and unchanged inputs before/after. Retain timeouts and failures.
No automatic extension, extra seed, larger grid or gate relaxation.

These are two existing geometries with different optimization histories. The
comparison cannot establish causality, common realized-flux coordinates, islands,
transport, confinement or benefit transfer. It does not close #26 or #48.
All existing field/geometry gates remain. Agent review is not external peer review.
