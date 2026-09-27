# Matched low-frequency shape freedom

27 September 2026. Session 6 complete; **wider shapes improve the fit**.
Session 7 is a prospective matched restart, not a completed result.
[Programme](STEP4_RESEARCH_PROGRAMME.md) · [Starting geometry](CONSTRAINED_COIL_EXPLORATION.md)

## Result and limits

The diagnosed retry at clean `c1d2260` completes both 600-bundle arms in
233.572 s worker / 234.478 s supervised. All startup checks pass, the source
graph is unchanged, and both searches stop at their fixed budget, not at a
demonstrated optimum. The [result evidence](../../evidence/coherent-coils-exploration-v2.json)
binds 2,427 run files / 36,177,183 bytes and result SHA-256
`328ccd9727e406a72b50016aa03d93f4ac4b0e57f7f57a11686050d7c088cf2b`.

| Same shape52 start and budget | Control | Wider low modes |
| --- | ---: | ---: |
| Frozen selected trial | 599 | 598 |
| Fine normal RMS, unshifted | 0.0760607170 | **0.0138430479** |
| Fine normal RMS, half-cell shifted | 0.0760607171 | 0.0138430479 |
| Worst sampled maximum normal error | 0.41178849 | 0.08238964 |
| Current per base coil | 345.713 kA | 349.383 kA |
| Minimum sampled boundary field | 1.15021 T | 1.20476 T |
| Continuous geometry verdict | Unresolved clearance | **Scoped pass** |

The wider arm lowers RMS **81.80% versus its matched control**, with 1.06% more
current, or **90.87% versus shape52**, with 7.57% more current. Compared with the
original shaped initialization, RMS is 94.99% lower. These comparisons describe
this pair, not a universal optimizer ranking. Trial 599 has the wider arm's
lowest penalized objective, but 598 has its lowest sampled-feasible RMS; the
predeclared selection is preserved.

The separate geometry run completes in 15.557 s / 15.844 s supervised with no
native fields. Wider-arm first-level bounds: maximum length 2.82955 m, maximum
curvature 10.1262/m, coil clearance at least 0.0639913 m and plasma clearance at
least 0.112898 m. Control remains unresolved after the second level: plasma
clearance lower bound 0.0757012 m is below 0.08 m, without a violation witness.
No directed interval proof or full self-disjointness check is implied.

Independent saved-data review verifies all 45 search sources, 1,200 trial/attempt
pairs, eight startup derivative checks, anchors/repeats, boxes, budgets and
selections. Separate formulas reproduce 48 fine metrics and four full saved-loop
fluxes; 256 B and 256 A comparisons and all 24 physical Fourier curves at each
endpoint agree. These are saved-data checks, not a second native search.
The geometry audit separately reproduces all three levels' cover/bound arithmetic,
828 coil-pair bounds, 72 plasma bounds and eighteen tighter curvature enclosures.
It does not rerun the full distance grids. The original loose curvature flag is
unchanged; the explicit supplemental curvature conjunction supplies the scoped pass.

**Still not accepted:** the wider RMS is 138.43 times the 1e-4 limit and 1.3843
times the exploratory 1e-2 signal; its maximum error also fails. Interior-field,
topology, benefit transfer, finite-pressure and engineering requirements remain
open. The accepted public reference is unchanged. The first failed attempt and
its diagnosis below remain part of the study's evidence and effort accounting.

## Question and rationale

Does freeing larger, coherent coil displacements improve the geometry/field
trade-off? Independent saved-trial inspection finds that the previous small
coefficient box obstructs descent:

| Saved full-mode point | Coefficients at ±0.02 m | Outward descent directions | Saturated coefficients in modes 0–2 |
| --- | ---: | ---: | ---: |
| Shape, selected 217 | 60 / 198 | 59 | 46 |
| Shape, geometry-checked 52 | 28 / 198 | 25 | 24 |
| Circle, selected 238 | 131 / 198 | 131 | 81 |

“Outward” means displacement times the penalized-objective gradient is negative
at a bound. Both full searches also exhausted their 240-bundle budgets. These
are reasons to test wider motion, not evidence of an optimum or of reachability.
Current-only normalized fits help modestly but do not close the gap; see the
[current study](INDEPENDENT_CURRENT_EXPLORATION.md).

An independent reviewer considered the existing eight-base-coil/order-7 starts.
They offer another valid family, but the modern exploratory shape implementation
explicitly maps six order-5 curves. Test the observed box restriction first;
do not silently reinterpret those mappings as eight-coil data.

## Fixed paired experiment

Both arms start from exactly the same geometry-checked **shape/full trial 52**,
snapshot SHA-256
`2492d83ad3392069be5bfe8ae35b2e98ca0419916517e96065e017bcf15417e9`.
Bind its original trial, seed and adaptive replay; replay its original **coarse**
metrics at startup, not the slightly different fine values. Same Goodman target,
oriented flux −0.03141592653589793 Wb, six equal base currents with fresh shared
normalization, 24 physical coils and explicit 198 named coefficients.

- **Control:** every coefficient within ±0.02 m of shape52.
- **Coherent-wide:** constants and modes 1–2 within ±0.08 m; modes 3–5 remain
  within ±0.02 m. Exactly ninety coordinates receive the wider bounds.

All coordinates remain active. These are **coefficient bounds, not pointwise
displacement bounds**. Recentered boxes define a new study; no earlier geometric
path certificate applies. The two new arms have the same budget: **600 total
value/gradient bundles including ten startup bundles**, at most 590 optimizer
iterations/function evaluations in L-BFGS-B, with the existing startup finite
differences and exact repeat. The total-bundle cap is authoritative. This is an
equal-budget pair, not a controlled comparison against the older 240-bundle run.

Reuse the local-normalized objective and construction penalties unchanged:
length above 3.5 m; curvature above 10/m with weight 0.01; coil/plasma distances
below 0.07/0.09 m with weight 1000. Original physical gates remain length 3.5 m,
curvature 12/m, distances 0.06/0.08 m, current 500 kA, normal RMS 1e-4 and maximum
1e-3. Penalties guide construction; they are not certificates.

Record every attempted point, lowest objective and lowest sampled-feasible RMS;
exclude derivative probes from selection. Freeze one lowest sampled-feasible
seed/search point per arm before fine checks. No endpoint substitution after
seeing a fine or continuous-geometry outcome. If the search fails, retain the
prefix and report it, rather than silently restarting.

Search at 64² boundary / 256 coil nodes. Check each selected point at 128² / 512,
unshifted and half-cell shifted, with its **coarse current frozen**. Save full B,
normals, loop A/tangents and independent B/A samples, plus boundary-field strength.
Any selected geometry needs a separate continuous check; the seed's certificate
cannot be inherited after a shape change. Fine screens consulted in exploration
are not confirmation holdouts. No new interior, topology or confinement claim.

For endpoints passing the sampled geometry/current/flux screens, reuse the
continuous schedule: 1024 coil nodes / 512² surface, then 2048 / 1024² if
unresolved; supplemental curvature enclosures at 1024 / 4096 nodes. Stop on a
scoped pass or explicit violation witness. A conservative lower bound below a
clearance limit remains unresolved, not a failure witness. Separate geometry
budget: 300 s / 305 s external, 8 MiB, same disk/thread rules. No new fields,
directed interval proof or complete self-disjointness is implied.

Execution: 300 s per arm, 900 s total / 905 s external process-group cap, one
thread, 256 MiB aggregate output, 3 GiB initial / 2 GiB live reserve. Fresh family
`artifacts/coherent-coils-v1/`; old scripts/artifacts remain unchanged. A thin
wrapper records its explicit runtime bounds/budget overrides and restores them
after use. Check final publication after writing so late results cannot pass.

Implementation checks: 58 combined coherent/constrained/objective tests pass
(14.23 s), including the interacting native-circle cache regression. Independent
review reruns thirty coherent/constrained synthetic tests (0.88 s), verifies all
thirteen pinned inputs and the ninety named widened coordinates, and checks the
late-publication/storage controls. This is readiness for execution, not a result.

## Decision

Compare the two new arms' fine RMS, currents, maxima and geometric status; a
single pair cannot establish a universal method ranking. If wider low modes help,
retain the shape/current/clearance trade-off and check continuous geometry. If
both remain far from the 1e-2 triage signal, prioritize a distinct family such as
the existing n8 starts instead of repeatedly widening this one. Neither the
triage signal nor experiment completion replaces Step 4 acceptance.

## First attempt: startup derivative failure

At clean `e8eeaf9`, both arms stop after their ten startup bundles; no optimizer
or fine screen runs. Worker time 7.080 s / supervised 7.660 s; 53 run files use
1,245,748 bytes. All sources remain unchanged. The
[failed-attempt evidence](../../evidence/coherent-coils-failed-v1.json) preserves
the exact original question, code, coefficients, gradients and failure verdict.
Result SHA-256:
`b371d45a07c5ed197b2c9fd56112d66474448036c29f29b4232a31dafeb813a2`.

All nine startup anchors replay exactly, as do repeated values/gradients and both
arms. Three of four directional checks fail the original absolute 1e-7 or
relative 1e-4 criterion:

| Direction | Absolute error at h=1e-5 | At h=5e-6 | Error reduction |
| --- | ---: | ---: | ---: |
| Sine | 5.25910e-6 | 1.31111e-6 | 4.0112× |
| Cosine | 5.62513e-6 | 1.44166e-6 | 3.9018× |

Independent saved-data inspection checks all 39 sources and twenty startup rows.
Only the curvature construction penalty is active. Splitting saved scalar values
into field/geometry terms attributes essentially all step-size dependence to the
geometry penalty: the field derivative changes only about 4–7e-12 on halving h.
Two-level Richardson extrapolation of saved values differs from the analytic
derivatives by 4.893e-9 / 4.717e-8. This supports finite-step truncation as an
explanation, but does **not** turn the failed startup into a pass.

### Bounded derivative-scale diagnosis before any retry

Keep this failed run and its script unchanged. A separate diagnostic reuses its
exact shape52 seed, control box and nine coarse anchors. No optimizer or new
candidate is permitted. Use thirty total bundles: seed, central probes in the
same normalized sine/cosine directions at h=2e-5, 1e-5, 5e-6, 2.5e-6, 1.25e-6,
6.25e-7 and 3.125e-7, then an exact seed repeat. Retain all attempts and independently
report field, geometry and total directional derivatives, raw errors and
convergence ratios. The acceptance tolerances remain unchanged; undefined or
inconsistent results remain failures.

Save the geometry gradient separately; subtract it from the total gradient for
the field component and compare both with their scalar central differences.
This is a same-model derivative diagnostic, not an independent physics code.
Require stable repeat/anchors and consistent finer-step behavior before defining
any fresh search startup rule. A retry must have a new output/source identity and
retain the initial failure, rather than silently changing its probes.

Diagnostic bounds: 180 s / 185 s external, 64 MiB, one thread, same 3/2 GiB disk
reserves; fresh `artifacts/coherent-derivative-scale-v1/`. No new geometry,
confinement, field acceptance or Step 4 completion follows from a derivative check.

Diagnostic implementation: 44 combined diagnostic/coherent/constrained tests
pass (1.21 s main), including component arithmetic, exact accounting/repeat,
late rejection and overflow controls. Preflight review found that an infinite
finite difference could satisfy an unguarded relative `inf <= inf` comparison;
the new diagnostic now rejects all nonfinite derived comparisons explicitly.
No real diagnostic was run before that correction; tolerances remain unchanged.

### Derivative-scale result and fresh retry rule

The diagnostic completes at clean `cd376b5`: thirty bundles in 9.151 s worker /
9.510 s supervised, 64 run files / 1,213,143 bytes, unchanged sources and exact
full-component seed repetition. The [diagnostic evidence](../../evidence/coherent-derivative-scale-v1.json)
binds result SHA-256
`fc0f32fed25f72451a71d8293252303430fc7e93f62c177f7ef7a80b5fedfb99`.

Every magnetic-component check passes. All three components in both directions
pass the original tolerances at the **four tested steps h≤2.5e-6**.
At h=1.25e-6 and 6.25e-7 the maximum
total discrepancy is 8.04e-11; no tolerance has been relaxed. Geometry errors
fall much faster than a simple h² law near 2.5e-6, so the full sweep, not just the
first pair's approximate fourfold ratio, is needed to interpret the behavior.
Native requests: 120 B, thirty A, thirty B-vjp, plus thirty explicit extra
geometry-gradient extractions. No optimizer, fine field or new design is involved.

Separate Fourier reconstruction of first/second curve derivatives for all thirty
saved points reproduces all 180 per-coil curvature maxima to 2.31e-14. It locates
the sampled penalty switches: larger positive probes cross κ=10/m at base coil 0,
node 69/256, and sometimes node 220/256. Negative probes and all tested steps
≤1.25e-6 preserve the seed's active set. The nearest seed curvature is 1.67e-4/m
from the switch. Thus the larger probes straddle a construction-penalty branch;
the selected smaller probes stay on the same branches. This is the **soft penalty
threshold 10/m**, not a violation or change of the physical curvature limit 12/m.
The reconstruction uses `|γ′×γ″| / |γ′|³` at the original 256 equally spaced nodes,
not new native fields or a continuous-geometry certificate.

Independent saved-data review verifies all 42 source hashes, reproduces all
42 component finite-difference/error/tolerance classifications and exact seed
repetition, and separately reconstructs all thirty coil sets. Its 180 curvature
maxima agree within 9.24e-14 and confirm the same branch crossings. This is a
saved-data/geometry arithmetic audit, not a new native field calculation.
An additional independent analytic reconstruction checks all 46,080 sampled
curvatures, thirty geometry penalties and 5,940 geometry-gradient components,
with maximum discrepancies 4.09e-14, 1.32e-18 and 3.43e-15 respectively.
The squared-hinge penalty is continuously differentiable, but not twice
differentiable at its switch; the branch transition explains the non-h² behavior.

**Fresh retry:** change only the paired search's two startup probe sizes to
**1.25e-6 and 6.25e-7**. Retain the same ten startup / 600 total bundles, paired
boxes, objective, penalties, actual acceptance limits, selected-endpoint rule and
fine/geometry schedules. Use a separately identified script and fresh
`artifacts/coherent-coils-v2/` outputs; bind this diagnostic and the failed first
attempt. Both new arms must independently pass their startup again. This is an
explicitly diagnosed numerical-probe revision, not a relabeling of the failed
attempt or proof of physical acceptance.

The retry's 46 combined retry/coherent/constrained tests pass (1.71 s main).
Sixteen new tests verify syntax-tree equivalence of the copied search after
normalizing only the documented probe tuple, module references and metadata;
they also test the exact 10/600 accounting, selection, source rejection and
override restoration. All nineteen fixed input hashes and the real saved-data
preflight pass without fields. Old sources and outputs remain unchanged.

## Session 7: extra iterations versus additional low-mode freedom

This follow-up is declared after inspecting session 6. Its wider arm's incumbent
RMS falls another 8.36% in its last hundred bundles, versus 0.95% for control.
At its lowest-objective trial 599, eleven low-mode and fourteen high-mode
coordinates still have outward gradients at their bounds, while the projected
gradient maximum is about 4.01e-4 versus solver tolerance 1e-9. A coil-family
floor is therefore not established. An independent saved-data reviewer favors
a matched restart before changing coil count or increasing high-mode freedom.

Both arms start at the **same geometry-checked coherent trial 598**, not the
lower-total-objective trial 599. Reset L-BFGS history in both; the old solver
state was not saved. Bind the completed search, exact selected snapshot/trial,
geometry report and their source graph. Replay the nine coarse seed anchors,
not fine metrics or shape52's older field.

- **Control:** keep the original absolute box centered on shape52: low modes
  0–2 ±0.08 m, high modes 3–5 ±0.02 m.
- **Expanded:** same original center and high-mode bounds; low modes ±0.12 m.

Do **not** recenter either box around trial 598. All 198 coordinates remain
active. Shape52 is only the bound center; trial 598 is the actual magnetic start.
Because that start is on 28 control bounds, central probes use shared feasible
directions: begin with sine/cosine of coordinates 1–198, zero coordinates whose
distance to either control bound is ≤2×1.25e-6 m, then normalize. Require at least
two remaining coordinates, retain the explicit mask/vectors, and reject a
nonfinite or out-of-box probe. Do not clip or inset the start. Use h=1.25e-6 and
6.25e-7, unchanged absolute 1e-7 OR relative 1e-4 derivative tolerances, exact seed
repeat and ten startup bundles. These checks cover the recorded feasible
directions, not every derivative coordinate. Either failed startup stays failed.

Each arm receives **1,200 total bundles including startup**, maxiter/maxfun 1,190,
maxls 20, ftol 1e-12 and gtol 1e-9. Keep the same local-normalized objective,
strong construction penalties, current normalization and physical limits.
Select the lowest sampled-feasible RMS before checking it, excluding probes;
keep every attempted point and do not replace an endpoint after its fine result.
Coarse 64²/256 and frozen-current fine 128²/512 at both shifts remain unchanged,
with independent B/A and full saved-loop data. Reuse the same separately bounded
continuous-geometry schedule above for eligible frozen endpoints.

New output family `artifacts/coherent-restart-v1/`: 450 s per arm, 1,200 s total /
1,205 s external, one thread, 256 MiB and 3/2 GiB disk reserves. Reuse the reviewed
model, fine checker and recorder; source changes are limited to explicit bounds,
seed/probe handling and this paired orchestration. Prior source files/results
remain unchanged. This is exploration session 7, within the ten-session ceiling.

Compare both new endpoints and currents with their shared start. A same-box gain
shows residual optimization opportunity; an expanded-box gain over that control
supports additional low-mode freedom in this pair. A result below 1e-2 with
checked geometry triggers a matched comparison and interior/topology screening,
not acceptance or Step 4 completion. If no such signal appears by the programme's
ceiling, switch the investigated family/approach instead of automatic continuation.

Implementation/preflight: 63 combined restart/retry/coherent/constrained synthetic
tests pass (2.08 s main); an independent reviewer reruns 47 restart/coherent/
constrained tests (1.37 s). All twenty pinned inputs and nine actual saved seed
anchors pass. The actual shared mask retains 169 coordinates and masks 29
(28 exactly on bounds plus one near a bound); all eight central probes fit both
absolute boxes. No new fields are used by these preflight checks.
