# Current verification

Updated 27 September 2026. Latest completed work, not an append-only history.
Git retains previous versions; canonical result pages retain scientific checks
and failed attempts.

## Independent currents: raw-objective result complete

Two fixed-geometry current fits complete fourteen replay/fine rows in 4.794 s
worker / 7.151 s supervised. Execution is dirty but source-bound at `39a1e13`;
sources remain unchanged. Both raw-objective numerical optimality checks pass,
without polishing, while normalized RMS worsens by 59.68% / 83.25%. Flux/current
checks pass, but the boundary field becomes much weaker. This is a negative
design result, not a failure of the numerical solver or a Step 4 completion.

Latest independent checks actually performed in the existing `.venv`:

- **Twenty synthetic implementation tests pass** (0.44 s main / 0.43 s reviewer),
  including derivatives, constrained optimality, mappings, partial/slow writes
  and rejection of late final publication. No real study runs in these tests.
- Verified 27 sources, all 54 run files / sixteen NPZs, 238 scalars, both saved
  response matrices, flux vectors, numerical optimality checks and nullspace
  spectra. Both starts retain their exact original geometry.
- Fourteen complete saved-loop-A integrals, six coarse linearity pairs and all
  **896 B / 896 A** comparisons pass. Maximum errors are 6.14e-16 / 1.13e-16.
- Independent Fourier reconstruction verifies all three grids and loops to
  1.95e-14. Explicit six/24-current mappings and frozen fine currents match.
- The reviewer did not rerun native fields, the full ancestral reference graph,
  physical diagnostics or resource-history measurements.

The [result record](../optimization/INDEPENDENT_CURRENT_EXPLORATION.md) and
[evidence](../../evidence/independent-currents-v1.json) retain exact identities,
failed-screen outcomes and scope. The next local-normalized-current experiment
is specified there; its results are not yet claimed.

## Public export of the improved shape

The [shape-52 candidate](../../submissions/constraint-aware-shape52/README.md)
reproduces all 198 native coefficients/names and physical-copy mappings.
Public evaluation and same-code audit both exit zero: normal RMS 0.170953
(−43.80% from the starter), interior-vector RMS 0.292176 (−23.20%).
Replay passes; independent implementation, physical admission and Step 4
completion remain false. The public fixed current differs from the native fit;
only geometry is exported, not its magnetic state or native interior acceptance.

Independent review checks both saved resolution levels, coefficient/current
identities, all source hashes and unchanged evaluator/reference bytes against
`39a1e13`. See the [portable evidence](../../evidence/public-shape52-v1.json).
**47 public tests pass** (3.360 s); scoped Ruff, documentation structure and
whitespace checks pass. No full native regression, independent public field
rerun or separate-machine replay is claimed.

## Supporting checks retained in their result pages

- [Constraint-aware fitting](../optimization/CONSTRAINED_COIL_EXPLORATION.md):
  744 search bundles, original four-arm selections and adaptive saved-point
  checks. Shape trial 52 passes scoped continuous geometry at RMS 0.151679;
  circle trial 126 has unresolved clearance. All boundary-error limits fail.
- [Matched calibration](../optimization/REFERENCE_CALIBRATION.md): thirteen rows,
  156 independently reproduced metrics, 832 field comparisons and QUASR surface
  reconstruction. No complete Goodman positive control is established.
- [Static starts](../optimization/COIL_START_SCREEN.md),
  [objective comparison](../optimization/NORMALIZED_OBJECTIVE_EXPLORATION.md) and
  [saved residual diagnosis](../optimization/FIELD_RESIDUAL_RESULTS.md) retain
  source-bound implementation checks, actual results and failed attempts.
- [Public release results](../validation/PUBLIC_RELEASE_RESULTS.md) retain exact
  dated portability checks and unverified hosted coverage.

No hosted CI, external peer review, release or pressure/engineering validation
is claimed by this maintenance record.
