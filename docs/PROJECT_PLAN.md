# Roadmap and completion criteria

Updated 24 September 2026.
[Overview](README.md) · [Evidence-based status](STATUS.md) · [Contribution guide](../CONTRIBUTING.md)

## MSX: our end goal

Contribute to nuclear fusion for humanity by finding the best reactor design
current technology can achieve. Pursue reproducible, useful design advances under
explicit performance, engineering, robustness, safety and cost constraints.
“Best” is the ambition, not a claim of global optimality or present plant readiness.
Stellarator plasma/coil optimization is our current route toward that wider goal.
**MSX is not achieved.** It extends beyond MS1: expert scrutiny and practical
follow-on work should turn verified design advances into useful fusion progress.

## Immediate priority: public collaboration

Build a useful public foundation for Nuclear Fusion @ Home without claiming that
the scientific design problem is solved. Success means an outside contributor can
start from a fresh checkout, reproduce a small reference, evaluate a candidate,
replay the report and submit useful work without our local artifacts or chat history.

| Release task | Completion criterion | Current state |
| --- | --- | --- |
| Preserve prior work | Original evidence intact; interrupted work explicitly unqualified | Done; protected-fit drafts saved, no new search |
| Portable entry | Bundled attributed data, no native install, named candidate schema, explicit scope | Complete in the starter scope; 44 public tests pass on local Python 3.11/3.12/3.14 |
| Reproduction and adversarial checks | Committed-source clean-copy reference/candidate/replay and rejection of forged results | Eight local checks pass on each supported CI Python; fresh dev-only core runner also passes |
| Public understanding and contribution | English entry/index pages, target scores, named edits, open contribution/review route | Eight-point review addressed and locally verified; hosted verification remains separate |
| Publication review | Inventory history/content, adjudicate privacy/rights, review exact release | Initial bounded inventory complete; home-path indicators found, clearance remains open |
| Hosted operation | Verified CI, reviewer identities, branch protection and safe permissions | Not configured or verified here; separate launch work |

The [release specification](validation/PUBLIC_RELEASE.md) and
[verification record](validation/PUBLIC_RELEASE_RESULTS.md) record exact scope
and observed checks. The [review follow-up](validation/PUBLIC_REVIEW_FIXES.md)
records the expanded local compatibility/CI verification. Public quickstart
success is not full historical reproducibility or physical admission.
No automatic PR monitor, merge bot, push or publication has
been enabled.

**Participation rule:** compute budget/cost disclosure is optional. Useful work
does not need to match a requested task. [Research hints](optimization/RESEARCH_HINTS.md)
are nonexclusive invitations. Review unexpected ideas and negative findings on
their merits. Our execution limits protect our infrastructure; they are not a
ceiling on others' research spending. Efficiency claims still require appropriate
measurements.

## Scientific roadmap — unchanged goals

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

## MS1: evidence-backed outreach to Proxima Fusion

As soon as strong, reproducible and independently checked evidence shows that a
design we found is better than the design Proxima Fusion is pursuing, we will
contact Proxima Fusion with the design and evidence for technical discussion.
**MS1 is not reached.** It is a targeted outcome of Step 5, not another name for
Step 1, completion of the public starter, or the project's ultimate goal (MSX).

Use an authoritative, versioned reference confirmed relevant at comparison time;
qualify its reproduction and compare under matched operating/technology constraints.
Define meaningful design objectives, feasibility gates and uncertainty checks
before confirmatory evaluation. Report trade-offs and limits; neither a single
favorable proxy nor an unmatched/obsolete baseline establishes design superiority.
The [MS1 evidence framework](squid_c/MS1_PROXIMA_COMPARISON.md) guides the later
numerical protocol without changing any existing study's acceptance thresholds.
No contact is being made by this planning update. MS1 leads to expert scrutiny
and further work, not a claim that the best possible reactor has been found.

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
is preserved but not qualified; it is one possible next experiment, not a required
method or an exclusive work allocation. The public contribution foundation takes
priority before resuming local searches. No vacuum-only result closes all of Step 4.

## Research and review discipline

Define confirmatory studies before running them; separate construction from
acceptance and preserve all predeclared resolution levels, failures and source
records. Existing experiment budgets/thresholds do not change retroactively.
External exploratory work is welcome without prior permission or retrospective
preregistration; label it honestly and agree independent checks for its claims.

Do not let a candidate change its own verifier. Improvements to physics models,
tests and criteria are valuable contributions, but require separate versioning,
review and revalidation. Source/dataset hashes are evidence of identity, not
proof of scientific correctness or trust in an unknown fork.

For maintainer research sessions: after each completed work step, update the relevant detail/log and affected
overviews, run appropriate tests/docs checks, review the diff and commit locally.
Do not replace these summaries with accumulating experiment histories; details
belong in the indexed child directories. Outside contributors document their
scoped change and checks in their PR; maintainers integrate the shared logs/status.
[Agent guide and maintainer-only rules](../AGENTS.md).

## Preservation and future scope

Research before the clarified foundation milestones is preserved at `5971fee`
(`foundation-pre-scope-2026-09-13`); Step 3 evidence remains at `d429783`.
Current negative results are retained rather than relabelled as successes.
The public layer is additive and uses its own portable artifact identities.

SQuID-C is a later baseline, not a prerequisite for contributing now. Source
availability must be checked when needed; old unsuccessful searches are not a
current proof of unavailability. Full SQuID-C qualification and SoTA comparisons
remain distinct from making this repository easy to use.
