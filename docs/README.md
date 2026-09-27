# Nuclear Fusion @ Home: scientific overview

For scientific reviewers and contributors who want the reasoning behind the work
and a map of the evidence. Updated 27 September 2026.
[Front page](../README.md) · [Status](STATUS.md) · [Roadmap](PROJECT_PLAN.md)

The goal, how to start and a progress summary are on the [front page](../README.md).
The [roadmap](PROJECT_PLAN.md) defines what each step and milestone requires, the
[step results](steps/README.md) explain what each step achieved, and the
[status page](STATUS.md) summarizes the current evidence, its limits and retained
failures. Despite the name, the project is collaborative research, not (initially)
a volunteer-computing client.

## Research question

Can we computationally identify and independently verify improvements to
stellarator designs that balance magnetic-field quality, coil buildability and
robustness? We begin with open reference cases and aim eventually to develop our
own quasi-isodynamic plasma configurations together with realizable coils.

A favorable plasma target does not automatically have practical coils; a coil
system that approximates a target does not automatically preserve its confinement.
This is why we separate optimization, numerical checks and physical acceptance.

Following the [strategic review response](review/STRATEGIC_REVIEW_RESOLUTION.md),
near-term work prioritizes calibration and reachability before longer searches.
The [research workflow](validation/RESEARCH_WORKFLOW.md) separates fast exploration
from independent confirmation; [MS0's programme](optimization/STEP4_RESEARCH_PROGRAMME.md)
aims to make the bottleneck reproducible and contributable.

“Quasi-isodynamic” (QI) describes a magnetic-field property relevant to reducing
particle drifts. Our plasma result so far concerns one specific bounce-action
diagnostic, not full QI.

## Why these references?

- **W7-X:** a known equilibrium/software regression case, not a model of every
  aspect of the actual machine or a comparison to measured device performance.
- **Landreman–Paul QA / StellCoilBench:** a fixed-surface coil-method reference.
  QA method success would not establish QI or SQuID-C performance.
- **Goodman open QI cases:** the plasma-physics bridge and source of our current
  nfp2 vacuum target. Their reference data is attributed separately.
- **SQuID-C:** a later target baseline requiring a properly matched author dataset
  and more physics qualification; it is not a prerequisite for contributing now.
  Old availability searches are not a current assertion that no public data exists.

## Detailed evidence and methods

Some reproducibility reports are in German; entry documentation and folder indexes
are in English. Each index states its purpose, current conclusion and limits.
Current guidance lives here; superseded plans and chronology live in Git, not
duplicate archive documents. Scientific protocols and evidence remain when needed
to reproduce supported results, including failures.

- [Step results](steps/README.md): one English page per roadmap step with its result, limits, failures and evidence.
- [Optimization](optimization/README.md): algorithms, attempts, negative results and [open research hints](optimization/RESEARCH_HINTS.md).
- [Geometry](geometry/README.md): curvature, clearance, continuous bounds and discretization checks.
- [QI physics](qi/README.md): equilibria, action diagnostics, field lines and coordinate issues.
- [Engineering](engineering/README.md): perturbations, meshes, loads and model limitations.
- [Validation](validation/README.md): portable entry points, scientific evidence, environment and review.
- [SQuID-C / Proxima comparison](squid_c/README.md): future intake, readiness limits and the MS1 evidence framework.
- [Current research notes](logbook/README.md): decisions, lessons and latest verification.
- [Reviews](review/README.md): documentation and usability reviews with the exact reviewed version and open recommendations.

Contribution rules: [CONTRIBUTING](../CONTRIBUTING.md) and the
[review policy](validation/REVIEW_POLICY.md). Working rules for agents and
maintainers: [AGENTS.md](../AGENTS.md).
