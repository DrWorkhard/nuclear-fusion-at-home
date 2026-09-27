# Step 4 research programme: calibration, feasibility and an open challenge

26 September 2026. Prospective priorities following the
[strategic review](../review/STRATEGIC_REVIEW.md), not new execution results.
[Roadmap](../PROJECT_PLAN.md) · [Scientific status](../STATUS.md) ·
[Two research lanes](../validation/RESEARCH_WORKFLOW.md)

## Near-term question

Can a useful coil family approximate these targets under defensible geometric
constraints? Answer this before investing in a longer protected local search.
The latest small gains are evidence of useful local motion, not evidence of
reachability or impossibility. The Step 4 limits remain unchanged pilot criteria,
not universal reactor standards. Steps 4A–4D and MS1 remain open.

## First decision window: by 10 October 2026

1. The [registered saved-field diagnosis](FIELD_RESIDUAL_RESULTS.md) is complete.
   Its eight comparisons show weak normalized-residual alignment relative to the
   raw objective. Use this to motivate objective/start comparisons, not to infer
   that other coil directions cannot succeed.
2. The [matched boundary calibration](REFERENCE_CALIBRATION.md) now supplies a
   QUASR boundary-positive control and reproduces LPQA's archived mean/max at the
   tested settings. Its 13 rows distinguish collocation error, flux clipping and
   RMS definitions. This completes a component comparison, not an end-to-end
   Goodman/current/geometry calibration; data rights still need verification
   before a new portable export.
3. If a suitable control is missing, record the exact missing data or adapter;
   do not substitute a different surface, a rescaled coil or an analytic unit
   test and call the physical gates calibrated. Analytic controls are still useful
   for units/signs, but answer a different question.

The calibration record must map target/equilibrium, coil count and symmetry,
currents/flux normalization, length units, physical scale, winding assumptions,
normal-RMS versus raw/normalized flux definitions, area weights, resolution and
clearance/curvature definitions. LPQA benchmark flux failures and QI-target
normal-RMS failures are not the same quantity or evidence of the same limitation.
Match vacuum/pressure/plasma-current assumptions and the interior target before
interpreting the vector gate. Select controls for source/definition completeness,
not by trying cases until one passes; absent data is not a failed physics gate.
The existing [LPQA reconstruction](UPSTREAM_LPQA_RECONSTRUCTION_RESULTS.md)
and [inventory](UPSTREAM_LPQA_INVENTORY_RESULTS.md) provide a local metric-control
starting point, not a known-good Goodman-target design. The inspected Goodman
manifest supplies equilibria, not matching author coil sets. No global assertion
about public coil-data availability follows from this local inventory.

**Decision:** if author metrics cannot be reproduced, repair or explain the
comparison before interpreting gate failures. If they reproduce but our gates
reject, report which stricter requirement is responsible. This does not prove
our thresholds are wrong or the target unreachable. Any justified new profile
requires separate rationale, versioning, review and fresh evaluation of all
controls; retain the old verdicts. A synthetic positive control is not a
substitute for a relevant physical design.

## Exploration window: through 24 October 2026

Use a maximum of ten active research sessions in the exploratory lane, with a
ceiling recorded before each local run (initial default: 30 minutes, 3 GiB start /
2 GiB live disk reserve). Reuse existing optimizers/evaluators. Contributor compute
disclosure remains optional; these limits govern our own executions only.

Explore stage-2 coil fitting in a small, documented matrix: existing versus
alternative geometry-feasible starts; raw-field versus normalized-error objectives;
and clearance/curvature trade-offs. Broader coil counts, current freedoms or
topologies are separate identified families, not silent changes to a comparison.
Sampled geometry can guide exploration cheaply, but only separately checked
continuous geometry earns a certified label. Report both sampled and certified
fronts, uncertified cases and actual violations distinctly. Freeze shortlisted
candidates before finer checking; fine results consulted during exploration are
not confirmation holdouts.

Four exploration sessions are complete: the [objective comparison](NORMALIZED_OBJECTIVE_EXPLORATION.md)
improves error only with geometry violations, and the [static start screen](COIL_START_SCREEN.md)
finds curvature freedom without a better starting field. [Constraint-aware fitting](CONSTRAINED_COIL_EXPLORATION.md)
and an adaptive saved-point check give a geometry-checked fit at RMS 0.1517;
lower sampled errors have unresolved
clearance. [Independent-current raw fits](INDEPENDENT_CURRENT_EXPLORATION.md)
reduce their objective but worsen normalized field error. Session 5 tests the
local-normalized objective using those saved field responses.
Source-bound failed
attempts remain in each result record and are not omitted from effort accounting.

At the earlier of ten sessions or 24 October, publish the reachability map or the
specific blocker. Use **fine normal RMS below 1e-2 with unchanged geometric gates**
as a triage signal for further local fitting, not a new acceptance threshold
(the old RMS limit is still 1e-4). Retain current, maximum normal and interior
errors as well. If no candidate reaches that signal, stop automatic continuation
of this local-search family and choose a different initialization/coil family,
objective or target using the measured trade-offs. Failure within a time box is
not a proof of infeasibility. If a signal appears, compare it fairly with the
matched reference before committing a larger budget.

The previously reviewed one-step protected continuation remains an optional
integration test, not the default next scientific objective. No new native run
is authorized merely by this programme or its dates.

## MS0: a useful open benchmark within six months

Target **26 March 2027**: an attributed, portable coil benchmark/challenge, with
calibrated interpretations of its gates, a published negative/positive-control
matrix and at least one reproduction on a separate machine. A well-explained
negative benchmark can satisfy this milestone; an accepted reactor design is
not required. This creates value before a possible Proxima comparison.

Deliver incrementally:

- By **26 October 2026**, prepare a portable Step 4 reference challenge and four
  issue-ready tasks below, or document the precise data/license/model blocker.
  This is a target, not a claim that the current sparse starter already does it.
- Publish only after the [launch checklist](../validation/REVIEW_POLICY.md#launch-checklist--requires-actual-hosting-work)
  clears the exact release/history and the owner authorizes hosting. Obtain real
  CI and a discussion/review channel; do not invent a URL or maintainer identities.
- By **26 December 2026**, seek an authorized independent expert review of the
  Step 3 proxy's interpretation and Step 4 gate comparability; pursue a second
  physics-code comparison where a suitable matched calculation exists. Proxima
  outreach still waits for MS1; no outreach has been performed here.
- For MS0 completion, another person must reproduce the packaged case from a
  fresh machine/checkpoint without private paths or chat history. Record actual
  results, not just a checksum match or same-machine agent review.

### Minimum challenge contract

Package a fixed, licensed coil/target pair, explicit named coefficients/currents,
units and symmetry, dense reference grids, geometry limits and trusted evaluator
revision. Support candidate → full-grid evaluate → independent replay with no
maintainer-local paths. Include continuous geometry checks and refinement-aware
scores; name unsupported finite-build/topology/pressure physics explicitly.
Publish size/dependency requirements and test the package in a disposable clean
checkout before claiming portability. Export new identifiers; never rewrite
historical paths/hashes in place.

A leaderboard, once hosted, must separate exploratory scores, numerically checked
results and fully accepted entries for this profile. Show field/current/geometry
trade-offs and rejected gates; no single score implies a reactor advantage.
Unsolicited methods remain welcome, and compute spending is not a ranking rule.
The contribution value is reproducible cross-tool evidence and design challenges
that can also benefit upstream SIMSOPT/StellCoilBench, not replacing those tools.

### Four issue-ready tasks (not yet hosted issues)

| Task | Reviewable completion |
| --- | --- |
| Matched reference and metric crosswalk | Attributed coil/surface pair; reproduced author metric; explicit differences from our profile, including negative gates |
| Portable target/coil export | Licensed, hash-bound minimal package; fresh-checkout replay without local paths; old evidence untouched |
| Full-grid and continuous-geometry adapter | Trusted evaluate/replay path with fixed identities, adversarial negative controls and scoped numerical checks |
| Independent reproduction / counterexample | Exact release and observed outcome on another machine, or a preserved failure of the public/expanded checks |

## Preservation and review indicators

Backup status is **not verified**. Before claiming durable preservation, the
maintainer must select an independent storage destination, copy the Git bundle,
pinned-source identities, necessary environment recipes and full reachable result
graphs, then restore a representative result and verify its hashes. A copy on the
same disk is not an independent backup. Do not delete local artifacts after export.
Major-result DOI archives follow rights/privacy review and explicit publication
authority; portable derivatives retain a manifest mapping to original evidence.

Track at each decision window: best fine RMS with certified geometry; matched
controls reproduced / controls passing each gate; covered design families;
question-to-answer time and science/tooling effort when recorded; external
reproductions/expert reviews; archive/restore status. Baseline evidence is on the
[status page](../STATUS.md); unknown values stay unknown. Calendar targets neither
schedule background work nor make a missed scientific result complete.
