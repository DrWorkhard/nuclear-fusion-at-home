# Saved-field diagnosis: objective progress differs from normalized error progress

27 September 2026. [Protocol](FIELD_RESIDUAL_PROTOCOL.md) · [Index](README.md) ·
[Machine-readable results](../../evidence/field-residual-results-v1.json).

## Result and decision

The registered eight-pair analysis is complete. The observed responses align much
more strongly with the raw normal-field objective than with the normalized
acceptance residual. **Do not automatically extend these local steps.** Proceed
with matched-reference calibration, then compare normalized-error objectives and
alternative starts under the [research programme](STEP4_RESEARCH_PROGRAMME.md).

| Shifted fine boundary grid | Six base coils | Eight base coils |
| --- | ---: | ---: |
| Normal residual squared-error fraction along observed response | 11.5793% | 19.6497% |
| Raw-objective residual squared-error fraction along response | 88.1283% | 89.6144% |
| Best affine normal-residual RMS | 0.2583270 | 0.2401826 |
| Affine RMS / unchanged 1e-4 limit | 2,583.27 | 2,401.83 |
| Affine coefficient alpha (control=0, measured proposal=1) | 202.567 | 301.019 |

Across all four boundary grids, fitted normal RMS spans 0.2583270–0.2583272 and
0.2401812–0.2401826 respectively. The measured proposals themselves still have
RMS 0.2745649473/0.2677716465. These fitted values are **not magnetic fields at new
coil coordinates**, feasible steps or lower bounds on the coil family's capability.
Alpha is not a proposed step count; subsequent directions and nonlinear responses
may differ completely. The analysis neither proves infeasibility nor predicts
performance of another optimizer.

## Normalization diagnosis

On the shifted fine grid, JN changes by −4.02794e-4/−3.28870e-4 while normal RMS
changes by −1.56696e-4/−1.74674e-4. Boundary field RMS decreases by
0.00606865/0.00508699 T. The exact control-denominator squared-error split has:

- Numerator linear terms: −8.59002e-4/−7.20408e-4.
- Opposing denominator linear terms: +7.72718e-4/+6.26676e-4.
- Net squared normal-error changes, including quadratic/cross terms:
  −8.60709e-5/−9.35761e-5.

This cancellation explains why progress in these two metrics differs for these
observations. It is not a causal current/efficiency attribution: uniform positive
current scaling cancels from normalized normal error, while JN changes. All
decomposition identities and separately implemented arithmetic checks pass.

## Execution, checks and limitations

Clean execution commit: `7b4ec7526e3ba5e815748afe006417c37beda5ef`; source identities
match before/after. One serial run completes in 1.836 s with 55,702 scientific bytes,
below 60 s work/65 s external timeout and 8 MiB combined output. Disk reserves remain
3 GiB at start / 2 GiB during work. No retry, new fields, gradients, geometry bounds,
candidate, equilibrium solve or threshold change.

Coverage: 16 saved models, 8 matched comparisons, 16 residual fits and 8 decompositions.
NumPy and independently authored scalar/`math.fsum` implementations agree within
unchanged tolerances and reconstruct saved JN, normal RMS and field RMS. Every
grid is retained. The launcher requires exit zero and an explicit returned hash
reference; a complete-looking file from a failed worker is not accepted.

Before execution, 203 focused tests pass, including timeout, source/shape/coverage,
short-write and rounding controls; 47 public and 32 documentation/workflow tests
also pass. Independent source/launcher review and a separate 203-test rerun find
no remaining scoped blocker. No fresh full native regression is claimed.

An independent internal result audit verifies 64 unique files / 40,040,460 bytes,
nine source files against the execution commit, sixteen model identities and all
eight ordered pairs. Separate scalar formulas reconstruct 496 quantities from
the saved arrays without importing either diagnostic arithmetic implementation.
No discrepancy or native field calculation occurs in this check.

Known conservative limitation: an extra synthetic sweep fails closed in 7/128
single-point near-perfect-fit comparisons because division by 1e-4 amplifies
last-bit norm differences. All 96 multi-point cases and all real study comparisons
pass. The exact first counterexample remains an expected-rejection regression;
no tolerance was relaxed. Internal numerical review is not external peer review.

Raw inputs/results and qualification logs are bound through the machine-readable
record. No physical admission, Step 4A–4D completion, SoTA advance or MS1 follows.
