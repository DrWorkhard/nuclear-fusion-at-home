# Current verification

Updated 27 September 2026. Latest completed maintenance; Git retains older records.

## Simplicity cleanup

Annotated tag `research-freeze-2026-09-27` points to
`56181dc4250cb24ce3d2bedf5cec3d894d1ac250`, before removals.
**691 tracked files removed:** 195 scripts, 127 library files, 191 tests and
178 detail documents. Every removed path exists at the tag; representative
foundation code/results and plasma results were read back successfully.
Docs shrink from 211 to 34 Markdown files, including the new
[reproduction guide](../validation/REPRODUCING_RESULTS.md). No raw artifact,
external checkout, environment or tracked scientific evidence was deleted.

The public evaluator and retained numerical code are unchanged: 36 retained
source files match the tag byte-for-byte. Only the CLI dispatchers and docs
checker changed among retained Python implementation files. All **51 combined
source references** in the latest coherent/restart results pass their original
hash checks. Both committed result manifests retain their recorded hashes.
Dependency metadata remains lock-compatible; `uv.lock` is unchanged.

## Checks actually run

- Reduced native suite: **404 passed**, 13 known HiGHS option warnings, 21.94 s.
- Public tests, Python 3.12 in isolated standard-library mode: **48 passed**,
  3.519 s.
- Isolated copied-tree release: **8/8 checks**, including 48 public tests, on
  both local Python 3.11 and 3.12. Reference B/A errors remain at most
  9.588e-16, below 5e-10. These are same-machine checks, not hosted CI.
  Local receipts: `results/simplicity-cleanup-check/qualification.json` and
  `results/simplicity-cleanup-python311/qualification.json`.
- Dev-only-selected documentation/maintenance tests: **31 passed**, 0.57 s,
  in the existing environment; no fresh dependency sync was performed.
- Ruff, documentation structure/links/budgets (also on Python 3.11), and
  `git diff --check` pass. Link checks now include contributor, example,
  submission and GitHub Markdown. Module CLI help/discovery work; retired
  root commands return a helpful tag notice with exit 2.
- Intermediate failures retained here: first reduced run had 399 passes and
  64 stale-link errors in its one failing documentation test. A misplaced
  test-function boundary then caused four new link-test failures; corrected
  before the final 404-pass run.

## Limits and next repair

Real-data intake of the prepared interior screen **fails before field work**:
saved target flux `-0.03141592653589793` differs from its `-np.pi/100` constant
by one ULP (6.939e-18 Wb). The adapter predates cleanup and is unchanged.
The 49 synthetic screen tests did not expose this. Fix against the exact
source-bound input, add a real-data regression and rerun intake before native
evaluation. See the [screen record](../optimization/INTERIOR_FIELD_EXPLORATION.md).
No new optimizer, native field or VMEC run occurred during cleanup.

Offline lock regeneration was blocked by the approval service's usage limit.
The old optional engineering extra remains declared and locked; no installation
or environment modification occurred. Hosted matrix execution, independent
reproduction and backup/restore remain unverified. The latest coil result still
fails physical field limits; Step 4 and MS1 are not complete.
