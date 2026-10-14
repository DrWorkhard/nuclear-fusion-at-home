# One question before more fitting

Updated 14 October 2026. [Roadmap](../PROJECT_PLAN.md) · [Assessment](../review/STRATEGIC_REVIEW_RESOLUTION.md)

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

## Route chosen, 8 October 2026: joint plasma/coil optimization

After the fitter fixes ([#52](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/52)), the preregistered
[coil-freedom probe](ISSUE53_COIL_FREEDOM.md) lifted six coils from Fourier order 5
to 8 under the same 30-minute budget. Boundary RMS improved only 3.6% (ratio 0.964,
required ≤ 0.5), so by the fixed rule the next route is joint plasma/coil
optimization ([#36](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/36)), not another coil family. A
[construction-margin probe](ISSUE70_CONSTRUCTION_MARGINS.md) then halved every margin toward its acceptance
limit and gained 5.8% (ratio 0.942). Under the owner-approved
[acceptance v2](../validation/ACCEPTANCE_V2.md), coil sets from three fixed-target
methods and their combinations pass the field and geometry checks on both targets
([leaderboard](../validation/LEADERBOARD.md)). The best combination lowers the
worst v2 ratio by 12.5% but boundary RMS by under 1%
([#102](ISSUE102_COMBINED_METHODS.md)); an 8× longer search lowers its field
errors by 9% more but loses the continuous geometry certificate
([#105](ISSUE105_SEARCH_BUDGET.md)). The wide bounce diagnostic completes only in
interior-weighted fields; in one matched pair 61% of the ideal improvement remains
([Step 3 record](STEP3_V2_METHODS.md), exploratory; [#89](ISSUE89_V2_COIL_BOUNCE.md)).
The route stands.

**Owner direction, 14 October 2026:** the plasma itself must be of the best achievable
quality, judged also by ConStellaration's stability, turbulence and coil-simplicity
criteria ([#111](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/111)). Both targets lack a vacuum well and exceed the
flux-compression bound. The first joint protocol ([JOINT_PROTOCOL.md](JOINT_PROTOCOL.md),
#59) is kept as a negative result: its derivative checks failed, and its ±5e-4 moves
cannot reach those requirements. The order of work is in the pinned
[#116](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/116) and the `P0`–`P2` issue labels:

1. **Score every plasma** ([#112](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/112)) and freeze **plasma requirements v1**
   after calibration on the ConStellaration dataset ([#113](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/113)).
2. **Plasma-only feasibility under v1** ([#114](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/114), stage 1), with target
   intake for new plasmas ([#115](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/115)).
3. **Coils for a v1 plasma, then a new joint protocol and optimizer** (#114 stages
   2–3, [#39](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/39)).
4. **Qualify realized-field endpoints** ([#48](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/48)). Until matched
   realized-surface labels exist, coil-field action scores are exploratory; if
   surfaces or required data are missing, report the blockage, not benefit transfer.

Keep target-specific normalization frozen and report each target separately;
do not treat errors against different targets as a matched improvement.
Report boundary RMS/max, interior RMS, geometry, current, realized-field findings
and elapsed time together. The original 1e-4 / 1e-3 / 0.01 limits (v1) and continuous
geometry checks remain unchanged; results also report the v2 verdict. No endpoint
or solver success flag admits a
physical design; the [Step 4 requirements](../steps/STEP_4_PLASMA_AND_COILS.md) still apply.

The probe used at most 30 minutes per search arm, one native thread, 256 MiB
retained output per arm and 3 GiB initial / 2 GiB live disk reserve; the joint
pilot declares its own limits in its protocol.
Use existing tools and one short result record. Stop at the resource ceiling,
retain failures and make no conclusion from a run with incomplete diagnostics.
These prospective limits do not change recorded experiments or restrict unsolicited
contributions. Avoid running heavy jobs during controlled timing.

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
