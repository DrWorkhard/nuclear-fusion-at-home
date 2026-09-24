# Nuclear Fusion @ Home: scientific overview

For contributors and scientific reviewers. Updated 24 September 2026.
[Quickstart](validation/PUBLIC_QUICKSTART.md) · [Status](STATUS.md) · [Roadmap](PROJECT_PLAN.md)

## Research question

Our end goal (MSX) is to contribute to nuclear fusion for humanity by finding the best
reactor design current technology can achieve. We use “best” as a research aim
under explicit performance, buildability, robustness, safety and cost constraints,
not as a claim that a global optimum has been proved.

Can we computationally identify and independently verify improvements to
stellarator designs that balance magnetic-field quality, coil buildability and
robustness? We begin with open reference cases and aim eventually to develop our
own quasi-isodynamic plasma configurations together with realizable coils.

A stellarator uses shaped external coils to create its confining magnetic field.
A favorable plasma target does not automatically have practical coils; a coil
system that approximates a target does not automatically preserve its confinement.
This is why we separate optimization, numerical checks and physical acceptance.

“Quasi-isodynamic” (QI) describes a magnetic-field property relevant to reducing
particle drifts. Our present plasma result concerns a specific bounce-action
diagnostic. It is not a demonstration of full QI, better measured confinement or
net energy production. Proxima Fusion/SQuID-C motivate our longer-term direction;
this is an independent project without claimed affiliation or endorsement.

## Evidence and current position

| Step / milestone | Status | What it establishes |
| --- | --- | --- |
| 1. Establish a reliable foundation | Complete (local reference tools) | W7-X/Goodman regression and specified LPQA filament tools |
| 2. Make design iteration reproducible | Complete (iteration workflow) | Real optimization paths can be saved, replayed and separately evaluated |
| 3. Improve our own plasma target | Complete (vacuum study) | An actual boundary change lowers the specified fine action-variance metric by 11.17% |
| 4. Develop plasma and coils together | In progress | Geometry-qualified starts exist; field-quality admission and broader physics remain unresolved |
| 5. Demonstrate a meaningful design advantage | Not achieved | No state-of-the-art or power-plant claim |
| MS1. Contact Proxima Fusion with strong evidence | Not reached | Contact Proxima as soon as strong, independently checked evidence supports a meaningful design advantage over the design they are pursuing |
| MSX. Our end goal | Long-term goal | Contribute to nuclear fusion for humanity; extends beyond MS1 and is not a present global-optimality claim |

**MS1 — Proxima Fusion outreach:** as soon as strong, reproducible and independently
checked evidence supports that our design is better than the design Proxima is
pursuing, we will contact them with the evidence. This targeted Step 5 outcome is
**not reached** and is distinct from the ultimate goal. It requires a correctly
identified reference, meaningful design-level comparison and explicit uncertainty/
trade-offs; see the [MS1 framework](squid_c/MS1_PROXIMA_COMPARISON.md).

The [plasma result](qi/PLASMA_BALANCED_RESULTS.md) includes independently computed
diagnostics and an exact cold repeat. Both action domains were used during
construction, so this is not a blind generalization test. The first plasma design
was rejected and remains visible. Our [first actual-coil pilot](optimization/COUPLED_COIL_PILOT_RESULTS.md)
also failed physical acceptance. Subsequent work produced valid starting geometry
and [numerically qualified field evaluations](optimization/CLEAR_COIL_FIELD_START_RESULTS.md),
but the magnetic errors remain far too high. No new feasible coil baseline exists.
The next protected-search controller now passes its
[bounded software qualification](optimization/PROTECTED_SEARCH_SOFTWARE_RESULTS.md);
native execution and physical-result verification remain separate work.

The [status page](STATUS.md) links the numerical evidence and important unresolved
model limitations. Independent internal calculations and agent reviews are not
external peer review. Test counts are software evidence, not physical admission.

## Public collaboration

Nuclear Fusion @ Home is collaborative computational research, not initially a
distributed-compute scheduler. Anyone may contribute with or without an agent.
Useful unsolicited work, alternative approaches, replications, documentation,
counterexamples and negative results are welcome. Compute spending disclosure is
optional; research hints are suggestions, never a gate for participation.

Our first portable layer includes a small real-coil reference, explicitly named
JSON candidates and sampled fixed-current B/A calculations. It needs no native
installation or maintainer-specific data. It is deliberately **not** the full
historical acceptance pipeline. Read [the quickstart's limits](validation/PUBLIC_QUICKSTART.md)
before interpreting a score. The committed-source reference and candidate paths
pass all eight [local copied-tree release checks](validation/PUBLIC_RELEASE_RESULTS.md),
without native packages or downloads. Hosted and independent-machine verification
remain separate, outstanding work.
The [release review follow-up](validation/PUBLIC_REVIEW_FIXES.md) adds reference
score comparisons, named edits, Python 3.11+ support, English folder indexes and
an explicit lightweight core-CI scope. The fresh-clone core runner, 44 public tests
and eight real release checks on each of Python 3.11/3.12/3.14 pass locally;
the latest full native regression passes 2,180 tests with 334 existing warnings.
An initial [publication inventory](validation/PUBLICATION_INVENTORY.md) also finds
historical home-path indicators; it is not full security/rights clearance.

A contributor should be able to discover a question, reproduce a reference,
propose a change, understand its result and submit reviewable evidence without
reading our conversation history. [Contributing](../CONTRIBUTING.md) explains the
open route; [review policy](validation/REVIEW_POLICY.md) separates software merges
from scientific acceptance.

## Why these references?

- **W7-X:** a known equilibrium/software regression case, not a model of every
  aspect of the actual machine or a comparison to measured device performance.
- **Landreman–Paul QA / StellCoilBench:** a fixed-surface coil-method reference.
  QA method success would not establish QI or SQuID-C performance.
- **Goodman open QI cases:** the plasma-physics bridge and source of our current
  nfp2 vacuum target. Their reference data is attributed separately.
- **SQuID-C:** a later target baseline requiring a properly matched author dataset
  and more physics qualification. Old availability searches are not a current
  assertion that no public data exists.

## Detailed evidence and methods

Most historical reports are in German; newer public entry documentation is in
English. Each purpose-specific folder has its own index and limits. No hidden
conversation context is required to follow the evidence.

- [Optimization](optimization/README.md): algorithms, attempts, negative results and [open research hints](optimization/RESEARCH_HINTS.md).
- [Geometry](geometry/README.md): curvature, clearance, continuous bounds and discretization checks.
- [QI physics](qi/README.md): equilibria, action diagnostics, field lines and coordinate issues.
- [Engineering](engineering/README.md): perturbations, meshes, loads and model limitations.
- [Validation](validation/README.md): portable entry points, scientific evidence, environment and review.
- [SQuID-C / Proxima comparison](squid_c/README.md): future intake, readiness limits and the MS1 evidence framework.
- [Research log](logbook/README.md): decisions, findings, actual checks and preserved failures.

Persistent working instructions: [AGENTS.md](../AGENTS.md). Historical evidence is
immutable; new portable derivatives have their own schemas and provenance.
