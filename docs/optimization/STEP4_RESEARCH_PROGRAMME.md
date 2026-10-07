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

## Next: a bounded joint comparison by 24 October 2026

The completed local [coil-freedom probe](ISSUE53_COIL_FREEDOM.md) misses the
registered continuation hurdle. The rule selects joint plasma/coil optimization;
its timing qualifications and the separate contributor report remain in that record.

1. **Reuse the existing fitter and checks.** Failed-trial handling, the stopping-rule
   fix and order-5/order-8 support are integrated. Do not repeat or extend the
   completed coil-freedom search to cross its threshold.
2. **Preregister the smallest joint comparison**
   ([#37](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/37)) and use
   the implementation work in [#39](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/39).
   Keep optimization separate from unchanged acceptance and independent checking.
   Compare against matched fixed-target effort before claiming actual-field benefit.
3. **Keep inspecting actual fields.** Shallow-well fidelity and realized flux
   labels ([#48](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/48))
   still require qualification. Missing surfaces or required data remain a blockage,
   not evidence of benefit transfer.

Keep target-specific normalization frozen and report each target separately;
do not treat errors against different targets as a matched improvement.
Report boundary RMS/max, interior RMS, geometry, current, realized-field findings
and elapsed time together. The original 1e-4 / 1e-3 / 0.01 limits and continuous
geometry checks remain unchanged. No endpoint or solver success flag admits a
physical design; the [Step 4 requirements](../steps/STEP_4_PLASMA_AND_COILS.md) still apply.

The completed probe retains its original protocol, budgets, failures and limitations
in the archive. Future experiments need their own decision and prospective limits;
those do not change historical results or restrict unsolicited contributions.
Avoid running heavy jobs during controlled timing.

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
Public dense boundary evaluation and a locally qualified
[dense interior packet](../validation/ISSUE10_DENSE_INTERIOR.md) now exist; full
acceptance is not portable yet. Prioritize publication and shared-check reproduction;
26 March 2027 remains the outer MS0 decision target, not a reason to delay it.
Publication and external contact require separate authority. No new outreach or
physical acceptance follows from this programme.
