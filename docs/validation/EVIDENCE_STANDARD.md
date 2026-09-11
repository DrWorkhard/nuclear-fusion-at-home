# Evidence standard

## Claim classes

Every material result is labelled as one of:

- **Reproduced:** obtained locally from recorded inputs and code revisions.
- **Cross-validated:** reproduced by an independent implementation or fidelity
  level with compatible assumptions.
- **Literature:** reported by a cited primary source but not reproduced locally.
- **Inferred:** a stated interpretation of reproduced or literature evidence.
- **Hypothesis:** a testable proposal without sufficient evidence yet.

## Required run record

A result used in a comparison must record:

- git revision and dirty-state status of this repository;
- revisions of all external codes;
- platform, CPU architecture, thread/MPI settings, and relevant environment;
- complete input configuration and random seeds;
- solver tolerances, resolution, termination condition, and wall time;
- raw outputs or content hashes for outputs too large to keep in git;
- evaluation code revision and metric definitions;
- failure state, warnings, and convergence checks.

## Improvement standard

An improvement must:

1. satisfy predeclared hard physics and engineering constraints;
2. improve at least one material objective without a material regression in the
   protected objectives;
3. remain improved under an independently evaluated resolution and fidelity;
4. include uncertainty from stochastic evaluation and manufacturing perturbations;
5. be compared under an equal, reported compute budget;
6. not use validation cases or high-fidelity outputs as hidden training data.

Primary reporting uses Pareto dominance and feasible-set attainment. Composite
scores may be diagnostic but are not sufficient evidence.

## Negative evidence

Solver failures, nonconvergence, platform incompatibilities, and cases in which a
surrogate or global method loses to a classical optimizer are recorded. They are
not discarded merely because they weaken the working hypothesis.
