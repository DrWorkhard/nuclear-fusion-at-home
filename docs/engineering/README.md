# Engineering models and independent plasma response

Purpose: extend ideal filament-coil studies toward manufacturing errors, volume
meshes, structural mechanics and free plasma boundaries.

This is later research, separate from the completed
[foundation and iteration workflow](../validation/FOUNDATION_ACCEPTANCE_RESULTS.md).
Steps 1/2 do not qualify full winding packs or mechanics.

Current conclusion: all six meshes pass intrinsic quality checks and the
independently audited non-overlap screen for pairs without shared vertex indices.
The finest-case repeat reproduces its earlier two-million-pair prefix exactly
and completes the series. Neighboring elements and full assemblies still need
checks. Large deformations invalidate the absolute linear-stress predictions;
a physically valid complete mechanics model remains open.

[Overview](../README.md) · [Status](../STATUS.md) · [Roadmap](../PROJECT_PLAN.md)

## Documents

Historical detailed reports remain in German; the English summaries distinguish
completed numerical checks from engineering conclusions.

- [Tetrahedron non-overlap method](TETRA_NONOVERLAP_METHOD.md). Separating directions, interior witnesses, complete pair accounting and independent partition/witness audits; 34 kernel controls.
- Nonlocal mesh overlap: [protocol](MESH_NONLOCAL_PROTOCOL.md), [results](MESH_NONLOCAL_RESULTS.md) and [retry protocol](MESH_NONLOCAL_RETRY_PROTOCOL.md). Six unchanged meshes, vertex-disjoint pairs only. First series: five complete passes and one pair-cap interruption; 3,358,644 individual pair proofs verified. Retry resolves historical source by Git/SHA without altering kernels or thresholds.
- Finest mesh: [completion protocol](MESH_FINE_COMPLETION_PROTOCOL.md) and [results](MESH_FINE_COMPLETION_RESULTS.md). Separate repeat of h=0.010 with four-million-call/1,200-second limits. All 2,222,785 separating proofs and exact old two-million prefix verified; all six nonlocal screens complete, full engineering gate G5 still open.
- [Free-boundary protocol](FREE_BOUNDARY_PROTOCOL.md). Immutable vacuum plasma-response holdout, separate from optimization.
- [Mesh integrity protocol](MESH_INTEGRITY_PROTOCOL.md). Intrinsic quality, orientation and boundary topology of the six frozen meshes.
- [Robustness protocol](ROBUSTNESS_PROTOCOL.md). Spatially correlated manufacturing perturbations of filaments, not a complete tolerance model.
- [Structural protocol](STRUCTURAL_PROTOCOL.md). Volume-mesh/mechanics path and resolution sequence, not a validated reactor structure.

Required protocols and evidence retain their identities; current summaries evolve.
Git retains old document versions. The [migration manifest](../../manifests/documentation-layout-v1.json)
resolves filenames used before the documentation reorganization.
