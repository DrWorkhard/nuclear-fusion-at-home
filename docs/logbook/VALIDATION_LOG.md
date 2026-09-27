# Current verification

Updated 27 September 2026. Latest completed work, not an append-only history.
Git retains previous versions; canonical result pages retain scientific checks
and failed attempts.

## Matched boundary calibration

Added a small exploratory metric crosswalk and fixed QUASR/LPQA comparison,
without modifying existing evaluators or gates. The first attempt failed before
fields on legacy generic surface labels. Physical tensor-slot mapping and a
regression test resolve that adapter mismatch; the failed prefix remains.

The retry completes all 13 fixed rows in 2.657 s (2.946 s supervised), below its
180/185 s ceilings. About 4.88 MB is retained. Native fields run in 128-point
blocks with one thread. Exact source hashes bind the uncommitted implementation
atop `9270692`; this is exploratory, not a clean-commit confirmatory result.

Checks actually performed in the existing `.venv`:

- **42 metric/representation tests pass** (1.50 s), including independently
  formulated sums, current/area scaling, named coils and legacy tensor labels.
- All **13** independent sampled-field comparisons pass, largest normalized
  discrepancy **8.742e-16**. All **39** native scalar-integrator comparisons pass.
- Read-only independent replay verifies 17 source and 13 array identities,
  13 complete rows, **156** independently summed scalar metrics and **832** saved
  field-point comparisons. LPQA's archived mean/max reproduce to about 1e-18.
- Independent direct tensor-series reconstruction from all 661 QUASR source
  coefficients reproduces four saved position/normal grids without SIMSOPT;
  normalized normal-vector error is at most 3.769e-15.
- **47 public tests pass** (3.385 s). Scoped Ruff, documentation structure and
  whitespace checks pass. No full native regression was run for these isolated
  exploratory additions.

The [result page](../optimization/REFERENCE_CALIBRATION.md) explains collocation,
refinement and mean/RMS differences; the
[evidence record](../../evidence/boundary-control-calibration-v1.json) binds all
rows and both attempts. QUASR is a boundary-component positive only. Neither
case establishes complete Goodman acceptance or Step 4 completion.

## Other scoped checks

- [Residual diagnosis](../optimization/FIELD_RESIDUAL_RESULTS.md): eight saved
  comparisons complete at clean `7b4ec75`; independent source/arithmetic audit.
- [Fixed field comparison](../optimization/FIXED_FIELD_PROBE_RESULTS.md): its
  source-bound 5,654-test regression predates later edits, not current full coverage.
- [Public release results](../validation/PUBLIC_RELEASE_RESULTS.md): exact dated
  portability checks and unverified hosted coverage.

No hosted CI, external peer review, release or pressure/engineering validation
is claimed by this maintenance record.
