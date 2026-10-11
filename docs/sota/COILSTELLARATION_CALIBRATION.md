# CoilStellaration calibration with our own checker

**This pipeline does not reach our boundary limit under our own metric.** Ten
CoilStellaration coil sets were recomputed with our checker. Their area-weighted
boundary RMS of |B·n|/|B| lies between 0.0014 and 0.0039 (median 0.0026). Every
case is above 1e-3, ten times our limit of 1e-4. The mapping check passed: our
plain mean agrees with the dataset's statistic within 0.06% in all ten cases. By
the rule preregistered in
[issue #75](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/75), the
outcome is recorded here, and a versioned acceptance definition is proposed
separately in [#82](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/82).
No limit changes. Recorded 11 October 2026. [Folder index](README.md) ·
[earlier comparison](CONSTELLARATION.md#calibration-of-our-boundary-limit)

## Question and inputs

The [earlier comparison](CONSTELLARATION.md) used the dataset's own statistic, a
plain mean on its own grid. Does the conclusion hold under our own metric, grid and
field kernel?

| Input | Revision or SHA-256 |
| --- | --- |
| `proxima-fusion/coilstellaration` (Hugging Face) | revision `286a268c664938519af6ceacfb4ec8143f64e20e` |
| `results/eval-part-0.parquet` | `5425524969d6ae7f844195e00bae0ec313228aadb27d905549791f6251695a37` |
| `coilsets/id_to_file_map.parquet` | `a7e119bc38f8e2f26cbafb072c0ed159abf40c1ff8a93c7b7a870fdf2afbe2c1` |
| `proxima-fusion/constellaration` (boundaries) | revision `8da71572eb63ce93e77ce89bec0d7c30b7eba89e` |
| Conventions read from | `proximafusion/coilstellaration` `03d1dc2`, DESC `v0.17.1` |

Both file hashes match the Hub's LFS records. **Sample:** rows with DESC results
(`desc_metrics_id` present, 8,058), two field periods, six coils per half-period
and stratum `tight` give 107 rows, all with coil order 7. These were sorted by
`requirements_id`, the only identifier that is unique over all 13,299 rows.
`numpy.random.default_rng(0).choice(107, 10, replace=False)` (numpy 2.5.4) drew the
ten rows. "Median case" means the two middle cases by dataset mean, and both must
pass. These two readings were fixed before any field was computed. The ten coil
sets and nine distinct boundaries were fetched by byte range only.

## Method and reconstruction check

The [script](../../scripts/coilstellaration_calibration.py) (SHA-256 `5930aa7d…`)
converts each DESC `FourierXYZCoil`, stored as [sin N … sin 1, const, cos 1 … cos N]
with s ∈ [0, 2π), to our Fourier layout. It adds DESC's stellarator partners: a π
rotation about the horizontal line at φ = π/NFP, with reversed current. It then
rotates both by one field period, which gives 24 filaments with 512 nodes each. The
ConStellaration boundary uses the same convention as our inputs, R = Σ r_cos
cos(mθ − n·NFP·φ). The field is the independent NumPy Biot–Savart sum and the
128 × 128 one-period grid of `coupled_coil_audit` (SHA-256 `3f9a5cee…`). RMS and
maximum come from `boundary_control_metrics` (`7ab1d0a5…`), the same function the
fine checks use.

**Reconstruction check.** As a gate before all ten cases, each case was also
evaluated on the dataset's own grid, DESC `LinearGrid(M=80, N=80, NFP=2, sym=True)`:
81 midpoint θ in (0, π) × 161 ζ. In all ten cases, mean, maximum and standard
deviation match the dataset to at most 3.2e-13 relative. The near-zero minimum
matches to 3.4e-15 absolute, and mean and maximum coil lengths to 1.1e-13. In
case 0, doubling the coil nodes to 1,024 changes RMS on our grid by 7e-16. The
half-shifted grid changes RMS by at most 2e-5 relative.

## Results

Cases 3 and 7 are the two middle cases by dataset mean.

| # | `requirements_id` | Dataset mean | Our plain mean | Deviation | **Our RMS** | Our max |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 0 | `DdpFrk83HqqGzmbsvkdq9sj` | 0.002283 | 0.002282 | 5.8e-4 | **0.003330** | 0.0185 |
| 1 | `DfGhoBAK9sH5nsWRsBPkXyw` | 0.002988 | 0.002988 | 2.1e-4 | **0.003940** | 0.0173 |
| 2 | `DWYXeLKRtb7gkrDqT7HwoSM` | 0.001586 | 0.001586 | 6.9e-5 | **0.002230** | 0.0156 |
| 3 | `DRw2vofVCi8eWfLNv8QW6i8` | 0.002047 | 0.002047 | 1.4e-4 | **0.002454** | 0.0162 |
| 4 | `DFEBhTk52rRoxSa4kYxwo4r` | 0.002649 | 0.002648 | 2.1e-4 | **0.003710** | 0.0221 |
| 5 | `D2WaHaFz2UhtSttpDaFx28y` | 0.002574 | 0.002574 | 3.7e-5 | **0.003089** | 0.0178 |
| 6 | `D2R3fcShkv7wyBpkprtFBfE` | 0.001100 | 0.001100 | 1.2e-5 | **0.001385** | 0.0079 |
| 7 | `DGfjpKzCQtwdgexbEbB9Gvp` | 0.002272 | 0.002272 | 1.5e-4 | **0.002675** | 0.0222 |
| 8 | `D9SW2sxpim2TVctmaSjWEdU` | 0.001335 | 0.001335 | 2.5e-4 | **0.001735** | 0.0104 |
| 9 | `D48ywFDdPmQ58HaNBN2cBBj` | 0.001986 | 0.001985 | 1.7e-4 | **0.002555** | 0.0154 |

Our RMS is 1.18–1.46 times the plain mean. Every maximum also exceeds our 1e-3
limit, by 8–22 times. For orientation only, since the plasmas differ, our
[construction-margin fits](../optimization/ISSUE70_CONSTRUCTION_MARGINS.md) (RMS
0.0018339 / 0.0017283) are lower than 8 and 9 of these ten cases.

## Rule outcome and limits

The mapping check passes: the middle-case deviations are 1.4e-4 and 1.5e-4, against
the 5% allowed. All ten RMS values exceed 1e-3. The preregistered reading is
therefore **"this pipeline does not reach our limit under our own metric"**. The
proposal for a versioned acceptance definition is
[#82](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/82).

Ten cases from one benchmark and one stratum; filament coils without finite build;
vacuum boundaries; ConStellaration QI plasmas rather than reference401; coil order
7 against our 5; Proxima's own requirement targets. These results show what one
professional pipeline achieves, not which field error a plasma tolerates. They are
no physical acceptance and change no limit.

Resources: a separate environment (Python 3.12.13, numpy 2.5.4, scipy 1.18.1,
pyarrow 26.0.0; 0.27 GB) on macOS 15.7 (Apple M1), with one thread. The final run
took 410 s and downloaded 34.5 MB, plus the 16.0 MB evaluation split and the
10.9 MB id map fetched before it. Two earlier attempts stopped while fetching, before
any field was computed. One hit the Hub's resolver rate limit (HTTP 429). The other
scanned id columns too slowly and was stopped after 21 minutes. By what their code
can request, all downloads together stay below 0.2 GB (limit 3 GB). At least 29 GiB
of disk stayed free. Raw outputs (27 MB) are kept locally in the ignored
`artifacts/issue75-coilstellaration-calibration/` folder: inputs with hashes, three
run logs and `report.json` (`d98321d4…`). They are not archived under an evidence
tag. To reproduce, create a fresh environment with `uv venv` and
`uv pip install numpy scipy pyarrow`, then run
`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 <venv>/bin/python scripts/coilstellaration_calibration.py --output <new-dir>`.
