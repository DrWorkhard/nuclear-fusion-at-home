# Prospective local curvature bounds

26 September 2026. Read-only internal proposal by `protected_runner_map`,
independently of the saved-value check. [Coarse evidence](../optimization/PROTECTED_COIL_FIT_RESULTS.md) · [Index](README.md)

Planning only: no new calculation,
implementation, registration or changed acceptance decision.

The current cumulative certificate uses global original-seed/perturbation bounds:

`K <= k0*(v0/(v0-D1))^3 + (D1*A0 + V0*D2 + D1*D2)/(v0-D1)^3`.

Worst cases can occur at different curve parameters, making this conservative.
The observed coarse sampled curvatures below 12/m do not prove a continuous pass.

For a fixed candidate c(t), set v=c', a=c'', j=c'''. On an interval centered at
t0 with halfwidth h, let A bound sup||a|| and J bound sup||j||. Then

`Vminus = ||v(t0)|| - h*A`, `Vplus = ||v(t0)|| + h*A`.

Since `(v cross a)' = v cross j`,

`Nplus = ||v(t0) cross a(t0)|| + h*Vplus*J`.

If Vminus>0, `sup kappa <= Nplus/Vminus^3`. Finite Fourier coefficients give
analytic derivative bounds. Subdivide unresolved intervals; an exhausted budget
is uncertified, never a pass. The absolute 12/m limit stays unchanged.

An endpoint proof alone does not preserve the current original-seed-to-candidate
path guarantee. For that, use `c(t,lambda)=seed(t)+lambda*(candidate(t)-seed(t))`
on the full unit square and enclose lambda variation too:
`d_lambda(v cross a)=delta_v cross a + v cross delta_a`.
Preserve original seed/candidate identities and every physical-copy transform;
leave other certificate gates unchanged.

Before any use: separate registration, complete interval coverage checker,
independent arithmetic implementation and tests on known circles, transforms,
between-node high-mode peaks, near-zero speed, threshold cases and excessive
curvature. Compare preserved historical states without rewriting their decisions.
Rigorous interval-proof claims require actual outward-enclosing arithmetic;
the current system explicitly provides floating-point bounds, not interval proofs.
Do not quietly promote floating-point padding into a formal guarantee.

The mandatory fine phase of the existing pilot comes first. This proposal is a
possible later experiment motivated by observed certificate-limited directions,
not proof of achievable better coils or a Step 4 result.
