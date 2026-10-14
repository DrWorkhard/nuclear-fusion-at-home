# Field acceptance, version 2

Frozen 13 October 2026 by the owner's decision on
[issue #82](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/82).
[Validation index](README.md) · [Calibration evidence](../sota/COILSTELLARATION_CALIBRATION.md)

**What it is:** `acceptance-v2` replaces only the boundary field-error limits. Its
thresholds are set so that the best 10% of a public coil benchmark passes. It means
"as good as the best tenth of a professional coil pipeline", not a physics-derived
tolerance. The original limits (`acceptance-v1`) stay in force and every verdict
reports both versions.

## Definition

| Check | acceptance-v1 (unchanged) | acceptance-v2 |
| --- | --- | --- |
| Boundary \|B·n\|/\|B\| on the 128 × 128 fine grid, both shifts | area-weighted RMS ≤ 1e-4 and maximum ≤ 1e-3 | plain mean ≤ **0.0018** and maximum ≤ **0.013** |
| Interior vector RMS, all three resolutions | ≤ 0.01 | ≤ 0.01 (unchanged) |
| Continuous geometry (length ≤ 3.5 m, coil–coil ≥ 0.06 m, coil–plasma ≥ 0.08 m, curvature ≤ 12 /m) | pass | pass (unchanged) |
| Flux and current limits, independent B and A cross-checks | pass | pass (unchanged) |

The plain mean is used because it is the public benchmark's statistic; the
[calibration](../sota/COILSTELLARATION_CALIBRATION.md) showed that our mean on this
grid matches it within 0.06%. The values are frozen in
[`acceptance_v2.py`](../../src/fusion_baselines/acceptance_v2.py); any change needs a
new version, never an edit.

## Calibration

Source: the evaluation split of Proxima's CoilStellaration benchmark
(`proxima-fusion/coilstellaration`, revision `286a268c664938519af6ceacfb4ec8143f64e20e`,
`results/eval-part-0.parquet`, SHA-256 `5425524969d6ae7f…`), all 8,058 quasi-isodynamic
cases with DESC coil sets. One common percentile q is applied to both statistics and
chosen so that 10% of the cases pass both together: q = 0.1287 gives 0.00178 and
0.0130, rounded to two significant digits as 0.0018 and 0.013. Then 820 cases (10.2%)
pass. Cases with two field periods, like ours, pass at a lower rate (6.6% of 1,345).
[`acceptance_v2_calibration.py`](../../scripts/acceptance_v2_calibration.py) reproduces
the thresholds from the pinned file.

## How to evaluate

`python scripts/acceptance_v2.py <run directory>` reads a completed fit or check run
(`result.json` and the saved fine-grid arrays), checks that the arrays reproduce the
recorded boundary RMS, and prints both verdicts. It needs NumPy.

## What it does not mean

- **Set with our results known.** Our fixed-target fits already ranked near the top
  10% of this benchmark when v2 was chosen; v2 results must say so, and v1 results are
  never relabelled.
- **Benchmark-relative, not physics.** A tolerable field error should ultimately come
  from realized-field consequences (#26). The benchmark covers QI plasma shapes with
  coils of Fourier order 7, not our target or coil family.
- **Not Step 4 or physical acceptance.** Passing v2 accepts the field and geometry
  checks only. Magnetic surfaces, benefit transfer, pressure and engineering remain
  open ([Step 4 requirements](../steps/STEP_4_PLASMA_AND_COILS.md)).
