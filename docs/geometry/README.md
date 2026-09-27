# Geometry checks

Active coil acceptance uses named Fourier reconstruction, curvature enclosures,
and continuous clearance/length bounds. These are separate from sampled
optimization penalties. A conservative bound below a clearance limit is
unresolved, not automatically a physical violation.

The latest [length-headroom fit](../optimization/LENGTH_HEADROOM_EXPLORATION.md)
passes scoped geometry; its longer predecessor has unresolved length bounds.
Padded floating-point bounds do not establish
directed interval proofs, complete self-disjointness or finite-build engineering.

Shared implementation: `coupled_coil_audit.py`, `clear_coil_geometry_audit.py`
and `curvature_bounds.py`. Completed path-certification studies and their tests
are [frozen in Git](../validation/REPRODUCING_RESULTS.md), not maintained here.
