# Step 3 result: an improved plasma target of our own

**Complete, 14 September 2026**, for one registered vacuum study. English summary
of the German [detailed results at the freeze tag](../validation/REPRODUCING_RESULTS.md); that report
and the evidence files remain authoritative.
[All steps](README.md) · [Roadmap](../PROJECT_PLAN.md) · [Status](../STATUS.md)

## What the step had to show

A real change to a quasi-isodynamic-like plasma boundary, with freshly computed
equilibria, that improves a registered physics metric and is confirmed by
separate checks — unlike Steps 1 and 2, a genuine improvement was required. The
registered protocol `docs/qi/PLASMA_BALANCED_PROTOCOL.md` at that tag fixed all gates
before the first new calculation.

**Setup.** Starting point: the nfp2 vacuum configuration from Goodman et al.'s
open QI dataset. Four named boundary modes may change: `rbc(1,1)`, `zbs(1,1)`,
`rbc(2,0)`, `zbs(2,0)`. Equilibria are cold-started VMEC++ solves with 201 or 401
radial surfaces, fixed boundary flux and major radius R00 = 1 m.

**Metric.** S is the relative variance of the bounce action (a trapped-particle
motion diagnostic), averaged over 35 cells of flux surface s ∈ {0.1, 0.25, 0.5,
0.75, 0.9} and bounce level q ∈ {0.03, 0.1, 0.3, 0.5, 0.7, 0.9, 0.97}.
Lower is better. A narrow “training” domain and the wide domain were **both used
during construction**, so the result is not a blind generalization test.

## How the design was found

- **Phase A:** the 16 shapes kept from the first, rejected attempt were evaluated
  on the wide domain without new solves. None qualified; the only one improving
  both domains violated the local mean-action limit.
- **Phase B:** eight ±10 µm finite-difference solves fed a local linear model,
  which proposed a joint step. All three proposals (full, half, quarter step) were
  solved for real; the full step had the lowest wide score and was selected:
  `rbc(1,1)` −1.0e-4 m, `zbs(1,1)` +5.12e-5 m, `rbc(2,0)` −1.0e-4 m,
  `zbs(2,0)` +1.0e-4 m. The model predicted 9.45% joint descent; the smaller
  actual narrow gain shows its limits.
- **Phase C:** an exact 201-surface repeat and a 401-surface solve, then a separate
  final audit. In total 13 new cold solves, within the registered maximum of 13.

## Result: all ten final gates pass

Finest comparison: 401 radial surfaces, 3,201 toroidal points, 64 field lines,
two field periods.

| Gate | Observed | Limit |
| --- | --- | --- |
| New shape | Four named changes; complete 401-surface input saved | Different boundary, only permitted modes |
| Exact repeat | All 13 registered solver quantities identical | Separate real 201-surface cold start |
| Geometry | Volume −0.0074481%; largest rotational-transform change 0.000324754 | ≤ 1% and ≤ 0.02 |
| Fields and contours | 24 field grids and 280 contour cells pass; no missing cells | All registered domains and both contour resolutions |
| Second field-line tracer | Largest relative B difference 2.1354e-12; length 2.5332e-6; action 7.8889e-6 | B ≤ 1e-8; length and action ≤ 1e-3 |
| Refinement | All 20 comparisons pass; largest action difference 3.0222e-4 | ≤ 1e-3 |
| Local action limits | All 70 cells pass; largest mean-action change 1.01834% | ≤ 2% (and envelope limits) |
| Narrow training gain | 1.154624e-5 → 1.098618e-5: **4.85%** | ≥ 0.5% |
| Finest wide gain | 2.389427e-4 → 2.122527e-4: **11.17%** | ≥ 0.5% |
| Gain above numerical noise | Absolute gain 2.669e-5 = 47.4 × the uncertainty sum 5.634e-7 | > 5 × uncertainty sum |

The uncertainty sum is a predefined empirical screen, not a rigorous error bound.
A lower average does not mean every cell improved; the local limits bound that.

## What it does not show

Not 11.17% better particle confinement, fusion power or plant efficiency. The
checks assume VMEC's nested flux surfaces; global QI, maximum-J, finite particle
orbits, transport, finite plasma pressure, MHD stability, matching coils and
engineering remain open. The separate audit ran on the same machine; it is not
external review or a second MHD solver family.

## Failures kept on record

The first plasma design (`docs/qi/PLASMA_OPTIMIZATION_RESULTS.md` at that tag) improved
its training metric by 14.35% but made the wide metric 15.53% worse and violated
20 local action limits; it was rejected. Both attempts together used 32 cold solves.
The Step 3 evidence is preserved at commit `d429783`.

## Evidence

- [Final audit](../../evidence/plasma-balanced-v1/final-audit.json) (`step3_pass: true`)
  and [full diagnostics](../../evidence/plasma-balanced-v1/validation.json)
- [Accepted 401-surface input](../../evidence/plasma-balanced-v1/selected-input-401.json)
  and [reference input](../../evidence/plasma-design-v2/reference-input-401.json)
- Phase audits: [archive](../../evidence/plasma-balanced-v1/archive-audit.json),
  [proposals](../../evidence/plasma-balanced-v1/propose-audit.json),
  [endpoints](../../evidence/plasma-balanced-v1/endpoints.json)
- Commands for each phase: [detailed results at the freeze tag](../validation/REPRODUCING_RESULTS.md)
  (native research environment required).
