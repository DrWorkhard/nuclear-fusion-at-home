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

Following the [review response](review/STRATEGIC_REVIEW_RESOLUTION.md),
near-term work focuses on normalized coil fitting and shared acceptance checks.
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

Current entry documentation is English. Closed detailed reports, some in German,
and their code/tests resolve at the [freeze tag](validation/REPRODUCING_RESULTS.md).
The main tree holds active work and concise conclusions, not duplicate archives.
Tracked evidence stays unchanged; raw data needs separate retention and backup.

- [Step results](steps/README.md): one English page per roadmap step with its result, limits, failures and evidence.
- [Optimization](optimization/README.md): algorithms, attempts, negative results and [open research hints](optimization/RESEARCH_HINTS.md).
- [Geometry](geometry/README.md): curvature, clearance, continuous bounds and discretization checks.
- [QI physics](qi/README.md): completed plasma result and remaining realized-field questions.
- [Engineering](engineering/README.md): deferred models and limits of filament geometry.
- [Validation](validation/README.md): portable entry points, scientific evidence, environment and review.
- [SQuID-C / Proxima comparison](squid_c/README.md): future matched-reference requirements.
- [Current research notes](logbook/README.md): decisions, lessons and latest verification.
- [Reviews](review/README.md): strategic and simplicity reviews, plus our current response.

## Reading the evidence

**Normal RMS** measures field leaking across the target boundary; **interior-vector
RMS** measures disagreement with the target field inside. Lower is better under
the same normalization and sampling. Sparse public scores and dense native scores
are different tests. **Bounce action** is a trapped-particle motion diagnostic,
not measured confinement. **Accepted** means passing the stated scientific gates;
a passing software test or a same-code report replay does not establish that.
Read each claim's source revision, comparison and failed checks before its score.

Contribution rules: [CONTRIBUTING](../CONTRIBUTING.md) and the
[review policy](validation/REVIEW_POLICY.md). Working rules for agents and
maintainers: [AGENTS.md](../AGENTS.md).
