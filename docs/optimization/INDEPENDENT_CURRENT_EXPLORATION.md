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

Implementation is being prepared; no new fit has run.
