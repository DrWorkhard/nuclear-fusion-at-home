# Fusion Baselines

Reproducible research infrastructure for testing and improving stellarator
coil designs, with a long-term focus on quasi-isodynamic (QI) configurations
relevant to Proxima Fusion's design direction.

The project starts from three deliberately separate baselines:

1. **W7-X** for physics and software regression against a built stellarator.
2. **StellCoilBench** for standardized coil-optimization comparisons.
3. **An open QI configuration** for QI-specific metrics before SQuID-C data is
   available.

SQuID-C is the target research baseline. It will be admitted only when its
machine-readable equilibrium, profiles, coils, currents, scaling, and provenance
are sufficient for an exact reproduction rather than a reconstruction from plots.

## Research principle

No method receives preferred status because it is labelled AI. Gradient methods,
automatic differentiation, augmented-Lagrangian methods, global search, robust
optimization, surrogate models, active learning, and hybrids are compared under
the same constraints and computational budget.

The primary question is:

> Can we find coil systems that improve the physics-engineering Pareto frontier
> when finite build, electromagnetic loading, manufacturing errors, and the
> free-boundary plasma response are included?

## Status

The core environment and pinned StellCoilBench/SIMSOPT/VMEC++ stack run natively
on Apple M1. The Landreman-Paul QA case is bit-reproducible, the W7-X coil and
equilibrium baselines run, and all three authoritative Goodman QI vacuum cases
have been exercised through equilibrium, legacy QI and J diagnostic routines.
Generic real-data metadata intake is verified for nfp=1 and nfp=2. The September 9
audit withdrew the full-readiness claim: scientific admission, a qualified QI
objective and a physically valid engineering model remain open. See:

The first preregistered bounce-action study now passes on all three open-QI
vacuum cases, with independent quadrature and geometry-based tracing checks.
Its scope and the remaining QI qualification work are documented below.

September 10: 31 finite-pressure Goodman equilibria are now hash-inventoried.
A four-case individual-well radial-action pilot has independent quadrature and
second-tracer checks: nfp2 at nominal beta=2% has negative derivatives throughout
the sampled domain, while nfp3 at that pressure remains mixed. This is not a
global maximum-J certificate. Both recent optimization candidates remain rejected
by the independent feasibility holdout; no SoTA improvement is claimed.

- [Audit and corrected readiness assessment](docs/AUDIT_2026-09-09.md)
- [Bounce-action measurement results](docs/QI_MEASUREMENT_RESULTS_V1.md)
- [Independent tracing results](docs/QI_TRACE_CROSSCHECK_RESULTS.md)
- [Finite-pressure data inventory](docs/QI_FINITE_BETA_INVENTORY.md)
- [Individual-well radial-action results](docs/QI_RADIAL_ACTION_RESULTS.md)
- [Independent finite-pressure tracing](docs/QI_PRESSURE_TRACE_RESULTS.md)
- [Rejected normalized optimization candidates](docs/NORMALIZED_FEASIBILITY_RESULTS.md)

- [Project plan](docs/PROJECT_PLAN.md)
- [Evidence standard](docs/EVIDENCE_STANDARD.md)
- [Findings log](docs/FINDINGS.md)
- [Decision log](docs/DECISIONS.md)
- [SQuID-C readiness gates](docs/SQUID_C_READINESS.md)
- [SQuID-C reproduction contract](docs/SQUID_C_ACCEPTANCE.md)
- [SQuID-C authoritative-data request](docs/SQUID_C_DATA_REQUEST.md)
- [Manufacturing-robustness protocol](docs/ROBUSTNESS_PROTOCOL.md)
- [Finite-build and structural protocol](docs/STRUCTURAL_PROTOCOL.md)
- [Free-boundary holdout protocol](docs/FREE_BOUNDARY_PROTOCOL.md)
- [W7-X equilibrium regression protocol](docs/W7X_EQUILIBRIUM_PROTOCOL.md)

## Canonical commands

```bash
./scripts/bootstrap_macos.sh
uv run python scripts/run_stellcoilbench_case.py \
  external/stellcoilbench/cases/basic_LandremanPaulQA.yaml \
  artifacts/runs/lpqa-baseline
./scripts/bootstrap_vmecpp.sh
./scripts/bootstrap_qi_data.sh
./scripts/bootstrap_simple.sh
./scripts/bootstrap_neo_jax.sh
uv run fusion-baselines summarize-equilibrium \
  manifests/qi-goodman-2022.json --data-root .
uv run python scripts/audit_squid_c_availability.py \
  evidence/squid-c-availability-$(date +%F).json
```
