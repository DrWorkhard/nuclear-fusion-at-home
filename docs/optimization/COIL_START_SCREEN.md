# Field screen of alternative geometry-valid starts

27 September 2026. **Exploration; static fields, no optimization.**
[Programme](STEP4_RESEARCH_PROGRAMME.md) · [Objective comparison](NORMALIZED_OBJECTIVE_EXPLORATION.md)

## Question and fixed inputs

Do the existing circular or farther-out shaped starts offer a useful field/
curvature trade-off for the next search? The first matched objective experiment
reduces field error only with geometric violations. Screen already audited
alternatives before extending that search. This is exploration session 2 of the
programme's ten-session cap; it does not change acceptance gates.

Use four currentless snapshots under
`artifacts/clear-coil-initialization-v1/sets/CASE/snapshot.json`:

| Case | SHA-256 | Existing curvature upper bound, 1/m |
| --- | --- | ---: |
| n6-circle-d100mm | `829ea3573b6e46771d771810420c0e378a07f4bb16363305376f4b6d39856de6` | 3.063018 |
| n6-shape-d100mm | `90fe6f84395d319d45ac39fab832a2b3908f0d16d7638e971e2a4602a3ef65d1` | 10.000000 |
| n6-shape-d140mm | `53784adda5dd4d0d4d5fba3b1ba31e08707d55624ed7d9b633999298b54580df` | 10.000000 |
| n6-shape-d180mm | `40e075d4fc856c0149523a5c6be8139dd65f4499ac602fbbd9c09c5a3cf100e1` | 7.083006 |

All have six order-5 bases, 24 physical coils, two field periods, stellarator
symmetry and the same 198 named coefficient layout. The
[existing geometry study](../geometry/CLEAR_COIL_INITIALIZATION_RESULTS.md)
certifies their scoped geometric bounds; no geometry is optimized here.
Its audit SHA is `b068fd6a6c76e8b4aaf57341e5a2ae139be196f35defacc644f1d5c890c0ea49`.
The circle offers much more curvature room, not a known better field.

Use the unchanged reference input `evidence/plasma-design-v2/reference-input-401.json`
(`57394ef682f3c6399faa03012abc02da2eb1ce40703a4f99640ece3d07e5691f`).
The old magnetic seed supplies only the target flux −0.03141592653589793 Wb and
target B² normalization, not another geometry's current scale. Derive a fresh
scale for each geometry from its actual vector potential and the fixed target
loop, starting with equal 100 kA reference currents. Save the signed physical
currents explicitly. No inherited magnetic seed or transferred certificate
for modified coils is claimed.

## Prospective matrix and bounds

Each case receives three rows, twelve total:

1. 64 × 64 full-field-period boundary, 256 coil/loop nodes, no grid shift.
2. 128 × 128 boundary, 512 coil/loop nodes, no shift.
3. 128 × 128 boundary, 512 coil/loop nodes, half-cell shift in both angles.

Freeze each case's coarse current at the fine grids and report flux refinement.
Store full fields/normals, the loop-A arrays and independent comparison samples.
Compare mean, RMS, maximum, raw/local flux and field strength distinctly.

Use existing Fourier surface/coil reconstruction and plain native BiotSavart;
no instrumentation subclass or optimizer. Check named physical coefficients and
native positions/tangents against the independent reconstruction. Check B at 64
fixed distributed boundary points and A at 64 loop points independently, normalized
discrepancy ≤1e-12. The loop samples supplement, not replace, a full independent
Stokes integration. The old shaped100 score provides a known reference replay.

Local ceiling: **180 s worker / 185 s external process-group timeout**, one
thread, 128-point field blocks, 64 MiB outputs, 3 GiB starting / 2 GiB live disk
reserve. Fresh outputs under `artifacts/coil-start-screen-v1/`; retain failures.
Inputs, actual evaluator/binary identities and all rows must be hash-bound.
No equilibrium, interior-vector, topology, pressure or load calculation.

## Decision rule

Inspect all four cases; do not select merely the smallest coarse score. Keep the
unchanged 1e-4 RMS, 1e-3 maximum, 500 kA current and 1e-6 relative-flux screens
distinct from existing geometry certificates. These component screens do not
replace the full Stokes and physical-admission checks. Favor a follow-up start
only by its measured field/current/geometry
trade-off. None inherits the Step 3 plasma benefit from a boundary fit alone.
If all fields remain poor, document that result and change constraint handling
or the explored family rather than calling extra curvature room a solution.

## Results and next decision

All twelve rows complete in 6.362 s (6.734 s externally supervised), retaining
15,219,993 bytes. This exploratory run used a **dirty, hash-bound tree at
`566a6ab`**, not a clean-commit qualification. Loaded sources are unchanged.
The [evidence manifest](../../evidence/coil-start-screen-v1.json) binds every
output and preserves the exact pre-run question. Result JSON SHA-256:
`6ef5c6c9824847e2eba6fbacc96c5abca3268032ff7760451f5b4d732132a89d`.

| Start | Fine normal RMS | Worst of two fine sampled maxima | Current, kA | Existing curvature bound, 1/m |
| --- | ---: | ---: | ---: | ---: |
| Circle100 | 0.3086613120 | 0.6286876172 | 287.919603 | 3.063018 |
| Shape100 | 0.2760512695 | 0.5980210929 | 294.966466 | 10.000000 |
| Shape140 | 0.2899547418 | 0.6308623426 | 287.169836 | 10.000000 |
| Shape180 | 0.3041000176 | 0.6367180345 | 283.306254 | 7.083006 |

Shape100 retains the lowest initial error. Circle100 offers curvature freedom,
not a better initial field. All four pass current/flux component screens and
retain their unchanged geometry; all fail boundary-error screens. The largest
relative coarse/fine RMS change is 3.50e-8, and fine/shift change 4.80e-12.
The maximum is still sampled, not a continuous bound.

An independent read-only audit rehashes 22 sources and all twelve arrays,
reconstructs physical curves from named coefficients, and checks snapshot →
construction → geometry-audit links. Separate arithmetic reproduces all **144
boundary metrics**, twelve normalized-raw values and twelve full saved-loop-A
integrals. All **768 B and 768 A** independent sample comparisons pass; maximum
discrepancies are 1.009e-15 and 1.390e-16. Relative flux error is at most 8.882e-16.
Per-case normalization and exactly frozen fine currents are verified; native
request counts are B=1152, A=40, independent=24. Shape100's reference replay passes.

All **11 focused implementation tests** pass (0.33 s); the independent reviewer
also reran them. The loop-A replay is not a full independent Stokes test, and
no new geometry certificate, interior-field check or physical admission follows.

Next, [constraint-aware fitting](CONSTRAINED_COIL_EXPLORATION.md) compares circle
and shaped starts, strong penalties and low-order freedom. The farther-out shapes
do not justify selection on field quality alone. This is a measured allocation
decision, not evidence that those shapes or the broader family cannot improve.
