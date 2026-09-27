# Step 1 result: a reliable foundation

**Complete, 13 September 2026**, in the registered local scope. English summary
of the German [detailed results at the freeze tag](../validation/REPRODUCING_RESULTS.md);
that report and the evidence files remain authoritative.
[All steps](README.md) · [Roadmap](../PROJECT_PLAN.md) · [Status](../STATUS.md)

## What the step had to show

That our local toolchain reproduces selected open references and correctly
accepts or rejects coil designs, before we rely on it for new designs. Steps 1
and 2 are capability milestones: they did not require a new feasible design, a
new method or a state-of-the-art result. The gates were fixed in the
registered protocol `docs/validation/FOUNDATION_ACCEPTANCE_PROTOCOL.md` at that tag
before the acceptance run.

**Scope:** the locked local Python/SIMSOPT/StellCoilBench toolchain on the
Landreman–Paul quasi-axisymmetric (LPQA) fixed plasma surface, with four Fourier
base coils of order 8 (16 physical copies, 207 named parameters) and fixed total
current. W7-X serves as a version-bound equilibrium regression; Goodman's open
QI data serves as a known-data regression of a frozen bounce-action diagnostic,
not as a global QI score.

**Gates**, grouped as in the protocol:

1. The full local test suite, Ruff and the documentation check pass with no skips
   or errors; separately, the six mandatory W7-X/Goodman data tests pass unskipped.
2. The preserved native build (21 phases) and archived binaries, inputs and
   outputs are hash-bound; the W7-X physics check passes and the extended file
   comparison stays at its known 60/63.
3. The field and derivative qualifications are bound, and the start Jacobian and
   native Gram-matrix checks are repeated with the unchanged tolerances (1e-12/1e-10).
4. All four independent candidate checks run for both new candidates: field and
   geometry, continuous curvature, coil spacing and additional native conditions,
   at every resolution. Correctly rejecting a candidate is not a tool failure.
5. Negative controls reject missing sources, wrong hashes or parameter mapping,
   incomplete phases, swapped numerical approvals and claims of excluded capabilities.

## Result

The fresh complete run `foundation-acceptance-v2` (commit `1aa28b6`) passes the
separate final audit, which confirms all eight Step 1 gate checks.

| Check | Observed result |
| --- | --- |
| Full regression | 720 tests pass in 53.33 s; no skips or errors; 144 known fixture warnings |
| Mandatory scientific data tests | Exactly the six W7-X/Goodman tests pass, none skipped |
| Code and documentation checks | Ruff and documentation structure pass |
| Preserved native reference | 21 build phases, 11 archived files and the protected W7-X physics confirmed; extended comparison unchanged at 60/63 |
| Start and derivative checks | 16 fixed start bundles per arm, full Jacobian and a separately computed native Gram matrix pass the unchanged limits |
| Environment | Same visible netCDF4 warning results and binary source as before; the strict import still fails, so there is no ABI claim |
| Preservation | 1,266 historical tracked files checked against `5971fee`; only permitted overview and journal edits |

## What it does not show

No new design success, global QI qualification, finite particle orbits, complete
engineering models, independent hardware, hosted CI, ABI certification,
state-of-the-art performance or SQuID-C reproduction. The W7-X file comparison
still differs in three quantities (`pres`, `presf`, `chipf`).

## Failures kept on record

The first acceptance run `foundation-acceptance-v1` (commit `028c4cc`) failed its
final audit because of a bookkeeping bug in the new audit code: one file reference
included its size, the other only path and hash, although both pointed to the same
content. That run stays rejected. The fix was committed and the whole acceptance
was repeated from scratch with unchanged budgets and limits (v2 above).

Research from before these sharpened milestones is preserved unchanged at `5971fee`
(tag `foundation-pre-scope-2026-09-13`).

## Evidence

- [Sequential run record](../../evidence/foundation-acceptance-v2/run.json) and
  [final audit](../../evidence/foundation-acceptance-v2/summary.json)
- [Candidate checks](../../evidence/foundation-acceptance-v2/holdouts/summary.json)
- [Re-confirmation with absolute run path](../../evidence/foundation-acceptance-v2-confirmation-absolute.json)
- Commands and operating limits: [detailed results at the freeze tag](../validation/REPRODUCING_RESULTS.md).
  Re-running requires the native research environment, not the public starter.
