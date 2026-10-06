# Bounded coil-freedom comparison

**Prospective; no experiment has run.** [Issue #53](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/53)
chooses the next research route after the fixed-target recipe stalled. This record
fixes the comparison before data collection; issue #52's fitter fix must first be
integrated and the final producer/protocol reviewed. No search is extended or
repeated to cross the decision threshold.

## Inputs, arms and checks

Use the original length-headroom snapshot, SHA256
`84bbdf3eca274981dfff80c967b6fd623a1a40350e583407cbb7262c26820217`, and reference401
Wout SHA256 `83dc45b911a1e8290c3e97c7e28d4de28fcff6021b93d55df2f91d6dd3751c5e`.
These remain maintainer-local at `artifacts/coil-headroom-v3/run/headroom/selected-snapshot.json`
and `artifacts/plasma-design-v2/reference-fine/wout.nc`; no substituted seed or Wout.
Target input, flux and B² normalization remain those in `coil_check.TARGETS`.

Run C then P, sequentially on the same machine with one native thread and no
competing heavy jobs. C uses six order-5 coils (198 named coefficients). P lifts
the identical seed to order 8 (306 coefficients), adding only zero modes 6–8.
No truncation is permitted. Native/independent geometry and B/A, same-seed objective,
old-mode gradients and finite differences in added modes must pass before the study.
The public candidate format remains order 5.

Each search gets 1800 s including intake/model/startup checks, followed by at most 900 s
TOTAL diagnostics: the existing fine boundary, continuous geometry, all three
interior refinements, then direct 512-node realized-field tracing of the same ten
starts for 200 turns. Use [fit_coils.py](../../scripts/fit_coils.py) with
`--seconds 1800 --check-seconds 900 --order 5` or `--order 8`, then
[trace_surfaces.py](../../scripts/trace_surfaces.py) with the selected snapshot,
original Wout, `--direct --transits 200` and only the remaining diagnostic budget.
The [study launcher](../../scripts/run_coil_freedom.py) runs C then P, using the fitter's
same-host monotonic diagnostic deadline for tracing, including early solver stops.
Invoke it with the original `--snapshot`, `--wout`, a fresh `--output` and the full
reviewed `--revision`; it rejects changed inputs or a dirty/different checkout and
records source hashes. It uses the current native Python with MPI disabled, four
thread limits set to one, and a minimal child environment. No comparison has run.

Its 0.1 s watchdog stops process groups on a deadline, aggregate output above
256 MiB minus 64 KiB reserved for final reports, or live reserve below 2 GiB;
each arm requires 3 GiB initially. Logs, cache and temporary outputs count. This
is a monitored ceiling, not a filesystem quota: overshoot before detection is
retained and makes the arm incomplete even if its raw report says completed.
Search selects only completed pre-deadline trials; an in-flight call can return
late, with its overshoot charged against the outer 2700 s arm limit. The diagnostic
clock is never restarted. An unreturned call is stopped at the outer limit.
Group cleanup still runs after the leader exits; uncertain cleanup aborts the
study before the next arm can start. Ordinary recorded failures retain both arms.

Both use issue #52's failed-trial handling and `ftol=0`, unchanged `gtol`, objective,
penalties and eligibility. Only completed eligible candidates can win; probes and
failed trials cannot. Report all failures, solver stops, startup/search/check times,
boundary RMS/max, interior RMS, current, geometry bounds/active limits, all traced
lines and signed iota. Software completion and physical acceptance remain separate.

## Decision rule

With complete diagnostics, pursue a richer coil family only if P's fine boundary
RMS (maximum of the two fine-grid shifts) is at most half C's, P's continuous
geometry passes, and P's finest 64×64/512-node interior RMS
is no worse than C's. Otherwise choose joint plasma/coil optimization as the next
route. Missing/late records, failed independent kernel checks or unreturned tracing make
the comparison inconclusive. A completed negative geometry/tracing diagnostic is
reported as such. Do not invent a ratio or rerun to force a choice.

This is one seed, one local optimizer and one budget per arm. It allocates research
effort; it cannot prove the physical cause of a plateau, a globally optimal family,
verified surfaces or benefit transfer. All original acceptance limits remain.
Keep full evidence in an immutable archive and one short result here. No result
or new fitting-performance claim exists yet.
