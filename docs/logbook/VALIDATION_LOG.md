# Current verification

Updated 27 September 2026. This page records the latest maintenance check, not
an append-only session history. Git retains previous versions; individual result
reports retain the checks supporting their scientific claims.

## Residual diagnostic: completed and independently checked

Added a thin external 65 s supervisor for the registered saved-array analysis,
with explicit returned-reference acceptance and checked durable publication.
The worker reserves launcher bytes inside its unchanged 8 MiB output cap.
Original field evaluators, inputs, numerical tolerances and scientific protocol
remain unchanged. Clean execution at `7b4ec75` completes all eight comparisons in
1.836 s, with 55,702 scientific bytes and no new native work.

Checks actually run with the existing `.venv`:

- Residual producer, independent arithmetic, intake/runner and launcher: **203
  tests pass** (0.74 s); `artifacts/field-residual-v1/execution-final-checks.xml`.
- Public tests: **47 pass**. Documentation/release/README workflow: **32 pass**.
  Logs and command/return-code records: `artifacts/field-residual-v1/execution-readiness-checks/`.
- Documentation structure, repository Ruff and whitespace: pass.
- Independent mathematical/intake review found no blocker in the fixed study.
  Its additional synthetic sweep passes 121/128: seven single-point perfect-fit
  rounding comparisons fail closed; all 96 multi-point comparisons pass. The
  first counterexample is now an expected-rejection test, without relaxed limits.
- Launcher review identified unchecked short writes; count/flush/fsync/readback
  checks and three synthetic publication-failure tests address that issue.
  Independent final rerun: 203 pass in 0.73 s; no remaining scoped execution blocker.
- Post-run independent audit verifies 64 files / 40,040,460 bytes, nine Git source
  identities and 496 separately reconstructed scalar values. All eight comparisons
  and sixteen model identities reconcile. No producer/checker formulas reused.

The [result record](../../evidence/field-residual-results-v1.json) binds execution,
all grid rows, sources and qualification logs. Diagnosis is complete; a full
native regression, physical acceptance or Step 4 completion is not claimed.

## Scientific and release checks

- [Fixed field comparison](../optimization/FIXED_FIELD_PROBE_RESULTS.md): latest
  completed field study and its source-bound 5,654-test pre-execution regression.
  That regression does not cover all subsequent edits.
- [Public release verification](../validation/PUBLIC_RELEASE_RESULTS.md): dated
  portability/compatibility checks, known failures and unverified hosted coverage.
- [Residual analysis](../optimization/FIELD_RESIDUAL_RESULTS.md): eight comparisons
  complete at clean `7b4ec75`, with independent arithmetic and unchanged limits.

No new fields, full native regression, hosted CI, external peer review or
publication follows from this saved-data software check.
