# Roadmap and completion criteria

Updated 23 September 2026.
[Overview](README.md) · [Evidence-based status](STATUS.md) · [Contribution guide](../CONTRIBUTING.md)

## Immediate priority: public collaboration

Build a useful public foundation for Nuclear Fusion @ Home without claiming that
the scientific design problem is solved. Success means an outside contributor can
start from a fresh checkout, reproduce a small reference, evaluate a candidate,
replay the report and submit useful work without our local artifacts or chat history.

| Release task | Completion criterion | Current state |
| --- | --- | --- |
| Preserve prior work | Original evidence intact; interrupted work explicitly unqualified | Done; protected-fit drafts saved, no new search |
| Portable entry | Bundled attributed data, no native install, named candidate schema, explicit scope | Implemented; unit/analytic controls pass |
| Reproduction and adversarial checks | Committed-source clean-copy reference/candidate/replay and rejection of forged results | Next local verification |
| Public understanding and contribution | Clear English overview, status, quickstart, open contribution/review route | Prepared |
| Hosted operation | Verified CI, reviewer identities, branch protection, privacy/rights review and safe permissions | Not configured or verified here; separate launch work |

The [release specification](validation/PUBLIC_RELEASE.md) records exact scope and
checks. Public quickstart success is not full historical reproducibility or
physical admission. No automatic PR monitor, merge bot, push or publication has
been enabled.

**Participation rule:** compute budget/cost disclosure is optional. Useful work
does not need to match a requested task. [Research hints](optimization/RESEARCH_HINTS.md)
are nonexclusive invitations. Review unexpected ideas and negative findings on
their merits. Our execution limits protect our infrastructure; they are not a
ceiling on others' research spending. Efficiency claims still require appropriate
measurements.

## Scientific roadmap — unchanged goals

| Step | Actual completion requirement | State |
| --- | --- | --- |
| 1. Reliable bounded foundation | Specified local reference/software/physics checks, source and environment identity, honest admission | Complete in the registered scope |
| 2. Reproducible iteration | Load reference → change/optimize → save → independently evaluate → repeat | Complete in the registered scope |
| 3. Own QI-like plasma target | Actual boundary/equilibrium change with registered independently confirmed improvement | Complete for the nfp2 vacuum action-metric study |
| 4. Coupled plasma and coils | The four subpackages below, not merely a favorable vacuum coil-fit score | Open |
| 5. Demonstrated performance advance | Fair, reproducible reference comparisons with independently verified meaningful advantage | Open; no automatic claim from Step4 |

Steps1/2 are capability milestones: they did not require a new feasible optimum,
novel method or SoTA result. Their [acceptance protocol](validation/FOUNDATION_ACCEPTANCE_PROTOCOL.md)
and [result](validation/FOUNDATION_ACCEPTANCE_RESULTS.md) remain authoritative.
Step3 did require a real improvement, established in the
[registered vacuum study](qi/PLASMA_BALANCED_RESULTS.md). Broader physics was not
silently included in its acceptance.

## Step4: coupled plasma/coil development

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
priority before resuming local searches. No vacuum-only result closes all Step4.

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

After each completed work step, update the relevant detail/log and affected
overviews, run appropriate tests/docs checks, review the diff and commit locally.
Do not replace these summaries with accumulating experiment histories; details
belong in the indexed child directories. [Persistent rules](../AGENTS.md).

## Preservation and future scope

Research before the clarified foundation milestones is preserved at5971fee
(`foundation-pre-scope-2026-09-13`); Step3 evidence remains atd429783.
Current negative results are retained rather than relabelled as successes.
The public layer is additive and uses its own portable artifact identities.

SQuID-C is a later baseline, not a prerequisite for contributing now. Source
availability must be checked when needed; old unsuccessful searches are not a
current proof of unavailability. Full SQuID-C qualification and SoTA comparisons
remain distinct from making this repository easy to use.
