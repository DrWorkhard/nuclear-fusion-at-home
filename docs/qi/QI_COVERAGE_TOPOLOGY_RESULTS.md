# Expanded QI coverage and contour results — 2026-09-09

Protocol **520dc95** preceded implementation **5979c97** and every new real-data
run. All three cases completed without changing inputs, thresholds or exclusions.
The command returned **2**, correctly retaining an overall failed screen.

| Case | Action coverage/refinement | Contour winding screen | Max relative action change, 1601->3201 |
| --- | --- | --- | --- |
| nfp1 | Fail: one inaccessible surface/pitch cell | Fail: same cell has zero roots | 1.41480e-4 on covered cells |
| nfp2 | Pass | Pass | 2.50377e-4 |
| nfp3 | Pass | Pass | 2.66658e-4 |

There are 135 distinct surface/pitch cells: five radii and nine pitches per case.
134 have complete-alpha coverage and pass the declared action refinement checks.
Those same 134 classify as two poloidally closed root graphs at all three contour
resolutions: 402/405 grid-level classifications pass. No censored wells occur in
the recorded action grids. All 147 path/hash records across the result and
supplementary diagnosis match their local files.

## Negative result and independently bounded cause

nfp1 at s=0.10, q=0.01 has Bstar=2.561015554880713 T, no complete wells on any
sampled field line, and zero contour roots on every sampled theta slice.
The finest surface grid minimum is 2.561574760392063 T. This is not merely
an assumption based on samples: a **retrospective** supplementary diagnostic
bounds the unsampled interpolation error using the Fourier coefficients.

For a uniform periodic grid, linear interpolation has error <=h^2 sup|f''|/8.
The tensor-product interpolation operator is a sup-norm contraction, so the
theta and zeta bounds add. For a cosine Fourier sum,
sup|B_theta_theta| <= sum|b_mn|m^2 and
sup|B_zeta_zeta| <= sum|b_mn|(n/nfp)^2.
The resulting bound here is 3.49060245e-5 T. Consequently the continuous
radially interpolated Fourier field stays at least **5.24299487e-4 T above
Bstar**. The corresponding fixed energy/magnetic-moment combination is
energetically inaccessible on this surface, not a passing-particle orbit or
evidence of broken QI. These are ordinary-double-precision analytical bounds,
not a directed-rounding interval proof or validation of the physical equilibrium.

The original interval was frozen on s=0.25,0.50,0.75. Extending to s=0.10 while
keeping its lowest extrapolated pitch was not guaranteed to stay in the
accessible trapped domain. That is the useful failure: future radial studies
must explicitly track the valid invariant domain, without silently changing
Bstar between radii. We do **not** relabel the preregistered nfp1 result as a pass.

Supplementary bound implementation 2e572dc passed three analytical/invalid-input
tests before the diagnostic script ran. The diagnosis is explicitly labelled
retrospective in evidence/qi-coverage-v2/domain-diagnosis.json.

## Passing measurement does not mean good confinement

The largest fine-grid action envelopes are approximately 0.327, 0.311 and 0.138
for nfp1, nfp2 and nfp3. These wider-pitch results are much larger than the maxima
in the original bounded v1 sample. The protocol tests **measurement stability**,
not a physical acceptance threshold on that envelope. The envelope mixes wells
and is normalized by mean action; it is not yet a well-family-resolved QI score.

Contour checks cover only the two-simple-root graph class and finite sampling.
They cannot exclude subgrid features or qualify the whole trapped-particle domain.
Branch-family identity, finite-pressure maximum-J, particle/transport validation,
and a useful constrained optimization baseline remain open. No SoTA advance or
SQuID-C readiness is claimed.

## Reproduction

`PYTHONPATH=src .venv/bin/python scripts/expand_qi_coverage.py`

Use an isolated checkout or fresh --output/--raw directories; existing evidence
is deliberately protected against overwrite. The v1 evidence currently contains
absolute input paths, so the experiment runner still requires local path
adaptation on another machine. The strict integration command below does not.

`bash scripts/run_qi_integration.sh`

At detached commit 587db93 in a fresh clone, this created the locked environment,
verified the existing 1 GiB archive cache, freshly extracted the data and passed
five numerical/metadata integration tests, with zero skips (the separate W7-X
test was explicitly deselected). No previous external solver tree or generated
artifact directory was copied. This verifies a cached-download bootstrap, not a
new network download or fresh VMEC solve. The clone remained clean. Initial
harness attempts had a wrong working directory, then a uv-cache sandbox denial;
neither reached the tests. The corrected permitted invocation passed.

The full local suite now passes 75 tests; Ruff passes. Eleven netCDF fixture
deprecation warnings remain recorded, not suppressed. Hosted CI and the complete
native-solver scientific bootstrap are still unwitnessed.
