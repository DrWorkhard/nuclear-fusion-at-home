# ConStellaration metrics for reference401 and the improved Step 3 target

**No measurable coil-simplicity cost.** The improved Step 3 target (selected401)
has a minimum normalized magnetic gradient scale length L∇B of 6.1388, compared
with 6.1404 for reference401. This is a change of −0.026%, inside the ±5% band
preregistered in [issue #76](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/76).
By this proxy, the Step 3 gain does not make the plasma harder to build with coils.
The rule therefore does not recommend L∇B as a constraint or objective term for the
joint pilot ([#59](https://github.com/DrWorkhard/nuclear-fusion-at-home/pull/59),
[#63](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/63)).
Recorded 11 October 2026. This is a proxy comparison, not a coil design or
physical acceptance.

## Question, inputs and tool

Coil fits stall near a boundary error of 0.0018 for both targets. Does the Step 3
improvement cost coil simplicity as measured by the L∇B proxy of ConStellaration's
"simple-to-build QI" problem ([background](../sota/CONSTELLARATION.md#lessons))?

| Target | Input | SHA-256 |
| --- | --- | --- |
| reference401 | [reference-input-401.json](../../evidence/plasma-design-v2/reference-input-401.json) | `57394ef6…` |
| selected401 | [selected-input-401.json](../../evidence/plasma-balanced-v1/selected-input-401.json) | `6bec3483…` |

The [script](../../scripts/constellaration_metrics.py) checks both full hashes against
`coil_check.TARGETS` before use. It ran with `constellaration==0.2.6`, the frozen
leaderboard version, in a separate virtual environment: Python 3.12.13 on macOS
15.7 (Apple M1, arm64), one thread. Resolved dependencies: vmecpp 0.4.11,
booz-xform 0.0.9, simsopt 1.8.1, desc-opt 0.17.1, jax/jaxlib 0.5.3, numpy 2.2.6,
scipy 1.17.1, pymoo 0.6.1.5, netCDF4 1.7.2, with the existing Homebrew NetCDF 4.10.1.
booz-xform is built from source. That build only succeeded with
`CXXFLAGS="-nostdinc++ -isystem <CommandLineTools SDK>/usr/include/c++/v1"`,
because the local Command Line Tools hide the libc++ headers. Nothing was installed
system-wide.

## Conversion and check

Our VMEC++ inputs and ConStellaration's `SurfaceRZFourier` use the same convention:
R = Σ rbc cos(mθ − n·nfp·φ) and Z = Σ zbs sin(mθ − n·nfp·φ). Each `rbc(m,n)` and
`zbs(m,n)` goes to `r_cos[m, n+9]` and `z_sin[m, n+9]` (m ≤ 4, |n| ≤ 9).
`n_field_periods` is the input's `nfp = 2`, and the boundaries are stellarator
symmetric. R00 is exactly 1 in both inputs, so the R00 = 1 normalization scales
by 1. Only the boundary is used. The forward model then applies its own defaults:
near-vacuum profiles (p = 1 − s Pa, zero current), edge flux πa², and high-fidelity
VMEC++ settings (mpol = ntor = 10, ns = 25/51/99).

- The arrays equal VMEC++'s own reader of the same files exactly.
- On a full-torus grid of 64 × 128 points, R and Z of the converted surface differ
  from a direct sum over the JSON entries by at most 2.0e-15. The boundary of the
  converged equilibrium differs from the input by at most 4.4e-16, with no θ flip.
  Both runs converged with fsqr ≈ 1.0e-15 and `ier_flag` 0.

## Hash-bound custom intake (#112; software support)

The current script also accepts a stellarator-symmetric VMEC++ JSON boundary:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  <separate-venv>/bin/python scripts/constellaration_metrics.py \
  --input <boundary.json> --sha256 <full-input-sha256> --target-id <name> --output <new-dir>
```

The exact bytes are checked before JSON parsing. Coefficients must be finite,
mode identities unique and R00 positive. The script requires the separate pinned
`constellaration==0.2.6` environment; it does not modify the native environment.
Only boundary geometry is used. Input pressure, current, flux and solver settings
do not replace the frozen forward model defaults. Omitting `--input` replays the
two registered targets; `--confirm` retains the extra public evaluator calls.

Conversion checks compare the actual surface coefficients and outer Wout
coefficients with the input in physical modes `(m, n*nfp)`. Wout `xn` already
contains `nfp`. Canonical cosine/sine coefficients give a numerical L1 bound on
each full-torus coordinate residual, avoiding modes that vanish on the sampled
grid. Both bounds must be at most `1e-10*R00`; the unchanged 64×128 sampled
checks must also pass. This is floating-point validation, not interval arithmetic
or a physical requirement. Nonfinite coordinates and failed checks leave an
incomplete record and a nonzero CLI status; metrics alone do not establish success.

Once the forward model returns a Wout, the script attempts to save it even if
later geometry validation fails. A save failure is recorded separately as
`wout_save_error`; it does not replace the original rejection or change completion.
Retained Wouts from incomplete records are diagnostic artifacts, not qualified
controls. This prospective retention change neither recovers missing historical
Wouts nor authorizes rerunning failed controls.

This implements software intake only. The historical results above and below are
unchanged. Reproducing #76, seeded dataset controls, resolution sensitivity and
the complete scorecard remain separate qualification work under
[issue #112](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/112).

## Metrics: default high-fidelity forward model

| Metric | reference401 | selected401 | Difference |
| --- | ---: | ---: | ---: |
| Aspect ratio | 9.99510 | 9.99555 | +0.005% |
| Maximum elongation | 5.96302 | 5.95671 | −0.11% |
| Average triangularity | −0.235298 | −0.236578 | −0.00128 |
| Edge rotational transform per field period | −0.251059 | −0.250772 | \|ι\| −0.11% |
| QI residual | 2.3756e-5 | 2.1949e-5 | −7.6% |
| Edge mirror ratio | 0.233303 | 0.234935 | +0.70% |
| **Minimum normalized L∇B** | **6.14039** | **6.13881** | **−0.026%** |
| Vacuum well | −0.0157702 | −0.0158143 | −4.4e-5 |
| Flux compression in bad curvature | 1.39591 | 1.39774 | +0.13% |

**Benchmark context only.** A design is feasible if its largest normalized
constraint violation is at most 0.01. Neither target is feasible for any of the
three problems, so every score is 0:

| Problem | Feasibility (ref. / sel.) | Violated constraints (both targets) |
| --- | ---: | --- |
| Geometric | 1.499 / 1.499 | aspect ratio > 4; triangularity > −0.5; \|ι\|/N<sub>fp</sub> < 0.3 |
| Simple-to-build QI | 0.193 / 0.191 | elongation > 5; edge mirror ratio > 0.2 |
| MHD-stable QI | 0.551 / 0.553 | flux compression > 0.9; vacuum well < 0 |

These values come from the problem classes' methods applied to one forward run.
Calling each problem's public `evaluate()` on the saved boundary JSON gives
identical values. In the simple-to-build problem, aspect ratio, ι and QI pass
(log₁₀ QI −4.62 / −4.66 ≤ −4). For scale: a feasible design scores L∇B/20, so
the leaderboard's best score of 0.6577 corresponds to L∇B ≈ 13.2.

## Rule outcome and limits

(6.13881 − 6.14039) / 6.14039 = −0.026%, inside ±5%. The recorded outcome is
**no measurable cost**. Other metrics are reported as measured: the QI residual is
7.6% lower, the mirror ratio is 0.7% higher, and every other metric changes by at
most 0.6%.

L∇B is a proxy, not a coil design. The calculation is vacuum only. ConStellaration's
QI residual is a different metric from the Step 3 bounce-action diagnostic. Its
resolution (ns 99) is coarser than our 401-surface Wouts. Upstream tests Linux
with Python 3.10. This run used macOS with Python 3.12 and was not compared with the
hosted evaluator.

Resources: the environment took 0.96 GiB, plus a 1.21 GiB download and build cache
(limit 3 GB). Compute took about 11 minutes, within the 30-minute limit: a main run
of 130 s, a confirmation run of 406 s with the extra `evaluate()` calls, and smoke
tests. At least 28 GiB of disk stayed free throughout. The two runs produced
bit-identical metrics and Wouts.

Raw outputs are kept locally in the ignored `artifacts/issue76-constellaration-metrics/`
folder (12 MB). It holds install logs (including two failed booz-xform builds), the
package freeze, both runs and the Wouts. They are not archived under an evidence
tag. SHA-256: report `8ca186fd…`, Wouts `e3c723fa…` and `8e916e77…`.
To reproduce, run `uv venv`, then `uv pip install constellaration==0.2.6`, then
`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 <venv>/bin/python scripts/constellaration_metrics.py --confirm --output <new-dir>`.
