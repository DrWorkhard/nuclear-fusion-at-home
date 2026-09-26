# Protected candidates: fine-phase integration notes

26 September 2026. Read-only mapping by independent internal agent
`protected_budget_impl`; **not an implementation, qualification or execution
registration**. [Original requirements](PROTECTED_COIL_FIT_PROTOCOL.md) ·
[Method limits](PROTECTED_METHOD_REVIEW.md) · [Index](README.md)

## What must follow the coarse pilot

Validate all eight selected candidates, including fallback seeds, without feeding
fine results back into selection. Bind acknowledged coarse execution, successful
saved-physics reconstruction, selected coordinates/certificate and the original
geometry seed/report. Freeze the selected **coarse current** on every fine grid.

| Operation | Fresh original-seed models | Native requests per model | Total |
| --- | ---: | ---: | ---: |
| Six field/interior diagnostic grids | 6 | 1 initialization A + 6 values | 42 |
| Flux blocks at 256/512 coil nodes | 2 | 1 initialization A + 18 values | 38 |
| Per selected case | 8 | No VJPs or hidden warm-ups | 80 |

Eight cases add at most 640 requests; combined original construction/fine maximum
remains 2,960. Diagnostic grid order `(nphi, ntheta, ncoil, ninner, offset)`:
`(64,64,256,32,0)`, `(128,128,256,32,0)`, `(128,128,512,32,0)`,
`(128,128,512,32,0.5)`, `(64,64,256,64,0)`, `(64,64,512,64,0)`.
Each has boundary B, interior B, loop A, boundary A, interior A, loop B.
Each flux block has three line grids (256/512/1024) and six fan grids
(16/32 radial points × 256/512/1024 angular points), two value calls per grid.

## Reuse and changed-candidate traps

Reuse the frozen native `make_model`/`execute`, archived targets and independent
`target`, `field_row(diagnostic=True)`, refinement/flux checks and absolute physical
gates. Preserve each case's N/V method explicitly; the old fine model plan uses N.

- Every model starts at the original seed. Then assign selected coordinates and
  verify exact bits. **The old flux `execute` does not assign candidate coordinates**;
  blindly reusing it after model creation would evaluate the original seed.
- Keep the selected coarse snapshot/current as the frozen diagnostic input.
  `ClearCoilField.snapshot(scale=...)` rejects frozen-current snapshots. Do not
  recalibrate fine current or pretend a changed candidate is an original seed.
- Fine initialization flux belongs to the original seed at that coil resolution,
  not to the candidate. Independently bind/check it. Fine measured flux/unit-flux
  may differ numerically from the retained coarse snapshot and must be evaluated
  against the original refinement/flux gates, not forcibly equated.
- Old whole-cell auditors assume ten models, 262 requests and original seed-only
  identities. Construction contracts/ledger require two models, coarse shapes and
  unfrozen metrics. Neither is a fine validator; add a separate tested boundary.
- The current supervisor requires real search-phase events. A no-search fine
  worker needs separately qualified timing/acknowledgement; never fake a search
  phase to pass its protocol.

## Direct geometry and storage

Reuse `Sampler(original_seed, both_target_surfaces)` and the independent sample
auditor with selected coefficients and the original-seed cumulative certificate.
Four grids: `(256,0)`, `(512,0)`, `(1024,0)`, `(1024,0.5)`. Check both immutable
256² full-torus target surfaces and every physical pair: 24 coils / 276 pairs per
grid for six base coils; 32 coils / 496 pairs for eight base coils.

The sampled `curvature_available` array is boolean, while qualified immutable
numeric storage rejects booleans. Register and test a lossless explicit uint8-mask
encoding with exact boolean restoration before the unchanged sample auditor.
Do not silently broaden the frozen storage schema.

## Before implementation or interpretation

Preregister the fine-specific contracts, 80-call accounting, resource/return
protocol and changed-candidate tests. Preserve all five refinement comparisons,
both flux blocks and cross-resolution checks, direct B/A checks, continuous
certificate and four direct geometry grids with unchanged thresholds.

A faithfully computed physical rejection is a complete negative result; malformed
evidence, numerical disagreement or resource/publication failure is not acceptance.
Successful fine numerics alone still do not establish a resolved field improvement
or Pareto dominance without the method review's separately registered resolution
margin. Realized-field transfer and Step 4B–4D remain later scientific work.
