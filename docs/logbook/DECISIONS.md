# Decision log

## D-020 — Public-benefit end goal, self-contained roadmap and MS1

**Status:** accepted explicit user clarification; no new scientific result
**Date:** 2026-09-23

State the end goal plainly: contribute to nuclear fusion for humanity by finding
the best reactor design current technology can achieve. “Best” remains a research
ambition under explicit constraints, not a current global-optimality claim.
The root README must explain all five research steps and what is actually done,
so references to Step 4 do not require reading prior conversations or detail logs.

MS1 is evidence-backed outreach: as soon as strong, reproducible and independently
checked evidence supports that our design is better than the design Proxima Fusion
is pursuing, we will contact them with the evidence. This is a targeted Step 5
outcome, distinct from the end goal and from completed bounded Steps 1/2/3.
MS1 is not reached; no Proxima comparison or contact has been performed here.

Require an authoritative, relevant versioned reference and matched technology/
operating assumptions, meaningful design-level advantage, credible uncertainties,
independent checks and disclosed trade-offs. An old publication is not automatically
the design Proxima currently pursues; our own-seed or sparse-proxy improvements do
not meet this bar. The framework fixes no numerical threshold or changed historical
gate. Public collaboration remains open, with optional cost disclosure. Preserve
past evidence and continue public-release preparation without restarting searches.
[MS1 framework](../squid_c/MS1_PROXIMA_COMPARISON.md).

## D-019 — Open collaboration, optional costs, additive portable publication

**Status:** accepted explicit user correction
**Date:** 2026-09-23

Prepare Nuclear Fusion @ Home as a public human/agent research repository.
Contributions need relevance and reviewable evidence, not a requested issue or
a declared spending budget. Publish nonexclusive research hints; assess novel,
unsolicited and negative work on its merits. Budget/cost reporting is optional;
equal-budget efficiency claims still require supporting measurements. Our CI
limits and frozen historical experiment budgets are separate and remain intact.

Prioritize a portable small real-coil starter, accessible English overview and
safe review workflow before further Step4 searches. Preserve absolute-path
historical evidence; portable exports are explicitly new derived artifacts.
Initial sparse fixed-current field diagnostics are not full design admission.
Preparing local files does not authorize publication or hosted merge privileges.
[Release plan and qualification gates](../validation/PUBLIC_RELEASE.md).

## D-018 — Preserve the complete checkpoint reference graph, not only its bytes

**Status:** accepted failure-provenance requirement; no scientific threshold change
**Date:** 2026-09-20

Pre-data source review finds a gap despite2055 passing tests: the new geometry
workflow's successful checkpoint binds an overwritten live inflight.json.
A later failed attempt leaves unchanged checkpoint bytes with an invalid hash
reference. Retain the first regression; do not equate a passing suite with a
fully qualified workflow. No project matrix was executed with that version.

Use an immutable marker per successful checkpoint and keep live status separate.
Independent audit checks marker path/hash/content and exact complete prefix;
failure tests traverse every retained reference after later IO/timeout and
checkpoint-publication errors. Never repair old checkpoint bytes after a failure
to hide the inconsistency. Applies to future workflows; historical evidence and
frozen kernels remain unchanged. [Qualification](../geometry/COIL_PERTURBATION_RESULTS.md).

## D-017 — Common entry points are additive, explicit and profile-scoped

**Status:** accepted interface scope; no new scientific admission
**Date:** 2026-09-20

On user request, provide shared profiles/evaluate/audit commands through
`python -m fusion_baselines` and root `fusion.py`. Keep the historical installed
intake CLI and package configuration byte-identical: an initial direct extension
correctly failed three preservation regressions and is not the accepted approach.

Version1 dispatches exactly the qualified clear-coil-field-start-v1 study and
its independent saved-run auditor. It does not accept arbitrary candidate designs,
retarget a profile, change scientific budgets or expose unqualified perturbation
work. Discovery/dry-run stay standard-library-only and do not trigger computation.
Exit0 retains its profile-specific meaning, never a universal physical pass.
Fresh outputs include protection of the historical audit writer's .tmp sibling.
Future candidate profiles need their own qualified source-bound workflows, not
just a new command alias. [Runbook](../validation/PROJECT_ENTRYPOINTS.md).

## D-016 — Qualify cumulative geometry protection before the next field fit

**Status:** accepted bounded step4A method choice; no search authorization by qualification alone
**Date:** 2026-09-19

After all four numerical startups pass at3334f1e, physical field quality remains
poor while safe geometry is finally established. Two independent read-only
reviews disagree on immediate priority: one free8×128 L-BFGS-B control to isolate
new starts/resolution, versus a short continuously certified local fit.
Choose the latter first, retaining the former as an explicit later control.
Reason: soft geometry penalties are zero initially and the conservative seed
CP reserve is only about18mm, not the50mm suggested by sampled distances.

First preregister/qualify a field-free cumulative D0/D1/D2 certificate against
the fixed actual seed, including curvature, projection winding and all original
distance gates. Do not repurpose rounding-only export_certificate, reset
allowances after each step, or inherit planar simplicity for arbitrary3D coils.
An overly tight certificate is a method limitation, not physical impossibility.
Only after its independently documented closure preregister the actual field
search/budgets/selection/refinement. No scope reduction of step4 or altered
physical thresholds. [Options/reviews](../optimization/GEOMETRY_PRESERVING_SEARCH_OPTIONS.md).

## D-015 — Explicit step4 authorization; independent review before coupled studies

**Status:** accepted; new user request after step3 handoff
**Date:** 2026-09-14

Start step4 with an independently reviewed methods portfolio and bounded actual
experiments. Three read-only agents separately reviewed physics, methods/literature
and local implementation. Prioritize paired reference/new-plasma coil realization,
then small genuine coupled updates. Do not reduce full step4 to vacuum normal-field
fitting: realized-field physics, pressure, finite geometry and robustness remain
explicit subpackages. New generic source-bound adapters must preserve exact target
modes/flux; old LPQA assumptions are not transferable. All old research and step3
atd429783 retained. [Options/reviews](../optimization/COUPLED_DESIGN_OPTIONS.md).

## D-014 — Close step3 only in its preregistered vacuum domain and hand off

**Status:** accepted implementation of D-013 and its fixed completion rule
**Date:** 2026-09-14

The [two-domain follow-up](../qi/PLASMA_BALANCED_RESULTS.md) passes all ten final
gates with an actual new boundary and numerically resolved improvement. Close
step3 in the registered Goodman-nfp2 vacuum scope. Do not keep it open merely
because later SoTA/global-physics goals remain unqualified; equally, do not
promote this local action-variance result into better measured confinement or
power-plant performance. The known construction domains are not blind holdouts.
Preserve the rejected first design, all source-bound code/protocols and both
studies' resource/evidence records. Hand off steps1/2/3; no new search or automatic
steps4/5 without a new task. Existing foundation and coil failures are unchanged.

## D-013 — Explicit step3 authorization: optimize plasma, not another coil-only study

**Status:** accepted; new explicit user request after foundation handoff
**Date:** 2026-09-13

Step3 now active under the [plasma protocol](../qi/PLASMA_OPTIMIZATION_PROTOCOL.md).
Develop a changed nfp2 vacuum boundary with a numerically resolved improvement
in a bounded, independently checked QI-relevant domain. Earlier foundation
closure is retained, not expanded into global physics certification. No SoTA
requirement; nevertheless a runnable/negative search alone cannot close step3.
Use existing pinned solvers and source data, add code without replacing older
kernels/evidence, preregister all search/holdout gates. Do not start steps4/5.

## D-012 — Separate foundation capability from design performance

**Status:** accepted; explicit user correction
**Date:** 2026-09-13

Steps1/2 are now bounded reference-tool qualification and practical reproducible
iteration on fixed LPQA filament coils. They do not require a feasible new optimum,
five starts, SoTA improvement or SQuID-C qualification. Old candidate failures and
limits remain unchanged. Known W7-X/output/netCDF limitations remain explicit.
Global QI/orbit/full-engineering qualification is deferred, not declared passed.
All previous work at5971fee remains preserved for later research. New24-bundle
smoke repeats and independent phase/audit aggregation qualify capability only.
After both refined milestones pass, hand off; do not automatically start later
research. Active contract: [foundation acceptance](../validation/FOUNDATION_ACCEPTANCE_PROTOCOL.md).

## D-011 — Resource preflight and truthful interrupted-run provenance

**Status:** accepted after disk-exhaustion incident
**Date:** 2026-09-12

Bound required source checkouts instead of materializing historical submissions.
Estimate disk needs plus reserve before large work, recheck between phases, and
separate heavy installation/build work from scientific searches. Retain original
checkpoints even when their last flag is running; append a terminal incident
record rather than inventing final state. Console progress is not persisted
progress. Only precisely identified disposable copies created by our current
workflow may be removed autonomously; never clear user caches or prior evidence.

## D-010 — Documentation is required after every completed work step

**Status:** accepted; explicit user requirement
**Date:** 2026-09-12

Update affected detail documentation and the validation log after each bounded
step, including negative findings, checks and blockers, before proceeding.
Check both repository/project READMEs, status, plan and the relevant folder index
for changes in the assessment or next action; keep them concise and synchronized.
Record material findings and durable decisions in the appropriate journals.
Validate links/layout and the intended diff, run proportionate tests, then commit
the scoped work. If committing is blocked, distinguish saved from committed work
explicitly; do not bypass permissions or silently defer documentation to session
end. The persistent checklist is in [AGENTS.md](../../AGENTS.md).

## D-009 — Keep documentation shallow, purpose-indexed and reviewer-readable

**Status:** accepted; explicit user requirement
**Date:** 2026-09-11

The docs root contains only the scientific overview, current assessment and work
plan. Detailed reports/protocols go into seven purpose-specific directories,
each with a complete explanatory README; no third level is permitted. Persistent
instructions are in [AGENTS.md](../../AGENTS.md), with automated layout/link tests.
Historical evidence is not rewritten. Original document paths and hashes are
preserved in the migration manifest; current scientific scripts change only
document paths. New findings update both the relevant index and concise status.

## D-008 — Qualify the bounce-action measurement before a new QI objective

**Status:** accepted for first experiment
**Date:** 2026-09-09

Use an independently integrated, well-resolved action diagnostic with explicit
coverage and numerical convergence checks. The existing smoothed legacy residual
and alpha-averaged radial slope are insufficient as optimization certificates.
The prospective experiment is frozen in QI_MEASUREMENT_PROTOCOL.md. Its envelope
score is diagnostic; topology, branch matching and maximum-J remain separate work.

## D-001 — Use a baseline suite, not a single substitute for SQuID-C

**Status:** accepted
**Date:** 2026-08-30

W7-X is the physics/software regression, StellCoilBench is the method benchmark,
and an open QI equilibrium is the data-interface and QI-physics bridge. None is
misrepresented as SQuID-C or Stellaris.

## D-002 — Keep optimization method-neutral

**Status:** accepted
**Date:** 2026-08-30

AI is not an objective or privileged baseline. Methods are compared under equal
budgets, constraints, and independent evaluation. Surrogates and active learning
are introduced only after a strong classical baseline exists and only retained if
they show measured benefit.

## D-003 — Target a robust physics-engineering Pareto frontier

**Status:** accepted
**Date:** 2026-08-30

The intended contribution extends beyond filament-coil normal-field error. Finite
build, electromagnetic loading, stress/deformation, clearances, manufacturing
errors, and free-boundary plasma response are part of the target validation stack.

## D-004 — Use all three published Goodman QI vacuum cases

**Status:** accepted
**Date:** 2026-08-30

The one-field-period case is the primary open-QI regression because the source
paper reports that the method works especially well there. The two- and
three-field-period cases are mandatory transfer controls: they reduce the risk of
building a metric or optimizer that works only for the favourable nfp=1 class.

## D-005 — Do not equate local VMEC convergence with cross-code validation

**Status:** accepted
**Date:** 2026-08-30

A VMEC++ run is accepted as locally converged when its force residuals meet the
input tolerance. Cross-validation is reported separately against the supplied
Fortran wout and the pinned Proxima validation tolerances. A subset of matching
global quantities cannot be relabelled as a full validation pass.

## D-006 — Separate legacy QI reproduction from the optimization metric

**Status:** accepted
**Date:** 2026-08-30

The exact published QI residual remains a required regression, but its
non-monotone resolution study disqualifies it as the sole objective for new
designs. A replacement must have a predeclared mathematical definition,
resolution convergence, transfer across all three QI cases, and agreement with
independent trapped-particle or second-invariant diagnostics.

## D-007 — Certify feasibility from outputs, not optimizer status

**Status:** accepted
**Date:** 2026-08-30

An optimizer success flag is diagnostic only. Feasibility is recomputed from the
serialized candidate using predeclared thresholds and the independent
high-resolution holdout. A candidate that is within the optimization grid's
tolerance but crosses a refined clearance or curvature bound is infeasible.
