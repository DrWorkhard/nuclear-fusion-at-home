# Scientific status and evidence

Updated 23 September 2026.
[Overview](README.md) · [Roadmap](PROJECT_PLAN.md) · [Public quickstart](validation/PUBLIC_QUICKSTART.md)

## Bottom line

**We have a bounded local research foundation, a numerically improved vacuum
plasma target, and useful coil-validation tools. We do not yet have a new
physically accepted coil design, a completed Step 4, a state-of-the-art advance,
or full SQuID-C readiness.**

The immediate work is a portable public contribution layer. It is not a new
physical result and does not reopen or expand the completed foundation milestones.
The interrupted protected-fit proposal/solver are preserved as unqualified drafts;
no new protected-fit search was executed.

## Established results and their limits

| Work package | Evidence-backed result | What remains unproven |
| --- | --- | --- |
| Steps1/2: bounded foundation and iteration | Eight foundation gates, six mandatory scientific regressions, two exactly repeated24-bundle paths and four independent candidate checks | Universal QI/engineering validity; those candidates remain physically rejected |
| Step3: own nfp2 vacuum plasma target | Relative bounce-action variance decreases from2.3894265674e-4 to2.1225270715e-4 (11.1700%); narrower-domain gain4.8506%; all ten final gates pass | Global QI, improved measured confinement, finite pressure, practical coils or plant performance |
| Step4 coil initialization | All12 constructed starting sets pass scoped geometry admission; selected six/eight-base-coil forms retain at least98.2mm certified plasma clearance, required80mm | Magnetic-field quality or full finite-build engineering |
| Step4 field starts | Four cells, eight N/V derivative checks,20 refinements,768 direct B/A comparisons and252 flux gates pass numerical qualification | All four fail physical field limits: normal RMS0.269–0.276 versus1e-4; inner-vector RMS0.3615–0.3723 versus0.01 |
| Cumulative geometry bounds | The52-state qualification passes all required small probes and independent direct checks;18 larger probes remain uncertified | Uncertified does not mean physically impossible; no field improvement follows from this alone |

Sources: [foundation acceptance](validation/FOUNDATION_ACCEPTANCE_RESULTS.md),
[plasma result](qi/PLASMA_BALANCED_RESULTS.md),
[coil initialization](geometry/CLEAR_COIL_INITIALIZATION_RESULTS.md),
[field qualification](optimization/CLEAR_COIL_FIELD_START_RESULTS.md),
[cumulative geometry](geometry/COIL_PERTURBATION_RESULTS.md).

The plasma comparison used both action domains during construction: it is not a
blind holdout. The reported improvement exceeds the registered numerical-uncertainty
test, but remains a metric-specific result. “Independent” in these reports refers
to the specified numerical/source checks, not external peer review.

## Failures we retain

- The [first plasma design](qi/PLASMA_OPTIMIZATION_RESULTS.md) worsened the wider
  action metric despite improvement on the construction objective.
- The [first actual-coil pilot](optimization/COUPLED_COIL_PILOT_RESULTS.md) has
  six completed searches and six physical rejections: fine plasma clearance only
  1.8–6.7mm against80mm required; only17/30 refinements pass.
- The best preserved [LPQA coil search](optimization/CURRENT_START_GN_RESULTS.md)
  reaches raw fine flux8.129882e-8, still above its1e-8 threshold. Its0.754% gain
  is real within that comparison, not a feasible-design or convergence claim.
- The extended W7-X file comparison remains60/63. The selected physics regression
  does not erase the other three differences.
- End-to-end QI/orbit qualification and valid complete mechanics remain open.
  Earlier finite-mesh checks do not certify neighboring elements/full assemblies;
  large linear-deformation outputs were outside the model's valid scope.

Detail: [validation](validation/README.md), [QI](qi/README.md),
[engineering](engineering/README.md), [research log](logbook/README.md).
Older optimistic journal conclusions do not supersede this current assessment.

## Public usability — a separate deliverable

The additive public code has dependency-free unit/analytic controls,
a small attributed real-coil packet and a candidate/report interface. Its first
committed-source copied-tree reference run is pending. Hosted CI and independent
hardware reproduction have not been verified.

The public profile evaluates192 fixed sample points with frozen physical currents.
It reports sparse normal/vector errors and256/512 filament-resolution differences;
it does not compute the original full-surface, flux-normalized acceptance.
Report replay uses the same public implementation. An unchanged-seed comparison
against archived native B/A is a separate arithmetic check. Public reports never
set physical admission or Step4 to true.

The complete historical research workflow still requires additional native
dependencies, large local artifacts and qualified source-bound adapters. Its
last completed full suite had2064 passing tests with334 documented warnings;
this is distinct from the new public tests. The strict netCDF4 import warning
remains unresolved, with no claimed ABI-freedom or hosted-CI pass.

## Next required evidence

First close the [portable release checks](validation/PUBLIC_RELEASE.md), including
fresh-copy use without site packages and explicit tampering rejection. Before an
actual public launch, complete [hosting/security checks](validation/REVIEW_POLICY.md).
Then contributors can tackle the nonexclusive [research hints](optimization/RESEARCH_HINTS.md).

Scientifically, Step4 still needs actual-coil field/QI transfer, genuine coupled
improvement, finite-pressure/confinement work and finite-geometry/robustness.
[SQuID-C readiness](squid_c/SQUID_C_READINESS.md) has additional gates; missing
author data is not the only remaining obstacle.
