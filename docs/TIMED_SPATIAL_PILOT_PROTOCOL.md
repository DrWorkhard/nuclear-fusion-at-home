# Equal-wall-time scalar versus batched-spatial TRF study — 2026-09-11

Declared after batched fixed-state qualification, before timed search. Original
guarded problem, normalization, starting physical state, solver settings and
acceptance limits remain unchanged. No warm start from an improved candidate.

Each representation receives **300 monotonic wall-clock seconds**, twice, in
fixed order scalar-1, scalar-2, batched-1, batched-2. One original common bundle
and one batched matrix at x0 are shared, recorded warmup outside the per-arm clocks.
Timers include the seven original seed-42 gradient probes, optimizer work, cache
requests and checkpoint writing. Preparation and final artifact serialization
are excluded. No parallel heavy benchmark is run during this timing study.

Time is checked before every oracle request, including exact-point cache hits.
An in-flight operation is not interrupted: record actual stop time and overrun,
never assert exact 300 s execution. A separate 300,000-proposal safety cap remains.
Use the existing runner with its oracle class replaced only inside a scoped
local dependency-injection context; do not edit pinned external packages.

Equal time means proposal counts can differ between repeats. Require identical
physical proposal hashes and residual values (rtol=1e-12, atol=1e-14) over each
pair's entire common prefix, identical stop reason (time, unless solver converges),
and passing initial gradient screens. Report both counts and all differences;
do not mislabel unequal terminal counts as exact trajectory reproduction.

Spatial flux uses the qualified batched Jacobian. Check original versus lifted
merit/gradient at every proposal to 1e-10, and projected field versus pinned B.
Count all coil contractions, geometry derivative requests, current VJPs and
original common bundles. Failed requests stop the arm and remain recorded.

After both pairs pass, independently audit ledgers and saved named array/field
identity. Evaluate **all four** serialized best candidates with unchanged flux,
geometry, continuous curvature and inter-coil checks. A solver success flag or
lower merit never replaces physical acceptance. No holdout feedback in these runs.

This is a two-repeat, one-start local timing comparison, not multi-start SoTA,
statistical hardware characterization, or engineering/SQuID-C certification.
Do not extend a run's deadline or change a limit after observing its result.
