# Project plan

## Objective

Build a reproducible, method-neutral platform that can establish credible
stellarator coil-design improvements and is ready to accept SQuID-C as the target
baseline without redesigning the workflow.

## Work packages

### WP0 — Reproducibility and evidence

- Record hardware, operating system, solver versions, source revisions, inputs,
  seeds, tolerances, and compute budgets.
- Separate facts reproduced locally from literature claims and hypotheses.
- Preserve failed runs and negative findings when they affect conclusions.

Exit: a fresh checkout can recreate the environment and run a smoke test.

### WP1 — StellCoilBench method baseline

- Pin and install StellCoilBench without vendoring generated results.
- Reproduce at least one Landreman-Paul case.
- Verify metric definitions independently where practical.
- Establish equal-budget comparisons for optimization methods.

Exit: a local result is accepted by the same evaluation path used by the
benchmark and is reproducible from recorded inputs.

### WP2 — W7-X physics regression

- Reproduce a published W7-X VMEC equilibrium.
- Verify geometry, aspect ratio, beta, iota, and selected magnetic metrics.
- Add coil-field and Poincare regression when the authoritative coil data path is
  established.

Exit: deterministic metrics agree with the authoritative reference within
predeclared tolerances, and deviations are explained.

### WP3 — Open QI bridge

- Select a machine-readable QI equilibrium with clear provenance.
- Reproduce QI, maximum-J, neoclassical, and fast-particle screening metrics in
  increasing fidelity.
- Pin and run SIMPLE locally against the exact open QI wout files; distinguish
  smoke-scale orbit tracing from reproduction of the published 5,000-particle
  protocol.
- Exercise exactly the data interfaces intended for SQuID-C.

Exit: the QI case runs through equilibrium, coil, robustness, and validation
interfaces without case-specific code.

### WP4 — Robust coil optimization

- Reproduce a strong classical augmented-Lagrangian baseline.
- Add finite-build, force/stress, clearance, and tolerance objectives.
- Compare local, global, stochastic, surrogate-assisted, and hybrid methods under
  equal budgets.
- Report Pareto sets; do not promote a single opaque weighted score as the main
  scientific result.

Exit: any claimed improvement survives independent high-resolution and
free-boundary validation.

### WP5 — SQuID-C readiness

- Audit all gates in `docs/SQUID_C_READINESS.md`.
- Prepare a canonical SQuID-C data manifest and reproduction protocol.

Exit: only authoritative SQuID-C files and paper-specific run parameters remain
missing.

## Order of execution

WP0 -> WP1 and WP2 -> WP3 -> WP4 -> WP5. Work may overlap, but no optimization
claim can outrun the validation layer on which it depends.
