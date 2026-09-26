# Geometry checks

Purpose: assess coil curvature and clearance independently of optimization sample points.

Current conclusion: coarse grids can miss real curvature violations. Position
witnesses and continuous Fourier bounds have been checked, using ordinary
floating-point arithmetic with safety margins. Full winding-pack and
self-intersection checks remain open. All twelve new outside-plasma starting
geometries pass the specified filament checks, including all 72 direct tests.
Their subsequent field calculations pass numerical checks but fail field-quality
limits. The 52-state cumulative-perturbation study certifies every required small
probe; 18 larger states remain conservatively uncertified, rather than proved
impossible. Geometry success alone establishes no field improvement.

[Overview](../README.md) · [Status](../STATUS.md) · [Roadmap](../PROJECT_PLAN.md)

## Documents

Historical detailed reports below remain in German; this index gives their scope
and conclusions in English.

- Local homotopy curvature: [protocol](LOCAL_CURVATURE_PROTOCOL.md), [method/input review](LOCAL_CURVATURE_REVIEW.md), [implementation qualification](LOCAL_CURVATURE_PROGRESS.md). Twelve fixed saved states and unchanged 12/m limit; complete seed-to-candidate coverage, exact budgets and separate arithmetic checker. Full regression passes 5,110 tests; separate execution checkpoint remains. No project-state calculation or changed historical decision yet.

- [Local curvature-bound options](LOCAL_CURVATURE_BOUND_OPTIONS.md). Prospective interval/subdivision inequality motivated by the protected pilot's conservative curvature bottleneck. Preserve the original-seed homotopy guarantee, all other gates and the 12/m limit; no implementation, calculation or new candidate pass.
- Coil perturbations: [protocol](COIL_PERTURBATION_PROTOCOL.md) and [results](COIL_PERTURBATION_RESULTS.md). Cumulative position/first-/second-derivative bounds protect distance, length and curvature relative to immutable seeds. Real 52-state matrix: 104 certificate calls, 208 direct grids; required small probes pass, 18 larger states remain uncertified. Includes checkpoint-reference preservation and the corrected test gap.
- Outside-plasma starting coils: [protocol](CLEAR_COIL_INITIALIZATION_PROTOCOL.md) and [results](CLEAR_COIL_INITIALIZATION_RESULTS.md). Shared 3D plasma envelope, circles and convex Fourier linear programs. All twelve geometries pass; both start families selected. No field or Step 4 completion claim.
- [Continuous coil clearance](CONTINUOUS_COIL_CLEARANCE_CHECK.md). Retrospective distance lower bounds valid between all sample points, from Fourier derivative bounds.
- Continuous curvature: [protocol](CONTINUOUS_CURVATURE_PROTOCOL.md) and [results](CONTINUOUS_CURVATURE_RESULTS.md). Analytic controls and bounds for the frozen curves.
- Curvature aliasing: [audit](CURVATURE_ALIASING_AUDIT.md) and [results](CURVATURE_ALIASING_RESULTS.md). Independent position/curvature witnesses confirm violations missed by coarse optimization grids.

Historical content and hashes remain unchanged. Resolve old filenames with the
[migration manifest](../../manifests/documentation-layout-v1.json).
