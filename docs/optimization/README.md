# Optimization and coil design

Purpose: reproducible optimization evaluators, checked derivatives and controlled
searches on LPQA, plus paired coil realization of our QI-like plasma targets.

[Steps 1/2 are complete](../validation/FOUNDATION_ACCEPTANCE_RESULTS.md) as reference
and iteration capabilities. A new feasible optimum was not their completion
criterion. Step 4 remains **In progress**: current starting coils pass geometry
checks but their full-grid normal field error is roughly 0.27 versus a 1e-4 limit.

The best older LPQA coil search passes checked geometry limits but exceeds its
raw-flux threshold by a factor of 8.13. The audited Gauss–Newton follow-up improves
fine flux by 0.754%; exact current redistribution previously helped negligibly.
These studies establish neither a feasible new baseline nor a general method ranking.

[Overview](../README.md) · [Status](../STATUS.md) · [Roadmap](../PROJECT_PLAN.md)

## Current work and public contributions

- [Protected coil-fit results](PROTECTED_COIL_FIT_RESULTS.md). Eight native searches and independent coarse audits complete at `2015ac5`; normal RMS improves 0.4463–0.4857%, interior RMS 1.1881–2.1916%. All stop at the curvature certificate; mandatory fine phase remains unrun and field limits remain far away.

- [Fine acceptance registration](PROTECTED_FINE_PROTOCOL.md). Fixed eight-model/80-request schedule per selected case, original-seed/current identity, complete flux/refinement/geometry checks, explicit lossless mask codec and separate no-search supervision. Independently reviewed before implementation; native execution requires separate qualification/checkpoint.
- [Fine validation progress](PROTECTED_FINE_PROGRESS.md). Implementation qualified at clean `80dddb8`: 4,883 complete regression tests pass, including 142 final integration tests. Eight old initializer fluxes independently reproduced within 6.515e-16 relative error. Execution checkpoint remains open; no fine native execution yet.
- [Fine-phase integration notes](PROTECTED_FINE_DESIGN_NOTES.md). Preserved pre-registration mapping of candidate-coordinate and seed-identity traps, geometry masks and reuse boundaries; the registration above now defines the implementation task.

- Protected pilot execution: [registration](PROTECTED_PILOT_EXECUTION_PROTOCOL.md), [results](PROTECTED_PILOT_EXECUTION_RESULTS.md). Launcher qualified at `6bb1e45`: 124 synthetic tests and all 3,487 regression tests pass; runtime clean-source admission and the subsequent pilot pass at `2015ac5`. Original budgets/fine requirements unchanged.

- Independent saved physics: [registration](PROTECTED_PHYSICS_PROTOCOL.md), [results](PROTECTED_PHYSICS_RESULTS.md). Scoped qualification complete: 130 synthetic tests, eight real saved-seed reconstructions and 3,363 tracked regression tests pass. Maximum sampled B/A error 1.316e-15; earlier physical rejections confirmed. Native launch and fine acceptance remain separate.

- Native plumbing: [registration](PROTECTED_NATIVE_PLUMBING_PROTOCOL.md), [results](PROTECTED_NATIVE_PLUMBING_RESULTS.md). Qualification complete: 315 focused and 3,233 full-suite tests pass; all eight real saved contexts/source-bound adapters validate read-only. No native pilot or physical acceptance follows from this software gate.
- Protected cell integration: [registration](PROTECTED_CELL_PROTOCOL.md), [results](PROTECTED_CELL_RESULTS.md). Synthetic qualification complete: 299 focused tests, 2,918 full-suite passes and eight historical schema comparisons, with reviewed fixes and source/artifact binding. Native launching and physical acceptance remain separate.
- Protected runner execution components: [registration](PROTECTED_RUNNER_PROTOCOL.md), [results](PROTECTED_RUNNER_RESULTS.md). Scoped qualification complete: 390 synthetic tests, 2,619 full-suite passes and successful real-data source preflight after independently reviewed fixes. Integrated orchestration and physical acceptance remain separate.
- [Second protected-fit method review](PROTECTED_METHOD_REVIEW.md). Independently authored internal support for a bounded diagnostic pilot, conditional on remaining execution/physical gates; seed-only historical replay, exact two-model schedule and no unresolved fine-improvement claim.
- Protected runner storage: [protocol](PROTECTED_RUNNER_STORAGE_PROTOCOL.md), [results](PROTECTED_RUNNER_STORAGE_RESULTS.md). Qualified in its single-writer POSIX scope: 47 event-journal checks, 108 controller/auditor checks and a 2,229-pass full-regression report, with source/artifact identities bound. Source/native-budget orchestration and physical verification remain separate prerequisites.
- Protected-search software qualification: [protocol](PROTECTED_SEARCH_SOFTWARE_PROTOCOL.md), [results](PROTECTED_SEARCH_SOFTWARE_RESULTS.md). Complete in its synthetic scope: 108 controller/auditor tests and 2,180 full regression tests pass. Runner, method review and physical recomputation remain; no new field fit or physical claim.

- [Research hints](RESEARCH_HINTS.md). Nonexclusive invitations: reproduction, kernels, counterexamples, geometry-preserving improvement and broader physics. Unsolicited useful work welcome; costs optional.
- [Original protected field-fit registration](PROTECTED_COIL_FIT_PROTOCOL.md). Preserved eight-cell low-mode proposal with its historical paused heading unchanged. Later method/software qualifications and coarse execution are linked above; the required fine phase and physical acceptance remain open.
- [Geometry-preserving search options](GEOMETRY_PRESERVING_SEARCH_OPTIONS.md). Two independent recommendations; qualify cumulative geometry bounds first. Free L-BFGS-B, support families and free currents remain separate options.
- [Coupled-design options and reviews](COUPLED_DESIGN_OPTIONS.md). Filament co-design, reduced directions, REGCOIL and direct surfaces; three internal agent reviews, integration traps and separate realization/coupling/pressure/robustness work packages.
- Paired actual-coil pilot: [protocol](COUPLED_COIL_PILOT_PROTOCOL.md), [negative results](COUPLED_COIL_PILOT_RESULTS.md). Two plasma targets, two coil classes and normal/interior-vector methods. Eight startup checks, six searches, all finer acceptance checks; no physical pass. Coarse grids missed very small plasma clearances.
- Geometry-to-field starts: [protocol](CLEAR_COIL_FIELD_START_PROTOCOL.md), [results](CLEAR_COIL_FIELD_START_RESULTS.md). Four cells, six resolutions, 1,048 native requests, 768 B/A comparisons, 20 refinements and 252 flux checks. Numerics, geometry and current pass; all four fail physical field limits.
- Blocked native reference: [protocol](BLOCK_NATIVE_REFERENCE_PROTOCOL.md), [results](BLOCK_NATIVE_REFERENCE_RESULTS.md). Four full-size resource runs in 64 surface blocks and 336 comparisons pass, at most 0.427 GiB/38.2 seconds. Three earlier memory failures remain preserved.

## Historical LPQA searches and diagnostics

Most detailed reports below remain in German. Protocols define the experiment;
results retain failures rather than relabeling them as design successes.

- Current-start Gauss–Newton: [protocol](CURRENT_START_GN_PROTOCOL.md), [results](CURRENT_START_GN_RESULTS.md). Two exactly repeated 2,048-bundle searches with native Gram controls and all four acceptance phases. Fine flux 8.129882e-8, 0.754% gain; still rejected, no Pareto dominance.
- Geometric curvature: [protocol](GEOMETRIC_CURVATURE_PROTOCOL.md), [results](GEOMETRIC_CURVATURE_RESULTS.md). Two sources, 32 fields and full matrices verified. All six quadratic prediction signs correct; at least 99.60% less prediction error. Local diagnosis, not a new design.
- Geometric descent: [protocol](GEOMETRIC_DESCENT_PROTOCOL.md), [results](GEOMETRIC_DESCENT_RESULTS.md). Six independently certified radius linear programs, 32 native bundles and 250 checks. Derivatives pass; all six real steps increase flux and violate construction constraints.
- Fixed geometry / optimal currents: [protocol](FIXED_GEOMETRY_CURRENT_PROTOCOL.md), [results](FIXED_GEOMETRY_CURRENT_RESULTS.md). Exact three-dimensional least squares, QR/provenance controls, 114 independent checks and eight field holdouts. Best fine gain only 0.000016608%; both shapes remain infeasible.
- Composite-start SLSQP: [protocol](SLSQP_COMPOSITE_PROTOCOL.md), [results](SLSQP_COMPOSITE_RESULTS.md). Same starting physics, qualified start Jacobian and two 2,048-bundle arms. Exact replay and fine checks; geometry/native pass, flux 8.191665e-8 fails.
- Polishing-start derivatives: [protocol](POLISH_START_DERIVATIVE_PROTOCOL.md), [results](POLISH_START_DERIVATIVE_RESULTS.md). Two directions, three complex steps and independent real chain rule. All 120 pair rows and 35 audit checks pass; error ≤4.063e-11 supports rounding explanation. Earlier finite-difference failure retained.
- SLSQP polishing: [protocol](SLSQP_POLISH_PROTOCOL.md), [results](SLSQP_POLISH_RESULTS.md). Planned two 2,048-bundle arms; stopped after nine startup bundles on four distance derivatives, before solver start. Independent postmortem confirms failure classification.
- Alternative upstream start: [protocol](UPSTREAM_START_PROTOCOL.md), [results](UPSTREAM_START_RESULTS.md). First preselected archive case, fixed current sum and fresh qualification. Both search paths/fine checks complete; geometry/native pass, flux 8.955e-8 fails.
- Upstream LPQA reconstruction: [protocol](UPSTREAM_LPQA_RECONSTRUCTION_PROTOCOL.md), [results](UPSTREAM_LPQA_RECONSTRUCTION_RESULTS.md). Five fixed archive cases pass source/field cross-checks and geometric grid screens; true raw flux near 1e-6 rather than reported zero, all rejected against 1e-8.
- Upstream LPQA inventory: [protocol](UPSTREAM_LPQA_INVENTORY_PROTOCOL.md), [results](UPSTREAM_LPQA_INVENTORY_RESULTS.md). 5,301 source-checked reports, 27 nominally matching records and five unqualified reconstruction candidates. 2,954 thresholded zero reports do not establish zero raw flux.
- Natural augmented-Lagrangian recovery: [protocol](NATURAL_AUGLAG_RECOVERY_PROTOCOL.md), [results](NATURAL_AUGLAG_RECOVERY_RESULTS.md). Separate single-arm/prefix postmortem and unchanged two-arm repeat. Replays/geometry/native checks pass; flux remains 26.99 times its limit.
- Jacobian-scaled augmented Lagrangian: [protocol](NATURAL_AUGLAG_JAC_PROTOCOL.md), [results](NATURAL_AUGLAG_JAC_RESULTS.md). Separate x_scale=jac trial, same physics and budgets. Fully repeated/audited; 11.4% less flux but higher curvature, still 23.91 times the limit.
- [Field-strength audit](FIELD_STRENGTH_AUDIT.md). Tests whether reduced field amplitude alone explains lower raw flux, with fixed base-current sum and global-scale controls. No new threshold.
- Original natural-flux augmented Lagrangian: [protocol](NATURAL_AUGLAG_PROTOCOL.md), [interrupted results](NATURAL_AUGLAG_RESULTS.md). Least-squares residual rather than old quartic penalty. First 1,033-bundle arm and saved 700-bundle prefix verified; original study remains incomplete.
- SLSQP-1024: [protocol](DIRECT_SLSQP_1024_PROTOCOL.md), [results](DIRECT_SLSQP_1024_RESULTS.md). Equal maximum bundle budget to Gauss–Newton. New repeats exact, historical prefix/audit fails; geometry/native pass, flux rejected at 12.7 times the limit.
- Native field projection: [corrected protocol](GN_NATIVE_COVECTOR_PROTOCOL.md), [results](GN_NATIVE_COVECTOR_RESULTS.md). Consistent identity check without changing values, gradients or Gauss–Newton matrix. Two 1,024-bundle searches replay exactly; geometry/native pass, flux 24.7 times the limit.
- Saved Gauss–Newton failure point: [protocol](GN_FAILED_POINT_PROTOCOL.md), [results](GN_FAILED_POINT_RESULTS.md). Native state stability and independent derivatives pass; separately rounded field projection caused adapter identity mismatch.
- [Gauss–Newton failure replay protocol](GN_FAILURE_REPLAY_PROTOCOL.md). At most 29 bundles to reproduce the failed prefix and capture the full failure point, without changing thresholds.
- Gauss–Newton trust pilot: [protocol](GN_TRUST_PILOT_PROTOCOL.md), [stopped results](GN_TRUST_PILOT_RESULTS.md). Planned two 1,024-bundle repeats. Field/gradient identity fails after 28 complete bundles; second arm not started.
- Quadratic field model: [protocol](QUADRATIC_FIELD_MODEL_PROTOCOL.md), [results](QUADRATIC_FIELD_MODEL_RESULTS.md). Four saved steps, full native matrices and independent kernel audit. All signs correct; ≥99.907% less prediction error than linear model.
- [Composite local-descent results](DIRECT_DESCENT_COMPOSITE_RESULTS.md). Four real probes: smallest slightly improves, larger predicted descents strongly worsen flux; motivates quadratic model.
- Complex-step clearance: [protocol](COMPLEX_CLEARANCE_PROTOCOL.md), [results](COMPLEX_CLEARANCE_RESULTS.md). All 120 pair-direction derivatives agree at both fixed states to about 2.4e-12. Earlier difference-test failure preserved.
- Local descent diagnosis: [protocol](DIRECT_DESCENT_DIAGNOSTIC_PROTOCOL.md), [stopped results](DIRECT_DESCENT_DIAGNOSTIC_RESULTS.md). New direction check misses its fixed limit; no descent probes. Cancellation is a hypothesis, not an established fix.
- Direct SLSQP pilot: [protocol](DIRECT_SLSQP_PILOT_PROTOCOL.md), [results](DIRECT_SLSQP_PILOT_RESULTS.md). Exactly repeated 256-bundle run and independent selection check; geometry/native pass, flux fails, convergence unresolved.
- Direct inequalities: [qualification protocol](DIRECT_INEQUALITY_QUALIFICATION_PROTOCOL.md), [results](DIRECT_INEQUALITY_QUALIFICATION_RESULTS.md). Conservative smooth geometric constraints; all 138 derivative rows and independent/native metrics agree, before optimization.

## Historical evaluator and method controls

- Affine feasibility: [protocol](AFFINE_FEASIBILITY_PROTOCOL.md), [results](AFFINE_FEASIBILITY_RESULTS.md). Fixed coordinate scaling enables equal consumed budgets; both methods remain infeasible on holdout.
- [Batched qualification failure](BATCHED_QUALIFICATION_FAILURE.md). Original JSON serialization failure retained separately from successful retry.
- Batched spatial Jacobian: [protocol](BATCHED_SPATIAL_JACOBIAN_PROTOCOL.md), [results](BATCHED_SPATIAL_JACOBIAN_RESULTS.md). Analytic derivatives in 16 coil contractions, control formulae, matrix comparisons and repeated timing.
- Guarded feasibility: [protocol](GUARDED_FEASIBILITY_PROTOCOL.md), [results](GUARDED_FEASIBILITY_RESULTS.md). Geometry margins and finer curvature support repeatability, but field errors remain too large.
- [Guarded replay protocol](GUARDED_REPLAY_PROTOCOL.md). Independent reconstruction and conditioning diagnosis of a saved candidate.
- Normalized feasibility: [protocol](NORMALIZED_FEASIBILITY_PROTOCOL.md), [results](NORMALIZED_FEASIBILITY_RESULTS.md). Rescaled common evaluator with unchanged independent flux/geometry acceptance.
- Optimization evaluator: [protocol](OPTIMIZATION_ORACLE_PROTOCOL.md), [results](OPTIMIZATION_ORACLE_RESULTS.md). Named parameter space, vectors/Jacobians, budgets, repeats and retained setup failure.
- [Replay mapping correction](REPLAY_MAPPING_REMEDIATION.md). Runtime names changed positional parameter order; explicit named physical mapping fixes replay.
- Spatial flux factorization: [protocol](SPATIAL_FLUX_FACTORIZATION_PROTOCOL.md), [results](SPATIAL_FLUX_FACTORIZATION_RESULTS.md). Objective-preserving algebra on two physical states with derivative controls.
- [Point-local adjoint derivative protocol](SPATIAL_FLUX_LOCAL_VJP_PROTOCOL.md). Qualifies the same Jacobian through local vector-Jacobian products.
- [Spatial Gram check](SPATIAL_GRAM_CHECK.md). Independent identity for the extra positive-semidefinite Gauss–Newton term; no convergence claim.
- Spatial trust-region pilot: [protocol](SPATIAL_TRF_PILOT_PROTOCOL.md), [results](SPATIAL_TRF_PILOT_RESULTS.md). 128 proposals: better flux per proposal but substantially more time; both candidates infeasible.
- Timed spatial pilot: [protocol](TIMED_SPATIAL_PILOT_PROTOCOL.md), [results](TIMED_SPATIAL_PILOT_RESULTS.md). Two 300-second runs per representation with complete accounting; all four candidates independently rejected.

Historical content and hashes remain unchanged. Resolve old filenames with the
[migration manifest](../../manifests/documentation-layout-v1.json).
