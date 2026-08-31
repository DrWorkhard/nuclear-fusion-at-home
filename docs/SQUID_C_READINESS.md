# SQuID-C readiness gates

The project is ready for SQuID-C when all gates below are satisfied.

## G1 — Reproducible environment

- [x] One-command environment creation on the canonical platform.
- [x] Recorded fallbacks for unsupported native ARM dependencies.
- [ ] Deterministic smoke tests in continuous integration.

## G2 — Method benchmark

- [x] Pinned StellCoilBench revision and data assets.
- [x] At least one Landreman-Paul result reproduced.
- [x] Independent checks of core coil metrics.
- [x] Equal-budget experiment protocol.

## G3 — W7-X regression

- [x] Authoritative W7-X equilibrium ingested.
- [ ] Equilibrium metrics reproduced within declared tolerances.
- [x] Coil field and Poincare regression established for the serialized
      W7-X-target benchmark coils, including a direct Biot-Savart holdout.
- [x] Perturbation/sensitivity protocol recorded.

## G4 — QI bridge

- [x] Authoritative open QI equilibrium ingested.
- [x] QI and maximum-J metrics reproduced.
- [x] Fast-particle screening path exercised with pinned SIMPLE.
- [x] Neoclassical solver path exercised locally (paper cross-check currently
      fails and is retained as a validation warning).
- [x] New equilibria enter through a case-independent manifest-to-VMEC/Boozer
      intake path; nfp=1 and an unmodified nfp=2 transfer case pass it.

## G5 — Engineering and robustness

- [x] Finite-build coil representation validated for the independent periodic
      structured sweep; the upstream Gmsh fallback fails on the real candidate.
- [x] Structural solve has a mesh-convergence record (extended series converges
      numerically, but the resulting deformation invalidates linear mechanics
      as an absolute design model).
- [x] Manufacturing perturbation distribution is predeclared.
- [x] Free-boundary validation is separated from optimization and exercised as
      an immutable vacuum holdout with a response-grid refinement.

## G6 — SQuID-C intake contract

- [x] Schema for equilibrium, profiles, coils, currents, scale, and provenance.
- [x] Paper reproduction metrics and tolerances predeclared.
- [ ] Raw/derived data lineage and hashes recorded.
- [ ] Authoritative SQuID-C files obtained or their absence documented as the only
      remaining external blocker.
