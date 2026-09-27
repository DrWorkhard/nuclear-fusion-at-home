# Current verification

Updated 27 September 2026. Latest completed work, not an append-only history.
Git retains previous versions; canonical result pages retain scientific checks
and failed attempts.

## Constraint-aware fitting: adaptive saved-point checks complete

An adaptive check of two saved full-mode points performs no new optimization.
Four fine screens complete in 6.022 s (6.386 s supervised), four geometry levels
in 24.086 s (24.338 s supervised). Execution is dirty but source-bound at
`e0f45e1`; the original four-arm experiment remains unchanged.
Shape trial 52 passes scoped continuous geometry at RMS 0.15168, 45.05% below its
own seed with 10.11% more current. Circle trial 126 has unresolved clearance.
All boundary-error limits still fail; these are adaptive exploratory checks.

Latest independent checks actually performed in the existing `.venv`:

- Rehashed all **1,573 files** in the original experiment manifest and recreated
  all sixteen inspected filter choices from 744 unchanged hashed trials.
- Verified the two frozen trials/seeds, **36 replay / seven geometry sources**,
  four fine array hashes and preserved coarse currents.
- Separate arithmetic reproduces **48 fine metrics**, four full saved-loop-A
  integrals and all **256 B / 256 A** comparisons.
- Four geometry levels: independently checked 1,104 coil-pair / 96 plasma bound
  rows and 24 tighter curvature enclosures. Shape's plasma lower bound is
  80.713670 mm; circle's is 79.825504 mm, unresolved rather than a failure.
- No full distance-grid rerun, new native audit fields, directed interval proof
  or complete self-disjointness is claimed.

Implementation and original experiment checks supporting this replay:

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
[adaptive evidence](../../evidence/constrained-coils-slack-v1.json) bind the
latest checks to the immutable original study. **47 public tests pass**. Scoped Ruff,
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
