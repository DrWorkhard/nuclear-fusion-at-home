# Fixed-invariant radial action pilot v1 — results

Protocol 598a4f9; tested implementation 30c5944; run on 2026-09-10.
All four input hashes match. This is a bounded measurement result, not global
maximum-J qualification or a reproduction of the paper's full parameter domain.

## Observations

Every case has 40 alpha/Bstar cells and 80 central-window well families. All
160 cells pass the geometric matching screen; all 320 families pass both declared
refinement screens. There are no censored wells in these recorded traces.

| Case | Negative | Positive | Unresolved | Range of (dA/ds)/A |
| --- | ---: | ---: | ---: | --- |
| nfp2 vacuum | 0 | 80 | 0 | 0.009016 to 0.419811 |
| nfp2 nominal beta 2% | 80 | 0 | 0 | -0.242464 to -0.045291 |
| nfp3 vacuum | 15 | 64 | 1 | -0.011425 to 0.716063 |
| nfp3 nominal beta 2% | 42 | 38 | 0 | -0.102250 to 0.316384 |

The nfp3 vacuum unresolved family is at q=0.9, alpha index 4; estimate
-4.02279e-5 with empirical allowance 1.00898e-4. It is not counted as negative.
Maximum trace/radial refinement changes over all families are 2.07534e-4 and
3.80772e-4. Trace/action execution took 5.91, 5.92, 7.75 and 8.82 seconds.

nfp2 therefore shows the expected pressure-associated sign change within the
sampled domain. nfp3 is not uniformly negative at this pressure and radius.
The Bstar domain is fixed across radius within a case, but chosen separately
between equilibria: this is not tracking identical particles across beta.

## Independent verification

The second integrator was committed as 9e5d424 after seeing pilot outcomes;
its validation is explicitly retrospective. It uses 128-point Gauss-Legendre
quadrature on each segment and does not call the exact segment-action formula.
All 13,440 recorded well integrals agree to a maximum relative discrepancy
5.315e-10 (declared tolerance 1e-6). Rebuilt matched stencils agree; the maximum
normalized derivative change is 2.372e-9 (tolerance 1e-5). Every sign and
refinement classification is unchanged. This verifies integration/accounting,
not the input equilibrium or independence of trace geometry.

Twelve matching/radial controls include an analytic parabolic magnetic well
with known normalized radial derivative -0.6; two separate quadrature tests
cover exact integrals and forbidden intervals.

Evidence: `evidence/qi-radial-action-v1/*.json` and
`evidence/qi-radial-action-v1-quadrature.json`; hashed raw NPZ traces are local
ignored artifacts, regenerable with `scripts/measure_radial_action.py` using
fresh `--output` and `--raw` directories.

## Limits and next checks

The conclusion applies only to s0=0.5, the declared radial stencil, eight alpha
values, five sampled-domain pitches and central-window wells. Allowances are
empirical, not rigorous error intervals; well identity between radial samples
and equilibrium resolution are not established. Radial derivatives use the
stated VMEC straight-field-line gauge, not a gauge-independent non-omnigenous
definition. Full invariant-domain coverage, continuum QI topology and independent
finite-pressure trace validation remain open. No G4 or SQuID-C readiness closure.

## Fresh-clone regression

A detached clean clone at 30c5944, with no pre-existing environment or data,
passed the locked core command: Ruff clean, 105 tests passed, six data-dependent
skips. Its strict QI integration then freshly extracted the verified archive and
passed five tests with zero skips (W7-X deselected). This predates the two new
quadrature tests; it does not include a native W7-X bootstrap or hosted CI.
