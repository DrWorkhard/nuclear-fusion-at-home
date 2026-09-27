# Matched boundary-reference calibration

27 September 2026. **Exploration, not acceptance.**
[Programme](STEP4_RESEARCH_PROGRAMME.md) · [Frozen metric diagnosis](../validation/REPRODUCING_RESULTS.md)

## Question and selection before field evaluation

Can attributed, matched coil/surface pairs anchor the interpretation of our
normal-field metrics? Select two local references for provenance and size, not
because a trial score passes. Neither is a matched Goodman/QI interior-field
control, so this study cannot calibrate the complete Step 4 profile.

- **QUASR 952:** SIMSOPT fixture `tests/test_files/serial0000952.json` at
  `a79006b0bc1e6df8ab48de284e3457d39a49b995`. One order-16 base coil, four physical
  coils, two field periods and stellarator symmetry. Preserve its complete
  tensor-Fourier surface (mpol=ntor=10), currents and original physical scale.
  No author score for this particular fixture is available locally.
- **LPQA 92598:** StellCoilBench submission `2026-02-17_083339_92598` at
  `c7949edc4ea6378fc3be633304c69c288c3b79b5`, with its exact
  `input.LandremanPaul2021_QA` target. Four order-8 base coils / sixteen physical
  coils, two periods and symmetry. Preserve original currents and scale rather
  than the earlier reactor-normalized comparison. The archived report gives
  mean-normal statistic 0.0004242713230861179, maximum 0.0019281263427522058 and
  thresholded flux zero (its threshold is 1e-6, not a physical zero).

The [QUASR dataset](https://zenodo.org/records/10944430) and
[method paper](https://arxiv.org/html/2310.19097v2) concern optimized vacuum
stellarators, not a claim of QI reactor qualification for this fixture. Dataset
redistribution rights remain to be verified; no archive is downloaded or
redistributed. LPQA's original producer revisions are recorded in its report;
we have not reproduced that old environment or established its exact grid.

## Fixed small experiment

Use [the existing native environment](../validation/ENVIRONMENT.md) and
`scripts/explore_boundary_controls.py`. Both cases receive this matrix:

| Surface grid | Coil nodes | Shift in grid cells |
| --- | --- | --- |
| 21 × 21 | 160 | 0 |
| 42 × 42 | 160 | 0 |
| 42 × 42 | 320 | 0 |
| 84 × 84 | 320 | 0 |
| 84 × 84 | 640 | 0 |
| 84 × 84 | 640 | 0.5 in both directions |

Grids cover one full field period. A thirteenth row uses LPQA with its original
256 coil nodes and a 32 × 32 half-period grid: the current upstream convention,
**not established as the original author's exact grid**. Record every row;
this resolution ceiling is a screen, not a promised convergence result.

Before running: 180 s worker ceiling, 185 s external process-group timeout,
one native thread, 128-point field blocks, 64 MiB output ceiling, 3 GiB starting
and 2 GiB live disk reserves. Fresh output only. No optimizer, equilibrium,
topology, force or finite-build work. Keep failed prefixes. Source/input hashes,
named coefficient identity and all signed physical currents must be preserved.
LPQA's nonzero regularization metadata describes self-field/force calculations;
ordinary `BiotSavart.B` here still evaluates filament fields.

## Metric crosswalk and checks

Let `a=|normal|`, `b=B·normal/a`, and `w=a/sum(a)`. Record separately:

- Raw quadratic flux: `0.5 mean(a b²)`; units and parametrization matter.
- Area-weighted local normal RMS: `sqrt(sum(w (b/|B|)²))`.
- Area-weighted mean absolute ratio, and maximum absolute ratio.
- Upstream mean statistic: `mean(|b|)/mean(|B|)` — neither the RMS nor the
  area-weighted mean of the pointwise ratio.
- Global normalized flux, local flux, field magnitudes and minimum field.

Current upstream executable evaluation (`_external_eval.py`) defines the mean
statistic above; its reported `final_B_field` is measured on the major radius,
not averaged over the surface. Distinguish this from documentation shorthand.
Local flux equals normal RMS squared times `mean(a)/2` for a fixed surface, so
SIMSOPT already supplies an appropriate scale-invariant objective for exploration.

At each row, compare native fields at 64 fixed distributed points with our
independent Fourier/filament calculation (normalized error ≤1e-12), and compare
all three flux formulas with the native scalar integrator (relative 1e-11,
absolute 1e-15). Preserve full field/normal arrays for independent metric replay.
The surface reconstruction is shared; this is not a second equilibrium code.

Compare RMS/max with the unchanged 1e-4/1e-3 gates only as boundary-component
screens. Geometry, interior vector error, confinement and full acceptance are
unassessed. A match or mismatch here does not complete Step 4 or validate a
reactor.

## Execution record

The first attempt (`artifacts/boundary-controls-v1/`) stops before any field
evaluation: QUASR's old serialized DOF container has generic `x0`, `x1`, … names.
The adapter now maps the native surface's physical tensor-slot names, requires
the DOF vector to equal `get_dofs()`, and checks every x/y/z tensor entry after
copying. A synthetic legacy-label regression covers this distinction. This
changes the adapter, not the source coefficients, matrix or numerical limits.
The retry in `artifacts/boundary-controls-v2/` completes all 13 rows in 2.657 s
(2.946 s including supervision), with 4.88 MB retained. Its
[evidence record](../../evidence/boundary-control-calibration-v1.json) preserves
every row, exact sources, native implementation/binary hashes and both attempts.
This exploratory run used uncommitted but hash-bound new code atop `9270692`;
it is not a clean-commit confirmatory study.

## Results and decision

| Fixed reference / grid | Area-weighted normal RMS | Maximum sampled ratio | Raw flux |
| --- | ---: | ---: | ---: |
| QUASR 952, original 21² / 160 nodes | 5.74e-16 | 2.56e-15 | 3.83e-31 |
| QUASR 952, 84² / 640 nodes | 2.272906638e-6 | 6.401989272e-6 | 5.773719353e-12 |
| QUASR 952, shifted 84² / 640 nodes | 2.272906638e-6 | 5.941287614e-6 | 5.773719353e-12 |
| LPQA 92598, 84² / 640 nodes | 5.383149980e-4 | 2.033327190e-3 | 9.999529352e-7 |
| LPQA 92598, shifted 84² / 640 nodes | 5.383149980e-4 | 1.992148596e-3 | 9.999529352e-7 |
| LPQA 92598, 32² half-period / 256 nodes | 5.383257517e-4 | 1.928126343e-3 | 9.999999992e-7 |

QUASR is a **positive boundary-component control on the tested refined grids**:
RMS is about 44 times below 1e-4 and sampled maximum about 156 times below 1e-3.
The original collocation grid's near-zero residual is misleading: refinement
reveals a finite error. RMS is stable across later refinements; sampled maximum
and absolute-mean statistics still move with grid phase. This is not a continuous
maximum bound or evidence that the Goodman coil family can achieve this result.

LPQA's 32² half-period row reproduces both archived mean and maximum statistics
to floating-point precision. Its raw flux lies just below the author's 1e-6
threshold, explaining the archived zero. The fine-grid maximum is larger than
the archived grid's value. At original physical scale, the refined RMS exceeds
our boundary screen by 5.38 times and sampled maximum by 2.03 times; this is a
stricter/different comparison, not a failed reproduction. Our older LPQA raw-flux
profile and this Goodman normal-RMS screen remain distinct.

All 13 independent sampled-field comparisons pass (largest normalized error
8.742e-16), as do all 39 native scalar-integrator comparisons. Forty-two synthetic
metric/representation tests pass, including legacy-name recovery. No complete
positive control has been established for the Goodman target, interior field,
geometry/current limits or pressure/engineering models.

Independent read-only replay verifies 17 source and 13 array identities,
all 13 row records, all 156 metric scalars using separate `math.fsum` arithmetic,
and 832 saved field comparisons. LPQA's reproduced mean/max differ from the
archive by +1.735e-18 / −8.674e-19. QUASR's area-weighted absolute mean still changes
21.2% from 42² to 84² and another 8.29% on shifting, despite stable RMS.
A separate direct decoding of all 661 original tensor coefficients reproduces
four saved surface grids without SIMSOPT: point error ≤3.109e-15 and normalized
normal-vector error ≤3.769e-15. This supports the legacy mapping and rules out
surface truncation as the explanation for the coarse/fine difference.
These are same-machine numerical checks, not external expert review or an
independent equilibrium calculation.

**Next decision:** normalized boundary error is calculable and demonstrably small
for one genuine matched reference. Stop treating every failed coil score as the
same issue. Compare raw-flux and local-normalized objectives from the same Goodman
seed, with unchanged endpoint gates and all failed proposals retained.
