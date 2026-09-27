# Constraint-aware coil fitting

27 September 2026. **Exploration; not independent confirmation.**
[Programme](STEP4_RESEARCH_PROGRAMME.md) · [Static starts](COIL_START_SCREEN.md)

## Question

Can stronger geometry penalties or fewer free Fourier modes turn the observed
field-error reduction into a geometrically usable candidate? The
[first objective comparison](NORMALIZED_OBJECTIVE_EXPLORATION.md) lowered RMS
only by violating curvature (and, for the raw objective, plasma clearance).
The static screen found no better initial field, but circular coils have more
curvature margin. Compare these construction choices before widening the family.
This is exploration session 3 of the programme's ten-session window.

## Inputs and prospective matrix

Use only the unchanged `n6-circle-d100mm` and `n6-shape-d100mm` snapshots and the
reference target identified in the static-screen record. Bind that completed
screen by SHA-256; derive each start's magnetic metadata from its own measured
loop flux and fresh normalization. Do not transfer the shaped coil's current
scale to the circle. Both start with six order-5 base curves, 24 physical coils,
two field periods and stellarator symmetry.

Run four arms, circle then shaped, full then low-order:

- **Full:** all 198 named coefficients free.
- **Low-order:** only constant and sine/cosine modes 1–2 free (90 coefficients);
  all higher coefficients remain exactly those of that start, not zeroed.

All arms minimize half the area-weighted squared local-normalized error, plus
the same construction penalties: length above 3.5 m, coil separation below
0.07 m and plasma clearance below 0.09 m (distance weights 1000), and integrated
quadratic excess curvature above 10/m (weight 0.01, 100 times the previous arm).
The distance margins and penalty weights guide construction; they do **not**
change admission: length ≤3.5 m, curvature ≤12/m, coil separation ≥0.06 m,
plasma clearance ≥0.08 m, current ≤500 kA, RMS ≤1e-4, maximum normal error ≤1e-3,
and relative target-flux error ≤1e-6. Interior/other requirements remain open.

Each active coefficient stays within ±0.02 m of its own start. This is a
coefficient bound, not a bound on pointwise motion. Use the existing named
derivative mapping, sparse distance evaluator and native optimizer. Current
scaling cancels from this local objective; fresh loop-A evaluations still determine
physical currents. Do not modify the previous experiment or its evaluator.

## Execution and checking

Coarse grids: 64² boundary, 256 coil/loop nodes; 128² full-torus surface for
distance penalties. Each arm permits **240 total value/gradient bundles**,
including ten startup bundles, and **300 s startup/search**. Startup requires
matching that case's static seed metrics, sine/cosine directional checks in its
active coordinates at 1e-5 and 5e-6 m (absolute error ≤1e-7 or relative ≤1e-4),
and an exact value/gradient repeat. Failure stops that arm before search.

Persist all trial coordinates, metrics, gradients and attempted/completed counts.
Report the lowest objective and, separately, the lowest RMS among actual seed/
search points meeting sampled geometry and current limits. Probes are ineligible.
Reject late results; the solver's success flag does not imply physical acceptance.

Freeze the best sampled-feasible point per arm (or its seed if no improvement).
Screen it at 128² boundary / 512 coil/loop nodes, unshifted and half-cell shifted,
with its **coarse current fixed**. Save full B/normals and loop A/tangents, plus
independent field comparisons. Fine sampling is adaptive exploration, not an
unseen confirmation set. A passing sample is not a continuous geometry certificate;
any promising point needs a separate continuous check before such a claim.

Use one native thread, 128-point field blocks, a **1,800 s worker / 1,805 s
external process-group cap**, 256 MiB outputs and 3 GiB initial / 2 GiB live disk
reserve. Fresh outputs under `artifacts/constrained-coils-v1/`; retain failures
and bind actual sources before/after. No equilibrium, pressure, topology,
interior-vector, finite-build or load computation in this experiment.

## Decision

Compare both field/current trade-offs and geometry, not just objective values.
Compare full/low-order and circle/shaped arms within this matrix; a difference
from the earlier experiment cannot be attributed to penalties alone because
coefficient bounds and evaluation budgets also changed.
Fine RMS below 1e-2 with geometric gates remains a triage signal, not acceptance.
If geometry improves but field quality stays far from that signal, consider a
different initialization/family or parameter freedoms; do not declare an optimum
or target impossibility from this small search. Independent confirmation and
Step 4A–4D remain separate requirements.

Implementation and independent method review pass. Fourteen focused synthetic
tests pass independently; the combined new/reused experiment suite passes all
53 tests (13.27 s), including the native-circle cache regression. Scoped Ruff,
documentation and whitespace checks pass.

## Follow-up geometry question

All four selected endpoints now pass the fine **sampled** geometry/current/flux
screens; the source-bound result is being independently audited. Before calling
any of them geometry-certified, check the frozen selected snapshots without
further optimization. This follow-up uses existing independent modules, not a
new acceptance profile or confirmation study.

For each eligible endpoint, run length/clearance bounds at 1,024 coil nodes and
a 512² full-torus surface; if unresolved, use 2,048 nodes and a 1,024² surface.
Supplement the original conservative curvature bound with the existing tighter
enclosure at resolutions 1,024 and 4,096 respectively. Keep the original bound
and report the supplemental conjunction explicitly. All four original geometric
limits remain unchanged. An upper/lower bound crossing its limit is unresolved;
only an actual curvature/distance witness establishes that type of failure.
Sampled mean speed is not an exact length-failure witness.

The native-free follow-up permits 300 s total / 305 s external process-group
time, 8 MiB outputs, and the same disk reserves. Preserve exact snapshot/current
identities and all attempts. These are padded floating-point bounds, not
directed interval arithmetic or a complete self-disjointness proof. Outputs:
`artifacts/constrained-coils-v1/geometry/`.

The first follow-up stopped after 2.361 s when its JSON writer encountered a
NumPy Boolean in the existing helper's self-nearness record. No geometric result
was saved or accepted. The original runner and failed prefix remain intact.
The retry writes to `geometry-v2/` and converts only NumPy scalars through
`.item()`; unsupported objects still fail. Its focused serializer check passes.
Numeric calculations, sources, grids, thresholds and execution limits are unchanged.

## Results

The search completes **744 bundles and eight fine screens** in 148.426 s
(149.177 s supervised), retaining 29,713,557 run bytes. The full-mode arms hit
240-bundle caps; low-order arms return the solver's local convergence condition
after 53/211 bundles. This is neither a global optimum nor a general method
ranking. Execution used a dirty but hash-bound tree at `b54eda4`; sources stayed
unchanged. The [evidence manifest](../../evidence/constrained-coils-exploration-v1.json)
binds all trials, fields, pre-run questions and the failed geometry prefix.
Search result SHA-256:
`3d5121165aa081f8c8589c9061295d79ec198fdf1cb64272781065654b394d7d`.

| Arm | Selected trial | Fine RMS | Worst fine sampled maximum | Current, kA | Continuous geometry |
| --- | ---: | ---: | ---: | ---: | --- |
| Circle / full | 238 | 0.189118900 | 0.511479727 | 340.054 | Clearance unresolved |
| Circle / low2 | 52 | 0.223503322 | 0.526188144 | 327.970 | Scoped pass |
| Shape / full | 217 | 0.137310287 | 0.506681654 | 365.639 | Clearance unresolved |
| Shape / low2 | 134 | 0.180418186 | 0.549948032 | 338.531 | Clearance unresolved |

All four meet fine sampled geometry/current/flux limits but fail both boundary
error gates. The lowest objective trials are 239, 52, 238 and 210: only one is
also the selected sampled-feasible RMS minimum. This separation matters.

The circle/low2 endpoint reduces RMS **27.59%** against its own circular seed at
**13.91% higher current**. Its second-grid continuous bounds give length ≤2.19165 m,
curvature ≤6.13704/m (supplemental tighter bound 6.00757/m), coil separation
≥119.02 mm and plasma clearance ≥84.14 mm. This is an improved boundary fit with
scoped continuous geometry, **not** complete physical acceptance. RMS is still
about 2,235 times the limit and 22 times the exploration triage signal.

Shape/full lowers RMS 50.26% against its own seed, but its clearance bound is
unresolved. The three other final clearance lower bounds are 74.90, 72.04 and
73.94 mm against 80 mm; these conservative bounds do **not** prove a violation.
Their tighter curvature bounds pass; the original broad curvature bounds do not.
The geometry retry completes all eight planned levels in 44.329 s (44.711 s
supervised), with no native field calls. New coefficients inherit no old certificate.

## Independent checks and next question

A separate audit rehashes 30 search sources and the saved prospective question,
checks all 744 trial pairs, masks/boxes, counts, case-specific anchors and all
16 derivative checks (largest discrepancy 2.351e-11). Separate formulas reproduce
96 fine metrics and eight full saved-loop-A integrals. All 512 B and 512 A
comparison points pass (maximum errors 9.501e-16 / 1.388e-16); standalone Fourier
derivatives reproduce physical curves and all 24 selected base curvature/length
sample calculations. These are same-machine numerical checks, not external review.

The geometry audit separately rehashes seven evaluator/source identities and
four selected snapshots, and checks all eight saved levels. Standalone formulas
reproduce derivative suprema, speed/length/global-curvature bounds, the surface
cover, all **2,208 coil-pair and 192 plasma lower-bound calculations**, and all
48 tighter curvature enclosures. It confirms one scoped pass and three unresolved
clearances. It does not rerun the full distance-grid searches or prove complete
self-disjointness; those limits remain explicit.

Next test [independent base currents](INDEPENDENT_CURRENT_EXPLORATION.md) on the
two original geometries. This isolates a previously frozen design freedom before
another shape/current search. No interior-field, topology, plasma-benefit transfer,
pressure or finite-build claim is made; Step 4A–4D remain open.

## Adaptive saved-point follow-up

Inspecting the saved trials with plasma-clearance filters 85/90/92/95 mm revealed
two lower-error points with more margin: circle/full trial 126 and shape/full
trial 52. Freeze these exact points and their seeds before finer checking.
Their coarse RMS values are 0.1906723 / 0.1516789, plasma gaps 90.601 / 90.939 mm,
coil gaps above 70 mm and sampled curvature below 11.5/m. These extra selection
margins do not change the original acceptance gates.

This is **adaptive postselection after inspecting results**, not preregistered
confirmation or a new search. Preserve the complete inspected filter table,
exact trial/seed hashes and the original four-arm selections/verdicts. Replay
only these two points at both existing fine grids with frozen coarse current;
then apply the same continuous-geometry schedule. No replacement point is chosen
after seeing its outcome. Use 180 s / 185 s external field limits, 64 MiB outputs;
geometry retains 300 s / 305 s and 8 MiB. Same one-thread and disk rules. Fresh
outputs: `artifacts/constrained-coils-slack-v1/`. No new optimizer evaluations.

### Follow-up result

Both frozen points complete four fine screens in 6.022 s (6.386 s supervised)
and four geometry levels in 24.086 s (24.338 s supervised). Sources stay unchanged
in the dirty, hash-bound execution at `e0f45e1`. The
[adaptive evidence record](../../evidence/constrained-coils-slack-v1.json) links
the original immutable study and preserves the sixteen inspected filter rows.

**Shape/full trial 52 passes the scoped continuous bounds**: length ≤2.081313 m,
tighter curvature ≤11.065107/m, coil separation ≥147.712 mm and plasma clearance
≥80.714 mm. Fine normal RMS is **0.151678906**, maximum across fine grids 0.515305,
and current 324.792 kA. Relative to the unchanged shaped seed, RMS falls **45.05%**
at **10.11% higher current**. This passes a supplemental geometry conjunction,
not the older loose curvature-bound flag; original limits are unchanged.
It is now the lowest checked RMS with scoped continuous geometry in this study,
but still about **1,517 times the field limit** and 15 times the triage signal.

Circle/full trial 126 has fine RMS 0.190672518 and current 338.982 kA. Its plasma
lower bound is 79.826 mm: unresolved, not a demonstrated violation. No extra
point or finer grid was substituted after that result. The earlier four-arm
selections, the circle/low2 pass and all unresolved results remain unchanged.

The independent follow-up audit rehashes all **1,573 original manifest files**
and reconstructs all sixteen filter choices from the 744 original hashed trials.
It verifies the two frozen trials/seeds, 36 replay / seven geometry source
identities, four array hashes, 48 fine metrics and four complete saved-loop
integrals. All 256 B / 256 A samples pass. Four geometry levels, 1,104 coil-pair /
96 plasma lower-bound calculations and 24 tighter curvature enclosures reproduce
with separate arithmetic. This confirms the supplemental scoped pass and the
other unresolved verdict; it is not a full distance-grid rerun or external review.
