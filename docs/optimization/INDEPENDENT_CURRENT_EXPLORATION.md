# Fixed-geometry, independent-current exploration

27 September 2026. **Exploratory current-family diagnostic, not confirmation.**
[Programme](STEP4_RESEARCH_PROGRAMME.md) · [Static starts](COIL_START_SCREEN.md)

## Question and fixed inputs

Does releasing the six base-coil currents improve the field without changing
geometry? Previous Goodman searches use equal base currents with a shared scale.
Five relative-current directions are therefore untested for these shapes. The
older LPQA current study used another target and already independently optimized
currents; its small gain does not answer this question.

Use the **original** `n6-circle-d100mm` and `n6-shape-d100mm` starts from the
static-screen result, SHA-256
`6ef5c6c9824847e2eba6fbacc96c5abca3268032ff7760451f5b4d732132a89d`.
Do not substitute newly optimized shapes. Preserve all 198 named coefficients
and 24 physical-copy matrices exactly; their existing geometric bounds apply
only through that identity. Use the same reference surface, oriented target
loop flux −0.03141592653589793 Wb and fixed target B²=1.6293829620247962 T².
The positive equilibrium `phiedge` is not the oriented loop target.
This is exploration session 4 of the ten-session window.

## Method and interpretation

Build six coarse response columns Bⱼ, Aⱼ, each from 100 kA in one base group
and its four correctly signed symmetry copies. Let qⱼ=Iⱼ/(100 kA), area weights
sum to one, and n̂ be the unit boundary normal. Solve the convex problem

```
minimize  0.5 ||M q||²
subject to  φᵀq = target_flux,  -5 ≤ qⱼ ≤ 5
M[p,j] = sqrt(weight[p]) * (n̂[p] · Bⱼ[p]) / sqrt(target_B²)
φ[j] = mean(Aⱼ · loop_tangent)
```

This releases relative currents, including **base-current reversals**, within
the existing absolute 500 kA limit. Physical copy current remains
`(-1 if flip else +1) * I[base_index]`. Use a separate explicit-current record;
the old magnetic snapshot schema assumes a shared scale and cannot represent it.
Geometry is unchanged; forces, loads, winding supply complexity and power are
not established by a current fit.

Use SLSQP with analytic quadratic gradient/equality and at most 200 iterations.
Independently check primal feasibility, stationarity with equality/bound
multipliers, dual signs, complementarity and objective reconstruction. No silent
regularization, singular-value truncation or favorable solver-flag inference.
Report all five flux-nullspace singular values, rank/conditioning, active bounds
and flux cancellation. Ambiguous numerical certification remains unresolved.
Raw-flux improvement may worsen local-normalized RMS/max; report both.

Numerical tolerances: equality/box 1e-10; scaled stationarity 1e-8, dual signs
1e-10, complementarity 1e-9, supporting-plane objective gap divided by
`max(1, |objective|)` ≤1e-8;
active-bound identification 1e-8. SLSQP uses `ftol=1e-14`. If its point does not
certify, permit one nonsingular active-set linear KKT polish, fixing only its
identified bounds. Reject a singular system, changed active set or failed
recertification; retain both raw and polished points. No regularization or
singular-mode truncation. A synthetic near-optimum exposed the stricter gap test;
the tolerance stays unchanged. These are **numerical KKT/supporting-plane checks**
with finite primal tolerance, not an exact or interval-arithmetic optimum proof.

## Controls, checks and bounds

Fit at 64² boundary / 256 coil and loop nodes. Replay the exact equal-current
static control and one prechosen unequal mixture,
`q = static_scale * [0.8, 0.9, 1.0, 1.1, 1.2, 1.05]`, with plain native fields
and independent B/A samples. The unequal mixture tests linearity; it need not
match the target flux. Replay the fitted point independently as well. Keep full
basis arrays and current/loop identities.

Freeze each control's and proposal's **six currents** before fine evaluation:
128² boundary / 512 coil and loop nodes, unshifted and half-cell shifted.
Store full B/normals and loop A/tangents, all 6/24 currents and 64 independent
B/A comparison points per screen. No per-column normalization, post-fit common
rescaling, LPQA fixed-current sum or fitted-field normalization denominator.
Current/flux and field screens keep their original values: 500 kA, 1e-6 relative
flux, 1e-4 normal RMS and 1e-3 normal maximum. No interior/physical admission.

Two fits total; per shape, six basis evaluations, control/unequal/fit replays and
four fine screens. **180 s worker / 185 s external process-group cap**, serial
one-thread execution, 128-point field blocks, 64 MiB outputs, 3 GiB initial /
2 GiB live disk reserve. Bind all actual sources and retain failed prefixes.
Fresh output family: `artifacts/independent-currents-v1/`.

## Decision

If raw and normalized metrics improve with stable flux and acceptable current,
relative currents warrant a later combined shape/current study. Otherwise retain
the trade-off and favor another family/initialization. A convex optimum applies
only to these fixed geometry columns and the raw objective, not to stellarator
design globally. No Step 4 completion or Proxima advantage follows.

Implementation and independent review pass all twenty synthetic tests (0.44 s
main / 0.43 s reviewer). Slow/partial writes, late final publication and a late
basis save are rejected; failed diagnostic bytes remain. Scoped Ruff and
documentation checks pass.

## Completed raw-objective result

Both fixed-geometry fits numerically certify without polishing. The run completes
fourteen replay/fine rows in 4.794 s worker / 7.151 s supervised, using 18,049,370
bytes. It is a dirty, hash-bound exploration at `39a1e13`; sources remain unchanged.
The [evidence record](../../evidence/independent-currents-v1.json) binds all inputs,
basis arrays, currents, fields and the pre-run question. Result SHA-256:
`54ce6a3f405e7f3f87d747c46937c574cfd23e0414809e5f2da83021861c7bf6`.

| Fine unshifted metric | Circle control → fit | Shaped control → fit |
| --- | ---: | ---: |
| Raw normalized error | 0.0507979 → 0.00388669 | 0.0393446 → 0.00446327 |
| Local normal RMS | 0.308661 → 0.492879 | 0.276051 → 0.505851 |
| Area-mean field, T | 1.26231 → 0.26603 | 1.28277 → 0.26462 |
| Minimum sampled field, T | 1.06681 → 0.014835 | 1.03822 → 0.008117 |

Raw error falls **92.35% / 88.66%**, while normalized RMS **increases
59.68% / 83.25%**. The target-loop flux and current limit still pass. Fitted base
currents, in kA, are:

```
circle: [416.189819, -48.181633, 67.036090, -26.013749, -11.407529, -10.967496]
shaped: [364.359697,  17.460118, 35.044362,  -6.553229,  -7.719620,  -7.459855]
```

No bound is active. Both five-dimensional flux-nullspace systems have numerical
rank five, condition numbers 3.951 / 2.442. Scaled stationarity residuals are
1.347e-10 / 1.793e-10; supporting-plane gaps 1.276e-9 / 2.920e-9. These support
the scoped raw-objective numerical result, not the field's suitability.

The refined/shifted screens retain the negative conclusion: maximum normalized
normal errors reach 0.99995 / 0.99998, and minimum fields 0.014761 / 0.008104 T.
All fourteen rows fail both boundary-error limits. All twelve control/fit rows
pass flux/current screens; the two unequal probes intentionally miss target flux.
Geometries remain exactly the previously checked starts; no new engineering or
current-independent physical qualification follows.

**Interpretation:** the raw objective can reward a much weaker boundary field
despite the specified loop flux being preserved. It does not adequately select
for normalized field direction in this current family. This does not establish
that relative-current freedom itself is unhelpful; test the appropriate objective.

Independent saved-data audit checks 27 sources, all 54 run files / sixteen NPZs,
238 scalars, both field matrices/flux vectors/KKT checks, nullspace spectra,
current mappings and frozen fine values. Fourteen full loop integrals, six
coarse linearity pairs and **896 B plus 896 A** comparisons pass. Separate Fourier
reconstruction verifies all three grids and loop geometry to 1.95e-14; field
comparison errors remain below 6.14e-16 / 1.13e-16. Actual native requests:
B=1600, A=68, combined independent=14. The reviewer did not rerun native fields,
the full ancestral graph, physical diagnostics or resource-history measurements.

## Next question: local-normalized current fitting

Exploration session 5 reuses these exact saved six-column matrices and unchanged
geometries. Compare four arms: circle and shaped, each starting from its equal-
current control and its raw-QP fit. These starts are all strictly inside the
current box. Minimize `0.5 sum(weight * (n̂·B(q))² / |B(q)|²)` with an analytic
six-current gradient, the same flux equality and ±500 kA limits. No regularization,
extra field-strength constraint, post-fit rescaling or silent threshold change.
This objective is nonconvex; no global-optimality certificate is implied.

Before each search: two sine/cosine directions projected into the flux nullspace,
central differences at 1e-5 / 5e-6 in q units (absolute ≤1e-7 or relative ≤1e-4),
and exact repetition. Require probes inside the current box; exclude them from
selection. A zero sampled field is invalid, not clipped into a favorable score.
Permit **400 total objective/gradient bundles per arm**, including ten startup
bundles, and at most 200 SLSQP iterations. Retain every attempt, actual metrics,
failed points and the lowest-RMS feasible seed/search point. Reject late results.

Freeze the selected six currents before two native fine checks per arm at
128² / 512 nodes, unshifted and half-shifted. Reuse original control fine rows;
save new full B/normals, loop A/tangents and independent B/A comparisons. These
adaptive checks are not confirmation holdouts. Bounds: **240 s worker / 245 s
external**, 64 MiB output, one thread, same 3/2 GiB reserves; fresh outputs under
`artifacts/local-currents-v1/`. No new field responses during optimization and
no shape, topology, pressure or interior-vector change/qualification.
