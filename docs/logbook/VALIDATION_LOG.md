# Current verification

Updated 27 September 2026. Latest completed work, not an append-only history.
Git retains previous versions; canonical result pages retain scientific checks
and failed attempts.

## Alternative coil starts: completed static comparison

Twelve field/loop rows complete in 6.362 s (6.734 s supervised); 15,219,993 run
bytes are retained. This was a dirty, source-hash-bound exploration at `566a6ab`,
not clean-commit confirmation. Shape100 retains the lowest starting error;
circle100 offers more curvature margin. All four fail boundary-error limits.

Checks actually performed in the existing `.venv`:

- **11 focused tests pass** (0.33 s), independently rerun (0.32 s): named
  geometry mapping, fresh current normalization, frozen fine scale, replay,
  serialization and execution bounds.
  `artifacts/coil-start-screen-v1/implementation-tests.xml`.
- Independent audit rehashes **22 sources**, launcher/question and **12 NPZs**;
  checks snapshot/construction/audit links, signed currents and unchanged geometry.
- Separate arithmetic reproduces **144 boundary metrics**, twelve normalized-raw
  values and **twelve complete saved-loop-A integrals**. All 768 B and 768 A
  independent samples pass; maximum discrepancies 1.009e-15 / 1.390e-16.
- All twelve rows, B=1152 / A=40 / independent=24 requests, source stability,
  exact current freezing, Shape100 replay and external limits are checked.
- Relative flux residual is at most 8.882e-16. This is saved-loop replay plus
  independent point checks, not a full independent Stokes test. No new geometry
  certificate or physical admission is asserted.

The [result record](../optimization/COIL_START_SCREEN.md) and
[evidence manifest](../../evidence/coil-start-screen-v1.json) bind the actual
data and pre-run question. **47 public tests pass** (3.433 s). Scoped Ruff,
documentation structure and whitespace checks pass. No full native regression
is claimed.

## Completed matched boundary calibration

The [result page](../optimization/REFERENCE_CALIBRATION.md) retains the 13-row
study, all 156 independently reproduced metrics, 832 sampled field comparisons
and direct QUASR tensor-surface reconstruction. QUASR is a boundary-component
positive only; LPQA reproduces archived mean/max under the tested convention.
This does not establish a complete Goodman positive or Step 4 acceptance.

## Other scoped checks

- [Objective comparison](../optimization/NORMALIZED_OBJECTIVE_EXPLORATION.md):
  160 coarse bundles, four fine screens, independent arithmetic and explicit
  curvature witnesses; both endpoints infeasible. Its first cache-identity
  failure and 28 implementation / 101 reused-component tests remain documented.
- [Residual diagnosis](../optimization/FIELD_RESIDUAL_RESULTS.md): eight saved
  comparisons complete at clean `7b4ec75`; independent source/arithmetic audit.
- [Fixed field comparison](../optimization/FIXED_FIELD_PROBE_RESULTS.md): its
  source-bound 5,654-test regression predates later edits, not current full coverage.
- [Public release results](../validation/PUBLIC_RELEASE_RESULTS.md): exact dated
  portability checks and unverified hosted coverage.

No hosted CI, external peer review, release or pressure/engineering validation
is claimed by this maintenance record.
