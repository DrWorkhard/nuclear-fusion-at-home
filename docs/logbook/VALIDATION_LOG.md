# Current verification

Updated 27 September 2026. Latest completed work, not an append-only history.
Git retains previous versions; canonical result pages retain scientific checks
and failed attempts.

## Coherent-shape comparison: failed startup retained

At clean `e8eeaf9`, both paired arms stop after ten startup bundles each.
All nine original coarse anchors replay exactly, but three of four directional
checks fail their unchanged tolerances. **No optimizer or fine screen runs.**
Worker/supervisor times are 7.080 / 7.660 s; 53 run files use 1,245,748 bytes.

Independent review verifies 39 source hashes, the execution/question identities,
all twenty startup rows and bit-exact repeats across arms and original trial52.
Saved scalar components localize the step-size dependence to the curvature
penalty; magnetic finite differences change only about 4–7e-12. Error reduction
of about four on halving h supports truncation error, not an automatic pass.
The [failed result and separate diagnostic](../optimization/COHERENT_COIL_EXPLORATION.md)
preserve the failure and specify thirty diagnostic bundles before any retry.

Implementation qualification remains scoped: **58 combined tests pass**
(14.23 s), including the existing native-circle cache regression; independent
review reruns thirty coherent/constrained synthetic tests (0.88 s). No full
native regression is claimed. The unused geometry runner's serializer check
passes; no geometry computation occurred for this attempt.

The separate derivative-scale diagnostic passes **44 combined synthetic tests**
(1.21 s). Independent preflight review added explicit nonfinite-comparison
rejection before any real diagnostic run; no acceptance tolerance changed.
This readiness check does not supply a new derivative or optimization result.

## Local-normalized currents: four-arm result complete

At clean `a3ce1ab`, four fixed-geometry searches complete **268 bundles and eight
fine screens**, in 6.746 s worker / 7.066 s supervised. Sources remain unchanged;
13,338,934 run bytes are retained. Equal-current starts give RMS gains of
12.91% / 6.93% for circle/shape; raw-fit starts reach worse solutions. All eight
flux/current checks pass and all eight normal-RMS/max gates fail. Boundary-field
strength is still much lower than the original controls. No physical acceptance.

Latest independent checks actually performed in the existing `.venv`:

- **42 combined local/raw-current synthetic tests pass** (0.39 s); the reviewer
  separately reruns 22 new tests (0.23 s). These include analytic derivatives,
  scale invariance, bounds/equality, selection, accounting and late rejection.
- Verified **31 sources and all 570 run files**, both saved response bases,
  four historical fine controls and eight new fine arrays.
- All **268 attempt/completion pairs**, forty startup calls, sixteen derivative
  checks, four exact repeats, 1,608 gradient components and 4,692 scalar metrics
  reproduce. The selected indices are the exact lowest feasible seed/search RMS;
  probes/repeats are excluded. Every recorded current vector satisfies the box
  and equality.
- Frozen six/24-current assignments and fine geometry/grids match their sources.
  Eight full loop-A integrals and **512 each of B, A and loop-B** comparisons
  pass. Maximum scalar/gradient discrepancies: 4.44e-16 / 1.044e-14.
- The reviewer did not rerun native fields or remeasure execution/resource
  history. No nonconvex global-optimality, interior or confinement proof follows.

The [current-study result](../optimization/INDEPENDENT_CURRENT_EXPLORATION.md) and
[evidence](../../evidence/local-currents-v1.json) retain all identities and
negative screens, including the earlier raw-objective result. Independent
saved-gradient inspection finds widespread old coefficient-box saturation;
the [next paired shape question](../optimization/COHERENT_COIL_EXPLORATION.md)
is specified before execution, not reported as a result.

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
**47 public tests pass**; scoped Ruff, documentation structure and
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
