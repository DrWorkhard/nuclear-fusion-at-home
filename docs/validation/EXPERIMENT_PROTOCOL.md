# Method-comparison protocol

## Unit of comparison

Methods operate on the same target surface, coil representation, initialization
distribution, hard constraints, and evaluation implementation. The primary output
is a feasible Pareto set, not a single weighted objective.

## Budgets

Every comparison reports three budgets:

1. number of high-fidelity objective/constraint evaluations;
2. wall time and hardware allocation;
3. number and cost of any lower-fidelity or surrogate-training evaluations.

The headline comparison fixes the high-fidelity evaluation budget. A second view
fixes wall-clock compute. Surrogate construction, failed evaluations, line
searches, and feasibility restoration all count; preprocessing shared by every
method is reported separately.

The pinned augmented-Lagrangian path currently reports its inner iteration cap as
`optimization_nfev`; this is not an evaluation count. Screening runs therefore
record every inner SciPy subproblem's `nfev`, `njev`, and `nit`, but cannot enter
the headline equal-budget comparison until setup, Taylor-test, and post-step
constraint evaluations are also counted and an exact global stop is enforced.

## Replication and uncertainty

- Deterministic methods: two identical runs before acceptance, then at least five
  initializations for comparative studies.
- Stochastic/global/surrogate methods: at least ten seeded runs for screening;
  increase the sample size when confidence intervals overlap materially.
- Report median, interquartile range, best feasible result, feasibility rate, and
  empirical attainment surfaces.
- Manufacturing perturbations use a frozen, versioned distribution and common
  random numbers across methods.

## Protected objectives and constraints

At minimum: normal-field error, coil length, minimum coil-coil and coil-surface
clearance, curvature, finite-build clearance, turns/current, electromagnetic
force/torque, structural stress/deformation, and robustness quantiles. Once the QI
bridge is active, QI/max-J and particle/neoclassical screening metrics are
protected as well.

## Method families

The first comparison includes L-BFGS-B and augmented-Lagrangian baselines. Global,
evolutionary, stochastic, surrogate-assisted, active-learning, and hybrid methods
enter with the same accounting. No method receives a budget or metric advantage
because it is described as AI.

## Holdout validation

Optimization resolution, robustness samples, and any surrogate training set are
separate from a frozen higher-resolution holdout. Claimed improvements must be
reevaluated from serialized coils by the holdout path and later in a free-boundary
equilibrium when available.

For Fourier coils, the geometry holdout uses direct analytic Fourier derivatives
with at least 20,000 points per unique coil for maximum curvature. Candidate
minimum-clearance pairs are identified globally and refined at 20,000 points per
curve; coil-surface distance uses a full-torus surface grid with a documented
resolution study. The optimization grid is never used as the final geometry
certificate.
