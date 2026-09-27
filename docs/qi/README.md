# QI physics and particle action

Purpose: develop reliable quasi-isodynamic (QI) diagnostics from open Goodman equilibria.

Step 3 is complete for the specified nfp2 vacuum study: a changed Fourier boundary
lowers the finest relative action variance by **11.1700%**, passing all ten final
checks. The first design remains rejected despite a 14.35% training gain. The
follow-up used both known domains, so it is not a blind generalization result
or full QI qualification. The [foundation](../validation/FOUNDATION_ACCEPTANCE_RESULTS.md)
covers specified data/frozen-action regressions, not global drift/orbit models.

Current conclusion: bounce-action and limited contour/resolution checks support
actual local plasma optimization. Both analytic 81-cell drift controls pass,
including nonzero radial drift and matching physical phase. Their absolute
parameters do not establish small finite-orbit excursions. Global topology, wider
invariant coverage and real particle orbits remain open. Historical nfp3 sign
changes under relabeling do not demonstrate changed confinement.

[Overview](../README.md) · [Status](../STATUS.md) · [Roadmap](../PROJECT_PLAN.md)

## Documents

Detailed historical reports remain in German. Protocols specify the tests;
results preserve their actual outcomes and limitations.

- Balanced plasma design: [protocol](PLASMA_BALANCED_PROTOCOL.md), [results and usage](PLASMA_BALANCED_RESULTS.md). Evaluate 16 retained shapes and, if needed, eight derivative probes; at most 13 new cold solves. Actual result: 4.85% narrow-domain and 11.17% finest wider-domain gain, all ten final gates pass. Authoritative Step 3 closure.
- First own plasma surface: [protocol](PLASMA_OPTIMIZATION_PROTOCOL.md), [results and usage](PLASMA_OPTIMIZATION_RESULTS.md). Four named boundary modes, limited classical search and finer independent domain. Nineteen cold starts; numerical checks pass, physical candidate rejected despite training gain.
- Vacuum drift: [protocol](VACUUM_DRIFT_CONTROL_PROTOCOL.md), [results](VACUUM_DRIFT_CONTROL_RESULTS.md). Nonaxisymmetric exact vacuum construction, both drift components and matching physical phase. All 81 cells/243 scalar states pass; up to 74% relative flux-label excursion at 10 keV prevents finite-orbit validation.
- Absolute drift: [analytic protocol](ABSOLUTE_DRIFT_CONTROL_PROTOCOL.md), [results](ABSOLUTE_DRIFT_CONTROL_RESULTS.md). Current-carrying mirror, Cartesian drift versus action derivative and SI normalization. All 81 cells/27 refinement lines and 45 scalar reference/difference runs pass; maximum relative discrepancy 1.552e-10. Actual QI/nonzero radial drift are outside this control's scope.
- Shared field-line angle: [protocol](QI_PEST_FIDELITY_PROTOCOL.md), [results](QI_PEST_FIDELITY_RESULTS.md). Parameterization diagnosis for 16 fresh/historical differences, with inversion/chain-rule/Brent checks. All 120 grids/61,440 roots verified, but only 4/16 fidelity and 5/16 comparison-refinement screens pass.
- [Producer inventory](QI_PRODUCER_INVENTORY.md). Four version-9.0 equilibrium files and inputs bound to sources. Strict flux bit-identity fails at rounding scale; a VMEC++ iteration setting does not establish historical producer identity.
- Fresh QI resolution: [protocol](QI_FRESH_RESOLUTION_PROTOCOL.md), [results](QI_FRESH_RESOLUTION_RESULTS.md). Four cases with 2×2 radial/angular refinement. Sixteen cold solves/96 field grids checked; finer angles pass identities, but only 9/16 diagnostic-refinement and 2/16 historical-fidelity screens pass.
- Clebsch spectrum: [protocol](QI_CLEBSCH_SPECTRAL_PROTOCOL.md), [results](QI_CLEBSCH_SPECTRAL_RESULTS.md). Frozen half surfaces, 64/128 grids, saved mode mask and Parseval controls. All 48 endpoint grids checked; stable projections still miss 1e-5, so simple field-mode truncation alone does not explain the discrepancy.
- Clebsch interpolation: [protocol](QI_CLEBSCH_INTERPOLATION_PROTOCOL.md), [results](QI_CLEBSCH_INTERPOLATION_RESULTS.md). Algebraic decomposition of 24 residual fields. All decompositions verified; 10/48 half-surface grids fail even without interpolation, ruling out radial product interpolation alone.
- Clebsch normalization: [protocol](QI_CLEBSCH_PROTOCOL.md), [results](QI_CLEBSCH_RESULTS.md). Signed flux and 2π factor across four cases with independent Fourier representations. All 24 calculations verified; 19 grids pass and five poloidal identities fail. No absolute-drift qualification follows.
- [Drift and coordinates](QI_DRIFT_COORDINATES.md). Primary-source/chain-rule treatment: transform both drift components at the same physical phase. Algebraic control, not absolute-frequency validation.
- Radial gauge: [protocol](QI_RADIAL_GAUGE_PROTOCOL.md), [results](QI_RADIAL_GAUGE_RESULTS.md). Exact replay of all 84 traces; 25 nfp3 families change sign under relabeling. Independent mapping/chain-rule checks pass.
- Coverage and topology: [protocol](QI_COVERAGE_TOPOLOGY_PROTOCOL.md), [results](QI_COVERAGE_TOPOLOGY_RESULTS.md). Five radii, nine pitch values and contour winding; one inaccessible nfp1 cell remains failed.
- [Finite-pressure inventory](QI_FINITE_BETA_INVENTORY.md). Hashed inventory of 31 Goodman pressure equilibria and inputs, supporting work before SQuID-C intake.
- Initial QI measurement: [protocol](QI_MEASUREMENT_PROTOCOL.md), [results](QI_MEASUREMENT_RESULTS_V1.md). Bounce-action definition and initial checks on three vacuum cases, with independent quadrature.
- Pressure traces: [protocol](QI_PRESSURE_TRACE_PROTOCOL.md), [results](QI_PRESSURE_TRACE_RESULTS.md). Second field-line/length calculator; 84 trace and 320 family comparisons.
- Radial action: [protocol](QI_RADIAL_ACTION_PROTOCOL.md), [results](QI_RADIAL_ACTION_RESULTS.md). Four frozen vacuum/pressure cases, fixed invariants and 320 well families; no global maximum-J claim.
- Trace cross-check: [protocol](QI_TRACE_CROSSCHECK_PROTOCOL.md), [results](QI_TRACE_CROSSCHECK_RESULTS.md). Independent VMEC Fourier reconstruction and field-line inversion for the first vacuum pilot.

Required protocols and evidence retain their identities; current summaries evolve.
Git retains old document versions. The [migration manifest](../../manifests/documentation-layout-v1.json)
resolves filenames used before the documentation reorganization.
