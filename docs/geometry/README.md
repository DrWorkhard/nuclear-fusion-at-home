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
impossible. The separate local whole-homotopy study now certifies all twelve
fixed states, including two previously curvature-rejected proposals, without
relaxing a limit. Geometry success alone establishes no field improvement.

[Overview](../README.md) · [Status](../STATUS.md) · [Roadmap](../PROJECT_PLAN.md)

## Documents

Historical detailed reports below remain in German; this index gives their scope
and conclusions in English.

- Local homotopy curvature: [protocol](LOCAL_CURVATURE_PROTOCOL.md), [method/input review](LOCAL_CURVATURE_REVIEW.md), [twelve-state results](LOCAL_CURVATURE_RESULTS.md). All 336 physical copies and 285,528 rectangle bounds pass separate checks; two previously rejected proposals certify under unchanged limits. Their [field comparison](../optimization/FIXED_FIELD_PROBE_RESULTS.md) confirms small gains but no absolute field-quality pass.
- Coil perturbations: [protocol](COIL_PERTURBATION_PROTOCOL.md) and [results](COIL_PERTURBATION_RESULTS.md). Cumulative position/first-/second-derivative bounds protect distance, length and curvature relative to immutable seeds. Real 52-state matrix: 104 certificate calls, 208 direct grids; required small probes pass, 18 larger states remain uncertified. Includes checkpoint-reference preservation and the corrected test gap.
- Outside-plasma starting coils: [protocol](CLEAR_COIL_INITIALIZATION_PROTOCOL.md) and [results](CLEAR_COIL_INITIALIZATION_RESULTS.md). Shared 3D plasma envelope, circles and convex Fourier linear programs. All twelve geometries pass; both start families selected. No field or Step 4 completion claim.
- [Continuous coil clearance](CONTINUOUS_COIL_CLEARANCE_CHECK.md). Retrospective distance lower bounds valid between all sample points, from Fourier derivative bounds.
- Continuous curvature: [protocol](CONTINUOUS_CURVATURE_PROTOCOL.md) and [results](CONTINUOUS_CURVATURE_RESULTS.md). Analytic controls and bounds for the frozen curves.
- Curvature aliasing: [audit](CURVATURE_ALIASING_AUDIT.md) and [results](CURVATURE_ALIASING_RESULTS.md). Independent position/curvature witnesses confirm violations missed by coarse optimization grids.

Required protocols and evidence retain their identities; current summaries evolve.
Git retains old document versions. The [migration manifest](../../manifests/documentation-layout-v1.json)
resolves filenames used before the documentation reorganization.
