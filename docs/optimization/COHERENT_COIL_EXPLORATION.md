# Matched low-frequency shape freedom

27 September 2026. Exploration session 6; **first attempt fails before search**.
[Programme](STEP4_RESEARCH_PROGRAMME.md) · [Starting geometry](CONSTRAINED_COIL_EXPLORATION.md)

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
