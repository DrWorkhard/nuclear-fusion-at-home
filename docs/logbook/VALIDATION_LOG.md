# Current verification

Updated 27 September 2026. Latest completed work, not an append-only history.
Git retains previous versions; canonical result pages retain scientific checks
and failed attempts.

## Derivative-scale diagnostic complete and independently checked

At clean `cd376b5`, thirty diagnostic bundles complete in 9.151 s worker /
9.510 s supervised, with 64 run files / 1,213,143 bytes. All nine original coarse
anchors and exact full-component seed repetition pass; all sources remain
unchanged. This is a fixed-seed numerical diagnostic, not optimization or a new
design.

All three components pass unchanged tolerances at the four tested steps
h≤2.5e-6. Maximum total discrepancy at the proposed retry steps 1.25e-6 / 6.25e-7
is 8.04e-11. Separate explicit Fourier reconstruction of all thirty saved coil
sets reproduces 180 sampled curvature maxima to 2.31e-14. Larger positive probes
cross one/two κ=10 penalty branches; chosen smaller probes preserve the sampled
active set. The physical curvature limit stays 12/m.

Checks actually performed in the existing `.venv`:

- **44 combined diagnostic/coherent/constrained synthetic tests pass** (1.21 s).
  Independent preflight review reruns fourteen new tests (0.33 s); its overflow
  counterexample was fixed before the real run, without changing tolerances.
- Component identities, exact thirty-bundle accounting and repeat are recorded;
  120 B / thirty A / thirty B-vjp requests plus thirty extra geometry-gradient
  extractions completed. No independent native field kernel was rerun.
- Independent saved-data review verifies 42 source hashes, all 42 component
  finite-difference/error/tolerance classifications and exact seed repetition.
  Separate reconstruction of all thirty coil sets reproduces 180 curvature
  maxima within 9.24e-14 and confirms the penalty-branch crossings.
- **47 public tests pass**; scoped Ruff, documentation structure and whitespace
  checks pass. No full native regression or separate-machine replay is claimed.

The [canonical result](../optimization/COHERENT_COIL_EXPLORATION.md) and
[evidence](../../evidence/coherent-derivative-scale-v1.json) preserve the initial
failed attempt unchanged. That clean `e8eeaf9` attempt stopped after twenty
startup bundles, before optimizer/fine work; its independent audit checked
39 sources and exact saved startup values. A separately identified retry changes
only the two startup step sizes, not budgets, selection, objective or gates.
No retry result is claimed here.

The fresh retry implementation passes **46 combined synthetic tests** (1.71 s),
including an exact syntax-tree comparison isolating the documented probe change,
source rejection, selection, 10/600 accounting and override restoration. The
nineteen fixed-input hashes and actual saved-diagnostic preflight also pass;
no native search was run for those checks.

## Supporting results retained at their point of use

- [Independent-current study](../optimization/INDEPENDENT_CURRENT_EXPLORATION.md):
  four normalized-current arms / 268 bundles improve original circle/shape RMS
  12.91%/6.93% at best, but weaken boundary fields and fail all field gates.
  Independent checks cover 31 sources, 570 files, 4,692 scalar metrics and
  512 each of B/A/loop-B samples. The earlier raw-objective negative result remains.
- [Public shape-52 example](../../submissions/constraint-aware-shape52/README.md):
  normal/interior sampled scores improve 43.80%/23.20%; evaluation and same-code
  audit pass. Geometry matches the native export, but the public current differs;
  no native interior or physical acceptance is inherited.
- [Constraint-aware fitting](../optimization/CONSTRAINED_COIL_EXPLORATION.md):
  shape52 remains the best scoped continuous-geometry pass at RMS 0.151679;
  lower sampled scores have unresolved clearance. All boundary limits fail.
- [Matched calibration](../optimization/REFERENCE_CALIBRATION.md): thirteen rows,
  156 independently reproduced metrics and 832 field comparisons; no complete
  Goodman positive control.
- [Public release results](../validation/PUBLIC_RELEASE_RESULTS.md) retain exact
  dated portability checks and unverified hosted coverage.

No hosted CI, external peer review, release, pressure/engineering validation or
Step 4 completion is claimed by this maintenance record.
