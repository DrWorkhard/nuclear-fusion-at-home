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
- [ ] Coil field and Poincare regression established.
- [x] Perturbation/sensitivity protocol recorded.

## G4 — QI bridge

- [x] Authoritative open QI equilibrium ingested.
- [x] QI and maximum-J metrics reproduced.
- [x] Fast-particle screening path exercised with pinned SIMPLE.
- [x] Neoclassical solver path exercised locally (paper cross-check currently
      fails and is retained as a validation warning).
- [ ] No case-specific code is required to add a new equilibrium.

## G5 — Engineering and robustness

- [ ] Finite-build coil representation validated.
- [ ] Structural solve has a mesh-convergence record.
- [x] Manufacturing perturbation distribution is predeclared.
- [ ] Free-boundary validation is separated from optimization.

## G6 — SQuID-C intake contract

- [x] Schema for equilibrium, profiles, coils, currents, scale, and provenance.
- [x] Paper reproduction metrics and tolerances predeclared.
- [ ] Raw/derived data lineage and hashes recorded.
- [ ] Authoritative SQuID-C files obtained or their absence documented as the only
      remaining external blocker.
