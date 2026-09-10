# Normalized feasibility continuation — 2026-09-10

Protocol 189632d preceded implementation b71bf45, all optimization runs and the
post-search holdout. Original unnormalized evidence is preserved. One shared
initial full bundle fixes the common scale factor at 909616.6005669826.
All four arms pass the frozen directional-gradient screen (maximum finest error
8.843e-9) and both methods' repeats have identical proposals, counters and values.

| Method, each repeated twice | Actual bundles, including probes | Outcome |
| --- | --- | --- |
| L-BFGS-B | 10 | Stops after one iteration at unchanged solver x0 |
| Pinned AL | 752 | Returns after its outer-loop cap; nonzero violations remain |

Both use fewer than their 1500-bundle maximum. This is not equal consumed work
and not a method ranking. AL's first repeat took 51.718 s; its best evaluated
candidate was attempt 711. L-BFGS-B's selected best is **a directional-test probe**
(attempt 4), not an accepted optimizer step; the predeclared selection rule
includes every completed evaluation, including probes.

## Important falsification of the first diagnosis

Global normalization does **not** fix L-BFGS-B's one-step termination. After the
seven probes, its three solver evaluations have merits 0.5, 1.37938e18 and 0.5.
The first and third have the **same x hash**. A relative-reduction convergence
flag follows a disastrous trial and return to the unchanged start, even with an
order-one merit. Small absolute objective scale was a plausible contributor in
the original pilot, but **is not a sufficient explanation**. Conditioning,
initial step size and the nonlinear/thresholded penalties need investigation.
The current data do not single out a unique cause. No tolerance was changed.

## Independent post-search evaluation

The holdout reloads each method's serialized best field, recomputes unthresholded
quadratic flux using a separate NumPy reduction, refines both surface and coil
quadrature, and uses the existing independent Fourier-derivative geometry path.
All 120 physical coil pairs are searched at each of four curve resolutions;
plasma clearance uses 20,000 curve points and a full-torus surface series through
512x512. Validation never feeds information back into these searches.

| Finest holdout metric, reactor-scale geometry | L-BFGS-B | AL | Required |
| --- | --- | --- | --- |
| Unthresholded quadratic flux | 1.09935194e-6 | 2.19687449e-7 | <=1e-8 |
| Unique total length, m | 219.99995562 | 220.00084245 | <=220 |
| Maximum curvature, 1/m | 0.90032817 | 0.99449856 | <=1 |
| Sampled centerline coil clearance, m | 1.09258963 | 1.06154259 | >=1.06 |
| Sampled coil/plasma clearance, m | 3.16230235 | 3.19503026 | >=1.3 |

Both flux quadrature-refinement screens pass. L-BFGS-B fails flux; AL fails flux
and length. The 0.842 mm reactor-scale length excess is **not waived**. AL's
roughly fivefold field-error reduction is therefore not a feasible improvement
or SoTA claim. Mean surface |B| remains approximately 0.94612 T for both saved
candidates, but this is not a complete current/field-strength certification.

Distance and curvature results remain finite-sampling screens, not continuum
geometry certificates. In particular, the small AL coil-clearance margin should
not be overstated. Force/torque, current margins, finite-build intersections,
mechanics, QI and free-boundary robustness are still outside this admission.

Evidence: normalized-feasibility-v1/ and normalized-feasibility-v1-holdout.json.
Holdout exits 2, as required for the failed acceptance. Three independent flux
kernel test groups pass, including subthreshold values without clipping. Full
local suite: 86 passed; Ruff clean. The eleven existing fixture deprecations and
the pinned AL's unknown `disp` option warning are retained.

Reproduce in fresh output directories with --normalized-feasibility, then run
scripts/validate_normalized_candidates.py on the completed study. Preserve the
thread/environment settings in OPTIMIZATION_ORACLE_RESULTS.md.
