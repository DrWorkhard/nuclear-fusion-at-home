# Scientific status and evidence

Updated 24 September 2026.
[Overview](README.md) · [Roadmap](PROJECT_PLAN.md) · [Public quickstart](validation/PUBLIC_QUICKSTART.md)

## Bottom line

**We have a bounded local research foundation, a numerically improved vacuum
plasma target, and useful coil-validation tools. We do not yet have a new
physically accepted coil design, a completed Step 4, a state-of-the-art advance,
or full SQuID-C readiness.**

**MS1 is not reached:** we do not have strong evidence that our design is better
than the design Proxima Fusion is pursuing. Contacting Proxima with such evidence
is a planned milestone, not an action already taken. Our existing plasma result
is against an open research reference, not a Proxima design comparison.
[MS1 evidence framework](squid_c/MS1_PROXIMA_COMPARISON.md).

**MSX remains our long-term goal, not an achieved result:** contribute to nuclear
fusion for humanity by finding the best reactor design current technology can
achieve. MS1 is an intermediate milestone on that path.

The portable public contribution layer now passes its scoped local release checks.
It is not a new physical result and does not reopen or expand the completed
foundation milestones. Public hosting and operational safeguards remain separate work.
Roadmap status: Steps 1–3 **Complete** in their stated scopes; Step 4,
**Develop plasma and coils together**, **In progress**; Step 5 **Not achieved**;
MS1 **Not reached**; MSX **Long-term goal**. [Canonical plan](PROJECT_PLAN.md).
The interrupted protected-fit proposal/solver are preserved as unqualified drafts;
no new protected-fit search was executed.

## Established results and their limits

| Work package | Evidence-backed result | What remains unproven |
| --- | --- | --- |
| Steps 1/2: bounded foundation and iteration | Eight foundation gates, six mandatory scientific regressions, two exactly repeated 24-bundle paths and four independent candidate checks | Universal QI/engineering validity; those candidates remain physically rejected |
| Step 3: own nfp2 vacuum plasma target | Relative bounce-action variance decreases from 2.3894265674e-4 to 2.1225270715e-4 (11.1700%); narrower-domain gain 4.8506%; all ten final gates pass | Global QI, improved measured confinement, finite pressure, practical coils or plant performance |
| Step 4 coil initialization | All 12 constructed starting sets pass scoped geometry admission; selected six/eight-base-coil forms retain at least 98.2 mm certified plasma clearance, required 80 mm | Magnetic-field quality or full finite-build engineering |
| Step 4 field starts | Four cells, eight normal/vector derivative checks, 20 refinements, 768 direct B/A comparisons and 252 flux gates pass numerical qualification | All four fail physical field limits: normal RMS 0.269–0.276 versus 1e-4; inner-vector RMS 0.3615–0.3723 versus 0.01 |
| Cumulative geometry bounds | The 52-state qualification passes all required small probes and independent direct checks; 18 larger probes remain uncertified | Uncertified does not mean physically impossible; no field improvement follows from this alone |

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
  1.8–6.7 mm against 80 mm required; only 17/30 refinements pass.
- The best preserved [LPQA coil search](optimization/CURRENT_START_GN_RESULTS.md)
  reaches raw fine flux 8.129882e-8, still above its 1e-8 threshold. Its 0.754% gain
  is real within that comparison, not a feasible-design or convergence claim.
- The extended W7-X file comparison remains 60/63. The selected physics regression
  does not erase the other three differences.
- End-to-end QI/orbit qualification and valid complete mechanics remain open.
  Earlier finite-mesh checks do not certify neighboring elements/full assemblies;
  large linear-deformation outputs were outside the model's valid scope.

Detail: [validation](validation/README.md), [QI](qi/README.md),
[engineering](engineering/README.md), [research log](logbook/README.md).
Older optimistic journal conclusions do not supersede this current assessment.

## Public usability — a separate deliverable

The public layer now has 44 passing dependency-free unit/analytic tests on local
Python 3.11/3.12/3.14, including named edits and score interpretation. The
[release review fixes](validation/PUBLIC_REVIEW_FIXES.md) add explicit dev-only
CI scope, UTF-8 reads, an early version guard and English navigation. The exact
core script passes in a fresh local dev-only clone (44 public + 14 selected tests).
The starter supplies a small attributed real-coil packet and candidate/report
interface. All eight committed-source copied-tree checks pass on each Python:
reference, changed candidate, replay,
tamper/overwrite rejection and contribution metadata without cost disclosure.
The largest reference/native relative field difference is 9.59e-16 against the
registered 5e-10 limit. [Release evidence](validation/PUBLIC_RELEASE_RESULTS.md).
Hosted CI and independent hardware reproduction have not been verified.
All B/A arrays match the earlier release exactly. Python 3.12/3.14 reports are
byte-identical; Python 3.11 has two seed metrics differing by less than 1.12e-16.
The existing tolerance and old-report replay pass without evaluator changes.

The [initial publication inventory](validation/PUBLICATION_INVENTORY.md) finds
about 325 MB of tracked content and 365 tracked files with home-path indicators
at its recorded revision. Five limited credential/key-shaped patterns have no
matches across reachable blobs. This is not a complete security or rights review;
privacy indicators, intended release scope and later commits still need review.
No historical evidence or Git history was sanitized or published.

The public profile evaluates 192 fixed sample points with frozen physical currents.
It reports sparse normal/vector errors and 256/512 filament-resolution differences;
it does not compute the original full-surface, flux-normalized acceptance.
Report replay uses the same public implementation. An unchanged-seed comparison
against archived native B/A is a separate arithmetic check. Public reports never
set physical admission or Step 4 to true.

The complete historical research workflow still requires additional native
dependencies, large local artifacts and qualified source-bound adapters. Its
latest full regression at `be916fb` has **2,072 passing tests**, no failures/skips,
and **334 documented warnings** in 222.70 seconds; this is distinct from the
44 public tests. The strict netCDF4 import warning
remains unresolved, with no claimed ABI-freedom or hosted-CI pass.

## Next required evidence

The [local portable release checks](validation/PUBLIC_RELEASE_RESULTS.md) are complete.
Before an actual public launch, complete the [hosting/security checklist](validation/REVIEW_POLICY.md),
including whole-history publication review, protected review settings and hosted
and independent-machine execution. Contributors can use the starter and tackle
the nonexclusive [research hints](optimization/RESEARCH_HINTS.md); those hints do
not restrict unsolicited contributions.

Scientifically, Step 4 still needs actual-coil field/QI transfer, genuine coupled
improvement, finite-pressure/confinement work and finite-geometry/robustness.
[SQuID-C readiness](squid_c/SQUID_C_READINESS.md) has additional gates; missing
author data is not the only remaining obstacle.
