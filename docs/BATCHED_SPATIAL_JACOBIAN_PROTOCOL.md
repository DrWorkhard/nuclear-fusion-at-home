# Batched analytic spatial Jacobian qualification — 2026-09-11

Declared before implementation timing or qualification. Replace 1024 separate
single-point adjoint traversals with per-coil analytic quadrature and matrix
contractions; retain exactly the same ideal-filament Biot-Savart discretization.
Coil cross-section regularization remains used by engineering models, not inserted
into this surface field kernel. No passive-current arrays are supported.

For R=p-gamma(t), tangent T, fixed weighted normal w, and f=w dot (T cross R):

    z_coil = (1e-7 I / Q) sum f / |R|^3,
    C_gamma = (T cross w)/|R|^3 + 3 f R/|R|^5,
    C_tangent = (R cross w)/|R|^3.

Contract C_gamma and C_tangent with the exact Fourier geometry derivatives,
then map full coefficient labels into the global free-DOF basis. Add current
derivatives through each coil's current.vjp, preserving dependent sums and signs.
Process one physical coil at a time, with no (points, quadrature, DOFs, 3) tensor.
No matrix caching across different states, approximate differentiation or cutoff.

Core controls: compare field projection to direct cross-product quadrature,
analytic circular-loop axis field, centered geometry/current derivatives;
check current sums, repeated symmetry DOFs and arbitrary free-DOF ordering in
the adapter; reject nonfinite inputs, singular observation points and bad shapes.

Physical checks: the same original and rejected guarded states from the spatial
qualification. Hash-check saved matrices; explicitly map archived physical DOFs.
Require z and Dz differences versus the qualified local-VJP reference normalized
by max(1,max|reference|) <=1e-10, raw Phi relative error <=1e-10, lifted common
merit/gradient equivalence <=1e-10, and seed-45 finest directional errors <=1e-6
at steps 1e-4,1e-5,1e-6. Keep all steps. Compare original field evaluation points
before/after: the batched path must not mutate them.

Report all sixteen-coil contractions, geometry/current derivative calls and
wall time explicitly. Repeat assembly three times at each fixed state and retain
all timings/matrix differences; first run includes setup effects. Passing these
checks permits a separately preregistered compute-aware optimization experiment,
not a feasibility or SoTA claim. Existing physical acceptance limits remain fixed.

Primary implementation references: pinned SIMSOPT biot_savart_impl.h, curve.py,
coil.py and their executed derivatives. Record hashes and executing versions.
