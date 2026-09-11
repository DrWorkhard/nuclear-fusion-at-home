# Local-point VJP qualification — 2026-09-11

Declared after spatial-flux-factorization-v1 passed, before local-point timing.
The dense Jacobian is mathematically unchanged. The existing implementation
submits 1024 covectors, each supported on a single point, to a 1024-point field
VJP. Linear contraction permits evaluating each such row on its one active point.

For each of the same two fixed physical states, use the same source/DOF mapping,
normalization, surface and coil quadrature. For each surface point:

1. Set the field evaluation points to that one point.
2. Evaluate B there, initializing the per-current field cache required by B_vjp.
3. Contract B_vjp with that point's weighted normal and assemble the global row.

Always restore original field points, including on exceptions. No caching across
different physical states and no finite-difference Jacobian. Count 1024 extra
single-point B calls and 1024 single-point VJPs per state, in addition to the
common bundle and seven field-only requests of the original qualification.

Re-run all original scalar/gradient/directional criteria unchanged. Hash-check
and load the original 1024-point-VJP matrices. Align their columns through the
recorded source-to-runtime DOF permutations; require entrywise error normalized
by max(1,max|reference|) <=1e-10 and exact physical-state identity after mapping.
Time the derivative assembly, but do not infer a statistical speedup from one
timing per state, or use the faster implementation in search before it passes.

Core controls must check the cache-initialization order, linear analytic answer,
DOF order and restoration on success and forced failure. This is an implementation
efficiency check, not a changed objective or evidence of a better coil design.
