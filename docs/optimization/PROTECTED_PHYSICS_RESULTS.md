# Protected saved-physics reconstruction

26 September 2026. [Registration](PROTECTED_PHYSICS_PROTOCOL.md) ·
[Execution plumbing](PROTECTED_NATIVE_PLUMBING_RESULTS.md) · [Index](README.md)

## Assessment

The independent saved-physics auditor and historical qualification driver are
implemented. **130 synthetic tests pass**, including a separately authored
internal review rerun. Real saved-seed reconstruction and full source-frozen
regression are next; this component is not yet fully qualified.

The calculations reuse the unchanged, separately implemented metric, sampled
Biot–Savart and cumulative-certificate auditors. No new native optimization,
equilibrium, producer-certificate or target calculation has run. This is not a
better coil design, physical admission or Step 4 completion.

## Boundaries

`reconstruct_bundle(bundle, context, target_context)` checks a complete numerical
bundle and independently reconstructs its objective, metrics and six sampled B/A
comparisons: 384 vectors / 1,152 scalar components. Both numerical methods and
coil classes retain the original normalization, coordinates and tolerances.

`audit_saved_cell(result_reference, context, source_manifest, output=...)` first
rebuilds the expected original context and requires complete saved-graph integrity.
It then checks every cumulative certificate and every numerical bundle, including
negative certificates and current/Armijo-rejected trials. Ten reconstructed startup
values feed eight recorded/reconstructed directional checks. Selected-versus-seed
changes use reconstructed metrics, not the producer's reported values.

Full proofs and bundle reports are immutable separate files, referenced by the
aggregate; a 128-proof synthetic case exceeds 17 MB without breaching the unchanged
8 MiB per-JSON cap. Failed publications never return completed report references.

The core cannot authenticate supplied source admission or execution acknowledgement;
the [separate launch connection](PROTECTED_PILOT_EXECUTION_PROTOCOL.md) must do so.
It also does not verify every full-grid field value or gradient component. Scope
flags for those claims, fine acceptance, physical admission, Step 4, SoTA and MS1
remain false. Recorded native startup gates run before search; reconstructed startup
checks are posthoc before completed evidence can be accepted.

## Verification so far

- Core: 69 tests pass (15.70 s); initial 64-pass run retained. Tests exercise both
  classes/methods, negative and positive histories, all 128 certificates, canonical
  arrays, full context identities, selected changes, actual frozen-metric mismatch
  rejection and resource/publication failures. Initial formatting findings fixed.
- Historical driver: 61 tests pass (0.54 s), with numerical/source work stubbed.
  It binds the complete plumbing qualification and its own committed sources.
  It will reconstruct two distinct original geometry certificates against four
  actual recorded producer proofs, and all eight historical native seed bundles.
- Independent review: 130 pass, no failures/errors/skips, 15.51 s console /
  15.139 s JUnit. All four code/test hashes stay unchanged through the review.
- Retained driver failures: 57 pass/four fail for swallowed storage poisoning;
  fixed with post-publication in-memory health checks. Then 60 pass/one fail for
  the reported disk minimum omitting the final observation; fixed by constructing
  the terminal summary after the last resource guard, without a post-write guard.

Evidence is under `artifacts/protected-physics-v1/`. These are internal checks,
not external peer review. The core and driver were implemented by
`protected_budget_impl` and `protected_runner_map`; `cell_integration_review`
independently reviewed both. Qualification closure and actual-data results follow.
