# Portable public layer: verification and limits

For usage, see the [quickstart](PUBLIC_QUICKSTART.md); for latest maintenance
checks, see [current verification](../logbook/VALIDATION_LOG.md). This page records
versioned release evidence, not an assertion that every check was rerun at HEAD.
No new optimization or physical-design acceptance is established.

The simplicity cleanup retains the numerical contract and reduces public CI to
Python 3.11/3.14 across three systems. Current local checks are in the log above;
the source-bound records below describe their original revisions, now reachable
through the [reproduction guide](REPRODUCING_RESULTS.md).

## Supported interface and numerical contract

- Python 3.11+ standard library; six order-5 base Fourier curves, 24 physical
  symmetry copies, frozen signed currents and explicit metre-valued names.
- Filament Biot–Savart B and vector potential A, periodic 256/512-node quadrature,
  with the reference convention μ0/(4π) = 1e-7. The attributed packet contains
  64 deterministic samples each from the boundary, interior and flux loop.
  [Data, selection and provenance](../../examples/clear-coil-samples-v1/README.md).
- Analytic circular-coil, symmetry, translation/current-linearity, SI derivative
  and invalid-input controls. The unchanged seed's B/A comparisons against saved
  native values require maximum-component error normalized by the native maximum
  to be ≤5e-10 for each quantity/sample group. Refinement is reported separately.
- CLI reference/candidate comparisons both use **512 nodes**; an unchanged
  reference has zero displayed change. Saved native 256-node comparisons remain
  separate. Sampled normal RMS is 0.3042070281 and interior RMS is 0.3804347184.
- Reports bind candidate/profile/data/evaluator identities. `audit` recomputes
  with the same evaluator, not an independent implementation. No continuous
  geometry, full-surface normalization, QI, pressure or engineering acceptance;
  `physical_admission` remains false.

## Source-bound local verification

The latest multi-Python interface qualification is
[readme-review-v1](../../evidence/readme-review-v1.json), implementation `0d9abcf`:
**47 public tests and all eight real copied-tree checks pass on Python 3.11.4,
3.12.13 and 3.14.3 on macOS**. Each copy's 16 files match that commit. The checks
include discovery, real reference replay, a changed candidate, report replay,
forged admission rejection, optional contribution metadata and output preservation.
The unchanged reference displays zero change at matched resolution.

The same implementation's full research regression passes **2,182 tests**, with
334 warnings and zero failures/errors/skips (244.42 s). This is not the latest
research-suite size or a regression of subsequent edits. All 42 referenced
source/artifact hashes and sizes were verified in that qualification.

[public-review-v2](../../evidence/public-review-v2.json) additionally records a
fresh dev-only core checkout passing without SciPy, meshio or JAX, simulated
Windows cp1252 documentation reads, and the actual macOS Python 3.9 early version
error. That revision had 44 public tests and 2,072 native tests; these checks
must not be presented as newer-source or hosted-CI runs.

The [original software qualification](../../evidence/public-layer-v1-software.json)
and [portable reference qualification](../../evidence/public-layer-v1-portability.json)
bind the original arithmetic and data export. The isolated copy had no `.git`,
`.venv`, external checkout or research artifacts; Python used `-I -S` and rejected
socket audit events. This was an isolation check, not an OS security sandbox.
Largest relative native B/A difference was 9.5879976e-16, below 5e-10. The
one-micrometre smoke variation was an interface test, not a selected improvement.

## Failures and outstanding verification

Qualification records retain initial JSON-depth and frozen-CI failures, the later
two disk-reserve test failures, and a stronger nonprotocol cross-Python byte-equality
failure from last-bit metric rounding. The unchanged numerical replay tolerance
passed; no scientific limit or disk guard was relaxed. Final passing checks do not
erase those observations. Raw logs remain referenced by the evidence records.

Actual Windows/Linux or hosted matrix runs and independent-machine reproduction
are **not established** by the local checks. Git history and ignored artifacts
still require separate rights/privacy/security review and backup arrangements.
The starter's portable packet does not make the full native research graph portable.
The [launch checklist](REVIEW_POLICY.md#launch-checklist--requires-actual-hosting-work)
owns hosting, real clone URL, reviewer/protection settings and security prerequisites.
No hosting, external contact or automatic merging is enabled by these files.
