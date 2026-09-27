# Current verification

Updated 27 September 2026. Latest completed work, not an append-only history.
Git retains previous versions; canonical result pages retain scientific checks
and failed attempts.

## Normalized-objective experiment: completed exploratory comparison

The corrected raw/local comparison at clean `5b744f2` completes 160 coarse
bundles and four fine screens in 37.224 s (38.027 s supervised). Both hit their
80-bundle caps. Source fingerprints remain unchanged; about 7.49 MB is retained.
Lower local-normalized RMS comes with higher current; both selected designs
violate geometric and field limits. No accepted design or gate change follows.

Checks actually performed in the existing `.venv`:

- **28 synthetic/native-circle experiment tests pass** (2.31 s), covering chain rule, current
  scaling, named mapping, derivative checks, exact repeats, budget and late-result
  rejection and interacting field caches. `artifacts/normalized-coils-v2/implementation-tests.xml`.
- **101 reused-component tests pass** (5.90 s): coupled fields, independent coil
  reconstruction, sparse geometry and boundary metrics.
  `artifacts/normalized-coils-v1/reused-components.xml`.
- **47 public tests pass** (3.546 s). Scoped Ruff, documentation structure and
  whitespace checks pass. Full native regression was not rerun.
- Independent audit verifies 22 loaded sources, nine project/question Git
  identities, nine native Python files against pinned Git, all 160 trial pairs,
  both selected minima and all eight real directional derivative checks.
- Separate `math.fsum` reconstruction reproduces **48 fine metrics**; **256**
  saved independent/native field comparisons pass. All twelve independently
  reconstructed curvature maxima agree; explicit witnesses prove both curvature
  failures. Independent geometry also confirms the raw plasma-gap failure.
- Reported flux closure is checked arithmetically, not independently re-integrated:
  loop-A arrays were not saved in this small comparison. Both arms now have 78
  distinct unit-flux values, resolving the old cache symptom.
- The first attempt at `e916c8d` remains an invalid comparison: its instrumented
  fields collided in the dependency graph. The failed prefix, shared-class fix,
  synthetic counterexample and unchanged thresholds are in the result record.

The [experiment record](../optimization/NORMALIZED_OBJECTIVE_EXPLORATION.md)
specifies actual budgets, source fingerprints and limits. The
[evidence manifest](../../evidence/normalized-coils-exploration-v2.json) binds the
complete run and retained invalid first attempt. Sampled geometry and numerical
agreement do not establish continuous acceptance or Step 4 completion.

## Completed matched boundary calibration

The [result page](../optimization/REFERENCE_CALIBRATION.md) retains the 13-row
study, all 156 independently reproduced metrics, 832 sampled field comparisons
and direct QUASR tensor-surface reconstruction. QUASR is a boundary-component
positive only; LPQA reproduces archived mean/max under the tested convention.
This does not establish a complete Goodman positive or Step 4 acceptance.

## Other scoped checks

- [Residual diagnosis](../optimization/FIELD_RESIDUAL_RESULTS.md): eight saved
  comparisons complete at clean `7b4ec75`; independent source/arithmetic audit.
- [Fixed field comparison](../optimization/FIXED_FIELD_PROBE_RESULTS.md): its
  source-bound 5,654-test regression predates later edits, not current full coverage.
- [Public release results](../validation/PUBLIC_RELEASE_RESULTS.md): exact dated
  portability checks and unverified hosted coverage.

No hosted CI, external peer review, release or pressure/engineering validation
is claimed by this maintenance record.
