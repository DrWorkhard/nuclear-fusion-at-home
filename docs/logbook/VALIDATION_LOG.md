# Current verification

Updated 27 September 2026. Latest completed work, not an append-only history.
Git retains previous versions; canonical result pages retain scientific checks
and failed attempts.

## Constraint-aware fitting: completed exploratory comparison

Four arms complete 744 bundles and eight fine screens in 148.426 s (149.177 s
supervised), retaining 29,713,557 search bytes. Execution is dirty but source-bound
at `b54eda4`. One candidate passes scoped continuous geometry at RMS 0.22350,
27.59% below its own seed with 13.91% more current. Lower sampled scores have
unresolved clearance. All boundary-error limits still fail.

Checks actually performed in the existing `.venv`:

- **53 combined experiment tests pass** (13.27 s): fourteen new synthetic
  constrained-search tests, 28 objective/cache tests (including a native circle),
  and eleven static-screen tests. The independent reviewer reran all fourteen
  new tests (0.54 s). `artifacts/constrained-coils-v1/implementation-tests.xml`.
- **Five reused curvature tests pass** (0.14 s), plus the retry serializer check.
- Independent search audit checks 30 sources, all **744 trial/attempt pairs**,
  masks/boxes, actual selections and **sixteen directional derivatives**.
  Separate formulas reproduce 96 fine metrics and eight saved-loop-A integrals;
  all **512 B / 512 A** comparisons and selected physical-curve reconstructions pass.
- Geometry follow-up completes eight levels in 44.329 s (44.711 s supervised).
  Independent saved-data arithmetic checks seven sources, four snapshots, 2,208
  coil-pair / 192 plasma lower bounds and 48 tighter curvature enclosures.
  Result: one scoped pass, three unresolved clearances, not three proven failures.
  No full distance-grid rerun, directed interval proof or full self-disjointness.
- The first geometry attempt failed while serializing a NumPy Boolean (2.361 s).
  Its script/prefix remain intact; the fresh retry changes scalar serialization
  only, with unchanged numerics/gates. Neither geometry run calls native fields.

The [result record](../optimization/CONSTRAINED_COIL_EXPLORATION.md) and
[evidence manifest](../../evidence/constrained-coils-exploration-v1.json) bind the
actual data, both pre-run questions and failure. **47 public tests pass** (3.374 s). Scoped Ruff,
documentation structure and whitespace checks pass. No full native regression
is claimed.

## Completed matched boundary calibration

The [result page](../optimization/REFERENCE_CALIBRATION.md) retains the 13-row
study, all 156 independently reproduced metrics, 832 sampled field comparisons
and direct QUASR tensor-surface reconstruction. QUASR is a boundary-component
positive only; LPQA reproduces archived mean/max under the tested convention.
This does not establish a complete Goodman positive or Step 4 acceptance.

## Other scoped checks

- [Static start screen](../optimization/COIL_START_SCREEN.md): twelve boundary/loop
  rows, 144 independently reproduced metrics and preserved original geometry.
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
