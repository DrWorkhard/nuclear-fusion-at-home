# Roadmap and completion criteria

Updated 25 September 2026.
[Overview](README.md) · [Evidence-based status](STATUS.md) · [Contribution guide](../CONTRIBUTING.md)

This page defines what each step and milestone requires and what comes next. The
goal and a short summary are on the [front page](../README.md); the evidence
behind each status is on the [status page](STATUS.md).

## Immediate priority: public collaboration

Build a useful public foundation for Nuclear Fusion @ Home without claiming that
the scientific design problem is solved. Success means an outside contributor can
start from a fresh checkout, reproduce a small reference, evaluate a candidate,
replay the report and submit useful work without our local artifacts or chat history.

| Release task | Completion criterion | Current state |
| --- | --- | --- |
| Preserve prior work | Original evidence intact; interrupted work explicitly unqualified | Done; protected-fit drafts saved, no new search |
| Portable entry | Bundled attributed data, no native install, named candidate schema, explicit scope | Complete in the starter scope on local Python 3.11/3.12/3.14 |
| Reproduction and adversarial checks | Committed-source clean-copy reference/candidate/replay and rejection of forged results | Eight local checks pass on each supported CI Python; fresh dev-only core runner also passes |
| Public understanding and contribution | English entry/index pages, target scores, named edits, open contribution/review route | [README follow-up](review/ROOT_README_RESOLUTION.md): 26 recommendations locally verified, including three-Python copied-tree checks. Real clone URL remains a hosting prerequisite |
| Publication review | Inventory history/content, adjudicate privacy/rights, review exact release | Initial bounded inventory complete; home-path indicators found, clearance remains open |
| Hosted operation | Verified CI, reviewer identities, branch protection and safe permissions | Not configured or verified here; see the [launch checklist](validation/REVIEW_POLICY.md#launch-checklist--requires-actual-hosting-work) |

Exact scope and observed checks: [release specification](validation/PUBLIC_RELEASE.md),
[verification record](validation/PUBLIC_RELEASE_RESULTS.md) and
[review follow-up](validation/PUBLIC_REVIEW_FIXES.md).

## Scientific roadmap

Stellarator plasma/coil optimization is our current route toward the end goal (MSX).

| Step / milestone | Actual completion requirement | State |
| --- | --- | --- |
| 1. Establish a reliable foundation | Specified local reference/software/physics checks, source and environment identity, honest admission | Complete (local reference tools) |
| 2. Make design iteration reproducible | Load reference → change/optimize → save → independently evaluate → repeat | Complete (iteration workflow) |
| 3. Improve our own plasma target | Actual boundary/equilibrium change with registered independently confirmed improvement | Complete (vacuum study) |
| 4. Develop plasma and coils together | The four subpackages below, not merely a favorable vacuum coil-fit score | In progress |
| 5. Demonstrate a meaningful design advantage | Fair, reproducible reference comparisons with independently verified meaningful advantage; target MS1 for the Proxima comparison | Not achieved |
| MS1. Contact Proxima Fusion with strong evidence | As soon as strong, reproducible and independently checked evidence supports that our design is better than the design Proxima is pursuing, contact them with the evidence | Not reached |
| MSX. Our end goal | Contribute to nuclear fusion for humanity by finding the best reactor design current technology can achieve | Long-term goal |

Steps 1/2 are capability milestones: they did not require a new feasible optimum,
novel method or SoTA result. Their [acceptance protocol](validation/FOUNDATION_ACCEPTANCE_PROTOCOL.md)
and [result](validation/FOUNDATION_ACCEPTANCE_RESULTS.md) remain authoritative.
Step 3 did require a real improvement, established in the
[registered vacuum study](qi/PLASMA_BALANCED_RESULTS.md). Broader physics was not
silently included in its acceptance.

MS1 is a targeted outcome of Step 5, not another name for Step 1, completion of
the public starter, or the end goal. The [MS1 evidence framework](squid_c/MS1_PROXIMA_COMPARISON.md)
sets out the evidence required and guides the later numerical protocol without
changing any existing study's acceptance thresholds. No contact has been made.

## Step 4: Develop plasma and coils together

- **4A — Realization and transfer:** realize both reference and selected plasma
  targets with actual coils, pass the appropriate numerical/geometry/field gates,
  then check field surfaces/topology and retention of the relevant plasma benefit.
- **4B — Coupled improvement:** compare coil-only controls with genuine coupled
  plasma/coil changes and independently admit an actual improvement. A proposed
  optimizer or predicted gain is insufficient.
- **4C — Pressure and confinement:** qualify finite-pressure/plasma-current and
  realized-field assumptions, with appropriate response/refinement and confinement
  diagnostics. Existing vacuum targets and first-order drift tests are insufficient.
- **4D — Finite geometry and robustness:** qualify winding/build/load assumptions
  and actual manufacturing/perturbation responses; retain absolute physical gates.

[Options and prior reviews](optimization/COUPLED_DESIGN_OPTIONS.md) give the methods
context. The [geometry-protected field-fit draft](optimization/PROTECTED_COIL_FIT_PROTOCOL.md)
is one possible next experiment, not a required method or an exclusive work
allocation; its [controller qualification](optimization/PROTECTED_SEARCH_SOFTWARE_RESULTS.md)
is complete in synthetic scope. The public contribution foundation takes priority
before resuming local searches. Next for Step 4A: qualify the source-bound runner's
persistence and budget handling with synthetic faults; complete the second method
review and physical auditor before native execution. Finer-grid acceptance remains
a separate required phase. No vacuum-only result closes all of Step 4.

## Rules and preserved history

Participation, study and review rules are set out once: [CONTRIBUTING](../CONTRIBUTING.md)
for contributors, the [review policy](validation/REVIEW_POLICY.md) for review and
evaluation boundaries, and [AGENTS.md](../AGENTS.md) for agents and maintainers.

Research before the clarified foundation milestones is preserved at `5971fee`
(tag `foundation-pre-scope-2026-09-13`); Step 3 evidence remains at `d429783`.
