# Protected saved-physics reconstruction

26 September 2026. [Registration](PROTECTED_PHYSICS_PROTOCOL.md) ·
[Execution plumbing](PROTECTED_NATIVE_PLUMBING_RESULTS.md) · [Index](README.md)

## Assessment

The independent saved-physics auditor and historical qualification driver are
implemented and **qualified in the registered saved-data scope**. All 130
synthetic tests, all eight real historical seed reconstructions and all 3,363
tracked regression tests at `2ac95db` pass, with a separately authored internal
review. The inactive next-stage launcher remains separately unqualified.

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
independently reviewed both.

## Actual historical evidence and committed-source regression

At `2ac95db`, the actual eight saved native seed bundles pass independent
reconstruction. Six B/A comparison statistics per case cover **3,072 sampled
vectors / 9,216 scalar components**; maximum relative disagreement is
**1.316e-15**, against the unchanged 5e-10 threshold. Two distinct geometry
certificates are independently recomputed and agree with four actual recorded
producer proofs. The method/target combinations share those original geometries;
they are not eight independent geometric certificates.

The reconstructed coarse field errors remain **0.269149–0.276109 normal RMS**
and **0.361571–0.372173 inner-vector RMS**, against physical limits 1e-4 and 0.01.
This confirms the earlier negative results, not a design improvement. No native
model/request, producer certificate, equilibrium solve or search was executed.
The new protected startup stencil still needs its own native runtime checks.

Full **tracked** research regression passes 3,363 tests, 334 existing warnings,
zero failures/errors/skips, exit zero; 286.74 s console / 286.655 s JUnit.
The two untracked, inactive next-stage launcher test paths were explicitly
excluded; neither was present when the run started. No committed test was omitted.
Those prototypes are outside this qualification and were not imported by the
historical qualifier. The whole checkout was not clean; tracked files and all
qualified scientific source bytes remained unchanged. The environment was not
resynchronized. Both complete regression outputs are retained.

The [qualification record](../../evidence/protected-saved-physics-v1.json) binds
11 sources and 23 artifacts, including both retained driver failures and the
complete actual-data evidence. Native execution next requires the separately
reviewed launcher and a committed execution checkpoint. Fine-grid acceptance,
realized-field transfer and Step 4B–4D remain open.
