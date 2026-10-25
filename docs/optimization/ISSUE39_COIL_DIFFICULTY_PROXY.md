# Does L∇B rank plasmas by coil-fitting difficulty? (#39)

[Active coil research](README.md) · [Issue #39](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/39) ·
[Programme #116](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/116)

**Question.** #116 plans the joint optimizer (#39) as an outer plasma loop with cheap coil-difficulty proxies,
plus periodic full coil fits. ConStellaration's minimum normalized magnetic-gradient scale length (L∇B) is
designed as a coil-simplicity metric and is already computed by the #112 scorer. Does it rank our plasmas by
how hard they are to fit with our coil recipe? A first test on #114 (N33, n = 5) gave Spearman ρ = −0.6,
inconclusive. This test (N45) extends it to n = 15. It is exploratory, and its rule was preregistered before
any data was selected. [Evidence](https://github.com/patrickmahlstein/nuclear-fusion-at-home/tree/81fc86ae7e53bce5cea15dc89c9a436306fca93b/evidence/issue39-lgradb-proxy):
preregistration and amendment, scripts, per-fit results, SHA-256.

**Inputs.**
- Plasmas: nfp 2, A 9.5–10.5, log10 QI ≤ −2.5, |ι|/nfp ≥ 0.15 rows of the ConStellaration dataset
  (rev `8da71572`, MIT licence; 1,597 eligible). For each target L∇B, the nearest row was taken. Plus N33's
  four rows and selected401.
- Amendment 1, before any fit: no eligible row has L∇B above 7.34, so targets 8–11 were replaced by 2, 3, 6
  and 7. The covered range is L∇B 2.0–7.4.
- Intake: [#115](ISSUE115_TARGET_INTAKE.md) `make_wout.py` and `make_target_spec.py`, orientation-matched inputs.
- Fits: the neutral circular seed (6 planar coils, r = 0.4 m), then `fit_coils.py --seconds 1800
  --check-seconds 900` with current margins, order 5 and the default objective. Code `954fd5a`, SIMSOPT 1.11.1,
  vmecpp 0.8.0, one thread, serial.
- Control: refitting selected401 gives a boundary mean of 0.0016095, against N33's 0.00161. This is within
  the preregistered 5%, so N33's five results enter as recorded.

**Result.** The outcome is the worse-shift fine boundary mean (acceptance v2's `mean`).

| Proxy | Spearman ρ with boundary mean (n = 15) |
| --- | ---: |
| **L∇B** | **−0.82** (preregistered "supports" at ≤ −0.45; usable at \|ρ\| ≥ 0.7) |
| Edge mirror ratio | +0.41 |
| \|ι\|/nfp | +0.34 |
| Flux compression | −0.32 |
| Vacuum well | −0.26 |
| log10 QI | +0.11 |
| Maximum elongation | +0.09 |

- Boundary means run from 0.0045–0.0067 at L∇B 2–3.5 down to 0.0016–0.0031 at L∇B 6–7.4.
- L∇B also ranks the boundary maximum (ρ = −0.78) and the interior RMS (−0.61).
- The result is robust:
  - without selected401, on which the fitter was developed, ρ = −0.82;
  - with N45's ten plasmas alone, ρ = −0.75;
  - ranking row 20912 worst, ρ = −0.81. Its continuous geometry is unresolved, but it has an eligible
    candidate, so the preregistered rule keeps it.
- All 15 fits completed. None passes acceptance v2, as expected for this short recipe.

**Conclusion.** Within this family (nfp 2, A ≈ 10, QI-good, L∇B 2–7.4), L∇B is a usable ranking proxy for
coil-fitting difficulty with our recipe. Maximum elongation, a common shape heuristic, is not. For #39 this
supports using L∇B as the outer loop's coil-difficulty term or constraint, with periodic full fits as a check.

**Limits.**
- One recipe (30-minute, order-5 fit from a neutral seed), one seed rule and one machine.
- Errors on different targets are not acceptance-comparable; this ranks difficulty only.
- Spearman ranks do not give a calibrated error prediction. Within a narrow L∇B band the spread is large:
  at L∇B ≈ 6, boundary means range 0.0016–0.0038.
- Untested outside the family: high L∇B (> 7.4, none eligible), nfp 3, other aspect ratios.
- Not a physics or acceptance claim.
