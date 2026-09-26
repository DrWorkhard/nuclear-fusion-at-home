# Protected runner execution components: results

26 September 2026. [Registration](PROTECTED_RUNNER_PROTOCOL.md) ·
[Method review](PROTECTED_METHOD_REVIEW.md) · [Index](README.md)

## Current assessment

Four new execution components pass **390 focused synthetic tests** after adversarial
review and corrections. Full regression, committed-source binding and the new
real-data source preflight remain pending. These are not yet a qualified integrated
native runner. No new field search, equilibrium calculation or physical design
improvement has been performed.

| Component | Interface and checked scope | Focused tests |
| --- | --- | ---: |
| Source admission | `protected_coil_fit_inputs.sources(root)`: prior immutable graphs, accepted 52-state qualification, retained four physical field failures, eight original seed bundles | 199 |
| Work ledger | `ProtectedRunLedger`: model/certificate/bundle wrappers, exact phase budgets and native callbacks, durable reservations, permanent failure state | 109 |
| Raw snapshots | `SnapshotStore.json/arrays`, `read_json/read_arrays`: exclusive POSIX persistence, finite canonical data, checked byte references, bounded headers before allocation | 56 |
| Startup/replay helpers | `points`, `derivative_screen`, `exact_bundle_replay`: low-mode probes, numerical derivative checks, exact recorded/independent seed repeat and equality of supplied bundle data | 26 |

The ledger's maximal synthetic sequence records 904 journal events, 128
certificates, 32 bundles, two model initializations and 290 native requests.
Synthetic counted-field adapters invoke no native physics. Publication descriptors
are checked structurally by the ledger; verifying their actual files, source
identity and physical contents remains the integration/auditor's job.

The startup equality helper reports `bundle_schema_verified=False`: equality of
two supplied objects does not prove a complete valid coil-field bundle. Integration
must first enforce the native snapshot and 16-array schema against its admitted
historical reference. These helpers alone do not verify every gradient component.

## Independent reviews and retained failures

Three delegated agents contributed bounded work: `protected_runner_map` implemented
source admission; `protected_budget_impl` implemented the ledger and reviewed the
startup/source checks; `protected_method_review` reviewed the method, snapshot
store and ledger. The maintainer implemented snapshots/startup helpers and
integrated fixes. These are internal reviews, not external peer review.

Follow-up review confirms the reported defects are fixed. `protected_runner_map`
independently rechecked ledger reentrancy after the first reviewer's service was
interrupted: 109 tests pass and 32 additional inline synthetic hook-boundary
controls pass. That JUnit is retained; the extra inline controls are reviewer
observations, not a separately committed test suite. `protected_budget_impl`
rechecked both startup classes and all six invalid seed-flux controls. Snapshot
review verified the corrected byte bounds and supplied the retained ZIP64 fixture.

1. **Swallowed callback failure:** initial ledger expansion had 84 passes/four
   failures. An external hook could suppress an error and let its containing
   operation be acknowledged. Explicit poisoned-state checks after hooks fixed it;
   the 88-test repair passes. Failed JUnit is retained.
2. **Reentrant budget overspend:** independent review used a valid 115-certificate
   prefix and a reentrant guard to produce 117 completions against a 116 cap.
   Added controls exposed six failures (103 passes), including native callback
   reentry. Guard/record hooks are now explicitly non-reentrant, and even swallowed
   inner errors poison the outer operation. All 109 ledger controls pass.
3. **Early allocation limits:** review found JSON parsing before the 8 MiB check
   and ZIP directory allocation before the 64-entry check. Limits now precede those
   parsers. A further crafted ZIP64 override made standard `ZipFile` allocate 66
   entries despite a one-entry ordinary header; explicit ZIP64 rejection plus the
   bounded actual-directory scan stops it before parsing. Tests retain this fixture.
4. **Collapsed startup probes:** huge synthetic coordinates rounded every proposed
   displacement back to the seed yet passed a zero-gradient screen. A retained red
   run has 24 passes/two failures, also exposing mismatched independent repeat
   values. The represented central direction must now be within `1e-8` in Euclidean
   norm of its registered unit direction; independent seed/repeat values must be
   bit-identical. This added fail-closed numerical guard leaves the original FD
   acceptance limits unchanged and was fixed before any native study.
5. **Seed-flux coercion:** the pure source gate accepted boolean or NumPy scalar/
   one-element-array `seed_unit_flux` when compared to float `1.0`. Three red tests
   (196 passes) are retained. Typed identity now rejects all three. Historical
   byte pins already prevented those alterations in actual admitted source data.

Initial line-length/import-format checks also failed and were corrected. All
current changed-source Ruff checks pass. Raw and corrected JUnit histories are
retained under `artifacts/protected-runner-v1/`; first-development sources were
uncommitted, so their exact initial bytes are not claimed to be independently
archived. The final committed qualification will bind current sources separately.
Implementation checkpoint checks: 47 public tests pass in 3.863 s; 14 documentation/
release tests pass in 0.56 s. Documentation, repository Ruff and whitespace pass.

## Source availability and remaining work

The existing predecessor binder passed a read-only check in 18.462 s: both geometry
seeds, both 401-surface target files and archived64 normalization are available.
This was not execution of the new binder or a native field calculation. The new
binder's real-data call follows its implementation commit.

Next: finish component qualification, then assemble a source-bound worker with
immutable raw manifests and separate controller/native journal receipts. Test the
whole ten-startup → search → fresh-selected-replay sequence with synthetic models,
including failure prefixes. Independently reconstruct physical fields, objectives,
geometry and runtime FD checks before starting a native experiment. Preserve the
two-model schedule and the review's historical-seed-only replay clarification.
All fine-grid, flux, topology/transfer and later 4B–4D gates remain separate.
