# Interior-field screen of exploratory coil fits

27 September 2026. **Prepared, not executed; paused for repository simplification.**
The implementation passes 49 synthetic tests (0.58 s main); no actual intake,
native field, optimization or VMEC run is claimed. This diagnostic accompanies
the [coherent-shape experiments](COHERENT_COIL_EXPLORATION.md); it does not add an
optimization session or change their selection rules.

## Question and fixed comparison

Does the improving boundary fit also improve the vector field inside the target?
Boundary error alone can hide amplitude or tangential mismatch. Inspect the
following five fixed geometries, without optimizing or selecting on interior error:

1. Original six-coil shaped initialization at 100 mm offset.
2. Geometry-checked shape/full trial 52.
3. Geometry-checked coherent-wide trial 598.
4. Session 7's frozen original-absolute-box endpoint.
5. Session 7's frozen expanded-low-mode endpoint.

Both session-7 endpoints must come from the successfully completed paired run;
bind its actual result hash before execution and verify snapshots against the
saved selections. Report their separate geometry verdicts, including unresolved
ones, alongside the screen: the combined evidence must bind the geometry report
and its exact snapshots. The field-only adapter marks geometry as not assessed
there and does not filter candidates on geometry or the new interior score.
Failed searches remain
failures, not silently omitted cases. Earlier source graphs remain unchanged.

All five address the **original reference**, input
`evidence/plasma-design-v2/reference-input-401.json` (SHA-256
`57394ef682f3c6399faa03012abc02da2eb1ce40703a4f99640ece3d07e5691f`).
This is not the accepted Step 3 target. The reference is symmetric nfp2, zero
pressure/current, with positive equilibrium edge flux π/100 Wb and oriented
coil-loop target **−π/100 Wb**.

## Fixed method and limits

Reconstruct target Cartesian fields on s=0.25, 0.5 and 0.75 from the qualified
64² archives indexed by `evidence/plasma-balanced-v1/validation.json` (SHA-256
`84eff962b74ca5124147e12b4e30927a29b44f31c849333b0ae17c79a382d50c`).
Bind those arrays and the reference Wout/input. Use the nested 32² and full 64²
grids, with the same fixed **B² scale 1.6293829620247962 T²** throughout.

For every snapshot evaluate these three levels:

| Interior points per surface | Nodes per physical coil | Purpose |
| --- | --- | --- |
| 32² | 256 | Coarser interior screen |
| 64² | 256 | Isolate interior-grid refinement |
| 64² | 512 | Isolate coil-quadrature refinement |

Freeze each snapshot's actual physical currents, not the sparse public starter's
current. Verify all six named Fourier curves, 24 physical copies and signed
currents independently. Do not renormalize on a finer grid. Report
`sqrt(mean(|Bcoil − Btarget|²) / B²_scale)`, per-surface errors, field amplitudes,
minimum field, current and measured frozen-current loop flux. The interior pilot
limit remains **0.01**; resolution differences are reported, not rounded away.

Retain full B, target coordinates/fields, loop A/tangents and coil geometry,
plus 64 independently recomputed B and A points per row. Reuse the existing
independent Fourier/filament primitives; matching native fields is a numerical
check, not external validation. No optimizer, equilibrium solve or new target.

Bounded fresh family `artifacts/coherent-interior-v1/`: fifteen rows, 180 s worker /
185 s external, 128 MiB aggregate, one thread and 3/2 GiB initial/live disk
reserves. Source identities and final publication must remain valid; retain
failed prefixes. Run after the paired optimization, not concurrently with it.

## Interpretation and next physical checks

A lower interior score is useful evidence about vacuum field fidelity; it does
not prove nested surfaces, confinement or preservation of the Step 3 benefit.
The realized field still needs actual field-line tracing and refined topology
checks. Calling the ideal VMEC geometry a realized surface, or evaluating coil
|B| along ideal field lines, would not establish that result.

The local tracing driver expects different input formats and needs a small
snapshot adapter with raw trajectories, refinement and domain-departure checks.
Existing action routines require physical arc length, unchanged absolute bounce
levels and complete well coverage on **realized-field** traces. Benefit transfer
also needs a matched coil realization of the selected Step 3 target. The old
free-boundary driver truncates the target and coil family; it cannot be reused
unchanged. These are remaining Step 4A tasks, not results of this screen.
