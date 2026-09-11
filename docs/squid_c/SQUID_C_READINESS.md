# SQuID-C readiness gates

The project is ready for SQuID-C when all gates below are satisfied.

Audit revision 2026-09-09: the claim that all internally executable gates were
complete is withdrawn. We can receive and inspect an author package; scientific
reproduction and improvement certification remain open. See
[the audit report](../validation/AUDIT_2026-09-09.md). The August availability search is a dated,
bounded result; missing author data is not the only remaining blocker.

## G1 — Reproducible environment

- [x] One-command environment creation on the canonical platform.
- [x] Recorded fallbacks for unsupported native ARM dependencies.
- [x] Deterministic locked smoke-test command and CI workflow. The exact command
      passes locally; remote execution remains an operational witness item until
      a Git remote is configured.
- [ ] Automated scientific integration suite from a fresh data bootstrap.
      Partial: strict QI numerical/metadata suite passes five non-skipping tests
      after cached-archive extraction in a fresh detached clone. A full native
      W7-X/solver bootstrap and hosted execution remain unwitnessed.

## G2 — Method benchmark

- [x] Pinned StellCoilBench revision and data assets.
- [x] At least one Landreman-Paul result reproduced.
- [x] Independent checks of core coil metrics.
- [x] Equal-budget experiment protocol.
- [ ] Strong feasible constrained baseline and actual equal-budget method comparison.
      Partial: full-vector/Jacobian oracle passes named-DOF, exact-budget and
      repeatability qualification. AL uses its 150-bundle cap; L-BFGS-B stops at
      10 while still infeasible. A common cap is not equal consumed work or a ranking.
      Normalized follow-up also reproduces exactly; independent holdout rejects
      both method-best candidates (flux; additionally AL length). Baseline remains open.
      Fixed affine-coordinate follow-up now consumes exactly 1500 bundles for
      each method and repeat, with identical physical problem and reproducible
      histories. Both candidates still fail flux, length and off-grid curvature;
      a feasible baseline and multiple initializations remain open.
      Guarded trust-region follow-up repeats exactly at 3000 bundles and passes
      geometry screens including continuous curvature/inter-coil bounds, but
      flux remains 101.752 times the fixed limit. G2 stays open. Independent replay
      exposed and corrected cross-process DOF ordering; all 14 archived best
      arrays match their serialized field parameters. See GUARDED_FEASIBILITY_RESULTS.md.
      A controlled spatial-residual pilot now preserves the scalar objective and
      repeats at 128 proposals per arm. Spatial raw flux is 2.43 times lower than
      scalar, but still 44.488 times over the limit; both fail admission. Geometry
      screens pass, while spatial derivative work is substantially greater.
      A two-repeat, one-start 300-second comparison now finds about 2.35x lower
      spatial flux at equal time, but all four candidates fail flux; scalar also
      fails clearance. Spatial flux remains >=41.461 times the fixed limit.
      Feasible construction and multi-start comparisons remain open
      (TIMED_SPATIAL_PILOT_RESULTS.md).
      A separately qualified direct-inequality SLSQP construction now repeats at
      256 bundles and passes geometry/native extras, but flux remains 23.308
      times the same limit. No converged or feasible baseline; G2 stays open
      (DIRECT_SLSQP_PILOT_RESULTS.md).

## G3 — W7-X regression

- [x] Authoritative W7-X equilibrium ingested.
- [x] The declared project equilibrium metrics are reproduced within pinned
      tolerances against a native, version-compatible VMEC 8.52 run. Full-file
      comparison remains separately failed at 60/63 fields; see the W7-X protocol.
      The selection and grid refinement were retrospective, not preregistered.
- [x] Coil field and Poincare regression established for the serialized
      W7-X-target benchmark coils, including a direct Biot-Savart holdout.
- [x] Perturbation/sensitivity protocol recorded.

## G4 — QI bridge

- [x] Authoritative open QI equilibrium ingested.
- [x] Legacy QI and published J routines executed.
- [x] Preregistered bounce-action measurement/refinement screens on three vacuum
      cases; 12,960 integrals independently checked by quadrature.
- [x] Independent geometric tracing agrees on 27 sampled traces and 135 pitch
      cells. See QI_TRACE_CROSSCHECK_RESULTS.md for scope and tolerances.
- [ ] Resolution-stable QI objective and independent maximum-J assessment qualified.
      Expanded five-radius/nine-pitch study: nfp2/nfp3 pass; nfp1 retains one
      inaccessible-domain failure. 134/135 cells pass sampled action and poloidal
      contour screens (QI_COVERAGE_TOPOLOGY_RESULTS.md). Remaining: full invariant
      domain, well-family identity, continuum topology and finite-pressure maximum-J;
      a bounded action study is not a full QI score.
      Finite-pressure Goodman data are now inventoried (31 cases); this work is
      internally executable and must not be called blocked on SQuID-C files.
      Four-case fixed-invariant radial pilot matches 320 well families; independent
      quadrature confirms every derivative classification. nfp2 beta2 is negative
      in the sampled domain; nfp3 beta2 remains mixed. A second tracer passes 84
      trace and 320 family comparisons, preserving the resolved signs. Full-domain,
      equilibrium-grid and gauge qualification remain open.
- [x] Fast-particle screening path exercised with pinned SIMPLE.
- [x] Neoclassical solver path exercised locally (paper cross-check currently
      fails and is retained as a validation warning).
- [x] New equilibria enter through a case-independent manifest-to-VMEC/Boozer
      intake path; nfp=1 and an unmodified nfp=2 transfer case pass it.

## G5 — Engineering and robustness

- [x] Structured sweep mesh generation and volume/tag screens exercised.
- [ ] Finite-build self-intersections, quality, orientation and solid clearances checked.
      Partial: all six structured meshes pass intrinsic cell-quality, shared-face
      orientation and boundary-topology screens. Spatial nonoverlap, full assembly
      clearance and physical winding-pack orientation are still unqualified.
- [x] Structural discretization series recorded; the final pair passes its screen.
- [ ] Mesh independence and physically valid mechanical predictions established.
      The large deformation invalidates the absolute linear-model predictions.
- [x] Manufacturing perturbation distribution is predeclared.
- [x] Free-boundary validation is separated from optimization and exercised as
      an immutable vacuum holdout with a response-grid refinement.

## G6 — SQuID-C intake contract

- [x] Schema for equilibrium, profiles, coils, currents, scale, and provenance.
      Schema 2 is exercised end-to-end with separate fixed/free-boundary wouts
      and ten required artifact roles.
- [ ] Author-confirmed canonical state, beta tolerance and field-error quadrature.
- [ ] Executable coil reconstruction and paper-metric reproduction evaluator.
- [ ] Raw/derived data lineage and hashes recorded.
- [x] Bounded availability search recorded. The 2026-08-31 audit found no publicly
      identified authoritative package; this is a bounded search result, not a
      proof that unpublished or anonymously indexed data do not exist.
