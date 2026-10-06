# One question before more fitting

Updated 7 October 2026. [Roadmap](../PROJECT_PLAN.md) · [Assessment](../review/STRATEGIC_REVIEW_RESOLUTION.md)

**Can practical coils preserve a useful plasma benefit?** Boundary error is a
necessary diagnostic in our protocol, not the project objective. The [first matched-target experiment](ISSUE25_MATCHED_TARGETS.md) now includes
the improved Step 3 target, but leaves full benefit transfer unresolved. Resolve
the shallow-well and realized-flux-label limitations before claiming reactor progress.

## Decision of 6 October 2026

The registered hurdle was to at least halve reference401's geometry-checked
boundary RMS (0.001996268) without worsening interior RMS (0.01147939), with
realized-field diagnostics supporting benefit transfer. It is not met:

- The preregistered conditioning/stopping comparison ([#31](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/31)) reached
  boundary RMS 0.0018761 (−6.0%) and interior RMS 0.010310 in 30 minutes.
  Removing the early stop added about 1.2% before one failed trial ended the run.
- The [matched-target fits](ISSUE25_MATCHED_TARGETS.md) reached 0.001932 and
  0.001953 in 300 s; the wide action diagnostic is incomplete in both coil fields.

#31 was reported by a contributor (one seed and one budget per arm) and has not
been rerun by the maintainer. That suffices for this resource decision, not for a
physical conclusion. **We stop extending the fixed-target recipe and accept that
Step 4 progress along this route has stalled.** Acceptance limits are unchanged.
[Decision record](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/28).

## Next: a bounded joint feasibility protocol

1. **Retain the completed fitter fix and probe.** The reviewed
   [fitter](README.md) handles failed numerical trials and removes the positive
   reduction cutoff. The [order-8 probe](ISSUE53_COIL_FREEDOM.md) completed but missed
   its half-error hurdle. Its frozen rule selects joint plasma/coil optimization
   ([#36](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/36)). Do not extend or repeat the probe to cross the threshold.
2. **Freeze a joint feasibility protocol** ([#37](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/37)) before implementing a broader search.
   Name limited plasma freedom, fixed size/flux and engineering constraints,
   controls, candidate selection and total budgets including equilibrium solves.
   The common realized-field endpoint is still unresolved; until it is qualified,
   the pilot can establish feasibility, not confirm benefit transfer.
3. **Keep inspecting actual fields.** Shallow-well fidelity and realized flux
   labels ([#48](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/48)) apply to whichever route follows. If surfaces or
   required data are missing, report the blockage, not benefit transfer.

Keep target-specific normalization frozen and report each target separately;
do not treat errors against different targets as a matched improvement.
Report boundary RMS/max, interior RMS, geometry, current, realized-field findings
and elapsed time together. The original 1e-4 / 1e-3 / 0.01 limits and continuous
geometry checks remain unchanged. No endpoint or solver success flag admits a
physical design; the [Step 4 requirements](../steps/STEP_4_PLASMA_AND_COILS.md) still apply.

Use existing tools and one short result record. Retain the existing ceilings
unless a separate protocol justifies a different bounded study: 1800 s search per
arm including intake, equilibrium solves and startup, 900 s diagnostics, one native
thread, 256 MiB output and 3 GiB initial / 2 GiB live disk reserve.
A joint protocol must account for all work and define how clock interruptions are recorded; the
completed probe's monotonic and wall-timestamp discrepancy remains a limitation.
Stop at resource ceilings, retain failures and draw no completed-comparison
conclusion from incomplete diagnostics. These rules do not change historical
experiments or restrict unsolicited contributions. Avoid overlapping heavy jobs.

## Reactor relevance and collaboration

Do a desk-level feasibility screen alongside this work, without rebuilding
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
