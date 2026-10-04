# One question before more fitting

Updated 4 October 2026. [Roadmap](../PROJECT_PLAN.md) · [Assessment](../review/STRATEGIC_REVIEW_RESOLUTION.md)

**Can practical coils preserve a useful plasma benefit?** Boundary error is a
necessary diagnostic in our protocol, not the project objective. The current
fits use reference401, not the improved Step 3 target. Resolve that disconnect
before treating further optimization as progress toward a reactor.

This is prospective work. The current driver reproduces reference401 only;
matched-target input support and realized-field diagnostics still need to be
prepared with existing physics tools. This cleanup does not supply new results.

## Next experiment and decision

1. **Prepare a matched comparison.** Bind the reference and improved targets,
   starting coils, currents/flux conventions and numerical grids. Reuse the
   normalized fitter and shared checks. Run one conditioning/stopping comparison
   against the current recipe before adding more optimizer variants. Match
   wall-clock budgets and report startup and search time separately.
2. **Inspect actual fields early.** Use a small, fixed set of saved candidates
   to examine magnetic surfaces, islands and interior fidelity; a failing field
   can still diagnose why the method fails. Compare the Step 3 diagnostic in
   reference-target and improved-target coil fields on matched domains. If
   surfaces or required data are missing, report the blockage, not benefit
   transfer. Register selection, tolerances and holdouts before confirmation.
3. **Decide by 24 October 2026.** Continue the fixed-target recipe only if a
   reference401 comparison at least halves its current geometry-checked boundary
   RMS (0.001996268) without worsening interior RMS (0.01147939), and
   realized-field diagnostics support
   investigating benefit transfer. The factor of two is a prospective resource
   allocation hurdle, **not** a new acceptance limit or a prediction. Otherwise
   stop extending this recipe and choose one alternative: another coil family,
   another target, or joint plasma/coil optimization in existing software.
   Incomplete checks are insufficient grounds to scale the search.

Keep target-specific normalization frozen and report each target separately;
do not treat errors against different targets as a matched improvement.
Report boundary RMS/max, interior RMS, geometry, current, realized-field findings
and elapsed time together. The original 1e-4 / 1e-3 / 0.01 limits and continuous
geometry checks remain unchanged. No endpoint or solver success flag admits a
physical design; the [Step 4 requirements](../steps/STEP_4_PLASMA_AND_COILS.md) still apply.

For this next comparison, declare at most 30 minutes per search arm, one native
thread, 256 MiB retained output per arm and 3 GiB initial / 2 GiB live disk reserve.
Use existing tools and one short result record. Stop at the resource ceiling,
retain failures and make no conclusion from a run with incomplete diagnostics.
These prospective limits do not change recorded experiments or restrict unsolicited
contributions. Avoid running heavy jobs during controlled timing.

## Reactor relevance and collaboration

Do a desk-level feasibility screen alongside this comparison, without rebuilding
retired solvers: identify the proposed device scale, field and pressure assumptions,
net-electric-power balance, winding/blanket/shield space, magnet loads, heat exhaust
and maintenance access. For each, record a source or an explicit unknown and the
cheapest check that could reject the direction. Detailed pressure/engineering work
starts when that decision needs it, rather than automatically at a boundary score.

The smallest MS0 deliverable is the matched target/coil data and existing checker
running outside the maintainer's workspace, with a positive control and retained
failures. Assess an adapter to existing community tools first; no new platform.
Public dense boundary evaluation already exists, but interior targets and full
acceptance are not portable yet. Prioritize that missing reproducibility now;
26 March 2027 remains the outer MS0 decision target, not a reason to delay it.
Publication and external contact require separate authority. No new outreach or
physical acceptance follows from this programme.
