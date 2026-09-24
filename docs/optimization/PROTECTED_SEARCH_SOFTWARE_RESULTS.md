# Protected-search controller qualification

Updated 24 September 2026. [Registered scope](PROTECTED_SEARCH_SOFTWARE_PROTOCOL.md) ·
[Optimization index](README.md) · [Paused native pilot](PROTECTED_COIL_FIT_PROTOCOL.md)

## Assessment

The pure controller and separate trajectory auditor pass **108 synthetic tests**.
Full research regression: **2,180 passed, 334 existing warnings**, no failures,
errors or skips, in 222.05 s. **This bounded software gate is complete.**
No new native field fit or equilibrium optimization was run.
The search policy, physical limits and earlier scientific evidence are unchanged.

This work makes the next geometry-protected coil search more auditable. It does
not demonstrate a field improvement, physical admission or completion of Step 4.

## Implementation and scope

- `protected_coil_search.py`: the fixed-policy controller delegates geometry and
  field calculations to callbacks. Reservations precede work; an exception stops
  further work and attempts a diagnostic record without replacing the original error.
- `protected_coil_search_audit.py`: a separate scalar/standard-library implementation
  reconstructs completed trajectories without importing the producer or NumPy.
  It checks normalization, backtracking, proposal coordinates, exact current and
  recorded Armijo decisions, selection, budgets and event order.
- These are separately implemented numerical/control-flow checks by the same
  maintainer, **not independently authored review or external peer review**.
  Stored field values, gradients, geometry assertions and source identity are not
  independently verified; the verdict explicitly marks each as unverified and
  always leaves `physical_admission` and `step4_pass` false.

The auditor accepts JSON-compatible `seed`, `initial`, `report` and `events` via
`fusion_baselines.protected_coil_search_audit.audit(...)`. It returns a verdict;
malformed or incomplete traces fail closed. This internal research interface is
separate from the portable public candidate `evaluate`/`audit` commands. Aborted
traces are not completed trajectories; failure-prefix behavior is tested in the
controller suite instead.

## What the tests establish

Both registered coil classes are covered: n6/M5 and n8/M7, with only modes 0–2
active. Scalar formulas check P (not P squared), full-index FD directions and
maximum per-coil D0 normalization. General signed gradients, exact repeats,
immutable original-seed callback arguments and high-mode signed-zero bits are
checked. Synthetic objectives and geometry decisions are not real coil data.

All five stop reasons are tested. A final rejected backtrack takes precedence
over a simultaneously exhausted budget; otherwise geometry budget precedes field
budget. These stops are not convergence claims. Twenty accepted toy steps and
116-proposal geometry-limited paths check separate counters. Tied objectives
retain the first minimum; rounding can permit a recorded Armijo equality.

Tests cover malformed returns, callback/recording failures, private copies,
missing/reordered events and coherent corruption of redundant trace copies.
One representable float above 500 kA is rejected: audit reconstruction tolerance
does not enlarge the physical current limit. A hand-built one-step trace passes
with the producer disabled and in an isolated Python process without site packages.
An explicitly fabricated but internally consistent geometry assertion still passes
control-flow audit; the test verifies that this never becomes physical verification.

## Retained failures and corrections

1. Initial controller tests: **29 passed, four failed**. Malformed geometry/field
   returns were marked completed before validation; certificate and completion
   publication failures inherited incorrect calculation-stage labels. Move completion
   counts after validation and label those two publication stages explicitly.
   The original descent policy, thresholds, budgets and callback outputs are unchanged.
2. Expanded auditor tests: **104 passed, three failed**. The hand-written fixture
   used decimal `-1e-7` instead of the exact machine result of
   `0.0 + 1e-4 * 0.001 * -1.0`. The auditor correctly rejected that one-bit
   discrepancy. Correct the fixture, retain the failure and add a specific negative
   control; do not relax the exact recorded Armijo check.
3. Ruff caught a missing strict zip, a lambda assignment and an overlong line;
   all are corrected. Final targeted checks: **108 passed in 4.61 s**, Ruff passes.
   Public tests: **44 passed in 0.537 s**; documentation and whitespace checks pass.

JUnit files are retained in `artifacts/protected-search-software-v1/`:
`initial-tests.xml`, `auditor-first-tests.xml`, `corrected-tests.xml` and
`full-regression.xml`. The [machine-readable record](../../evidence/protected-search-software-v1.json)
binds all four artifacts and five protocol/source/test files by hash and size.
They remain local ignored artifacts, not a bundled portable physical evidence packet.

Registration: `252f6f0`; implementation and full regression: `32dc632`.
The initial failing producer remains retrievable at the registration commit; the
initial test file was uncommitted, and its exact original bytes were not separately
archived. The failed JUnit retains the failing assertions. Do not imply a stronger
source binding for that first run than was actually recorded.

Regression used Python 3.12.13 and the existing native environment, with OMP,
OpenBLAS and MKL each limited to one thread. No packages were installed or synced;
process inspection found only editor services before the run. Full regression
includes the prior 2,072 tests and the 108 new tests. Existing HiGHS-option and
NumPy/netCDF deprecation warnings persist; this is not an ABI-cleanliness claim.
The worktree was not globally clean: the user's unrelated README edits were
preserved. All five bound source files match `32dc632`; no scientific source
changed during regression. No hosted or independent-machine run is claimed.
Final evidence verification matches all nine hashes/sizes, the five committed
sources and all four JUnit summaries. After summary updates, 34 documentation,
release-maintenance and foundation tests pass in 5.50 s; docs, Ruff and whitespace
checks also pass. No scientific code changed after the full regression.

## Remaining work

Before the native pilot, second internal method review, a source-bound durable
runner, independent physical recomputation and finer-grid acceptance still need
qualification. Preserve the original draft and its unqualified status until these
prerequisites are met. The next implementation work is the runner's persistence,
budget and source-binding layer, first with synthetic fault-injection tests.

Existing startup code is a reference, not a drop-in runner: its operation ledger
assumes a fixed startup matrix. The protected pilot instead needs 10 startup
bundles + one search seed + at most 20 field trials + one fresh-model replay,
with independent geometry accounting (at most 128 certificates). Two model
initializations and 32 nine-request bundles give the draft's 290 native-request
cap per cell. These are still planned limits, not work already executed. Adapt
the ledger explicitly; do not reuse or silently expand startup budgets.
