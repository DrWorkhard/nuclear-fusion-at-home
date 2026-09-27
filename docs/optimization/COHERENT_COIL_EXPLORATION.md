# Coherent coil fitting: current result

27 September 2026. Exploratory, independently checked numerically; **not physical
acceptance**. [Programme](STEP4_RESEARCH_PROGRAMME.md) · [Evidence](../../evidence/coherent-restart-v1.json)

## Matched comparison

Both restarts begin at the same geometry-checked coherent trial 598, with reset
L-BFGS history. The original absolute bounds remain centered on shape52:
low modes 0–2 ±0.08 m versus ±0.12 m; high modes 3–5 ±0.02 m in both.
Six order-5 base coils, 24 physical coils and all 198 named coefficients remain
active. Both arms get 1,200 bundles, including ten startup checks.

The objective is area-weighted local-normalized field error plus unchanged
construction penalties. Fresh coarse flux normalization fixes the signed
−π/100 Wb loop target. Fine checks freeze that current: 128² boundary points,
512 coil nodes, unshifted and half-cell shifted. Endpoints are selected before
fine checking; interior results play no role.

| Endpoint | Selected trial | Fine normal RMS | Base current | Geometry |
| --- | ---: | ---: | ---: | --- |
| Original absolute box | 1197 | 0.01092842152 | 345.245 kA | Scoped pass |
| Expanded low modes | 1198 | **0.00488873136** | **315.407 kA** | Scoped pass |

Expanded RMS is **55.27% lower**, with **8.64% less current**. Both budgets are
exhausted; neither is an optimum. Expanded geometry bounds: length ≤3.28691 m,
curvature ≤10.0353/m, coil clearance ≥0.0628479 m, plasma clearance ≥0.132237 m.

The **1e-2 exploration signal is met**, but RMS remains 48.89 times the 1e-4
acceptance limit; maximum normal error also fails. The subsequent
[interior screen](INTERIOR_FIELD_EXPLORATION.md) reaches 0.04029 versus 0.01.
No realized-surface, benefit-transfer, pressure or engineering acceptance is established.

## Checks and reproducibility

Clean source revision `c1fdddf`; search 478.475 s, supervised 479.247 s.
Geometry takes 4.539 s without native fields. Both source graphs stay unchanged.
Independent saved-data checking covers 46 search/seven geometry sources, all
2,400 trial pairs, masked startup directions, eight derivatives, repeats,
bounds/selections, 48 fine metrics, four loop integrals and 256 B/256 A comparisons.
Geometry checks compose 552 pair/48 plasma lower bounds and twelve tighter-curvature
classifications; they do not rerun distance searches or enclosures. Bounds use
padded floating point, not directed interval arithmetic or complete self-disjointness.

The linked evidence binds all 4,827 run files, exact pre-run question and receipts.
[Predecessor evidence](../../evidence/coherent-coils-exploration-v2.json) retains
the equal-budget 600-bundle comparison: RMS 0.07606 versus 0.01384.
Its initial startup failure remains failed; a component sweep diagnosed
curvature-penalty branch crossings before smaller probes passed unchanged tolerances.
[Diagnostic evidence](../../evidence/coherent-derivative-scale-v1.json).

Detailed earlier protocols, negative results and original scripts remain at the
[freeze tag](../validation/REPRODUCING_RESULTS.md). The shared evaluator is unchanged.
Next: a wall-clock-bounded trade-off map using the working fit and shared checks.
