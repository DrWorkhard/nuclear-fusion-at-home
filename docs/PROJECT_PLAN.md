# Roadmap and completion criteria

Updated 26 September 2026.
[Overview](README.md) · [Status](STATUS.md) · [Step results](steps/README.md) · [Contribution guide](../CONTRIBUTING.md)

What each step and milestone requires, and what comes next. Each step's results
are in its [step results page](steps/README.md); the overall evidence is on the
[status page](STATUS.md).

## Roadmap

Stellarator plasma/coil optimization is our current route toward the end goal (MSX).

| Step / milestone | Completion requires | Status | Results |
| --- | --- | --- | --- |
| 1. Establish a reliable foundation | Specified local reference, software and physics checks with source and environment identity, and honest acceptance and rejection; no new design required | Complete (local reference tools) | [Step 1](steps/STEP_1_FOUNDATION.md) |
| 2. Make design iteration reproducible | Load a reference → change/optimize → save → independently evaluate → repeat, exactly reproducibly; no new design required | Complete (iteration workflow) | [Step 2](steps/STEP_2_ITERATION.md) |
| 3. Improve our own plasma target | An actual boundary/equilibrium change with a registered, independently confirmed improvement | Complete (vacuum study) | [Step 3](steps/STEP_3_PLASMA_TARGET.md) |
| 4. Develop plasma and coils together | Work packages 4A–4D; a favorable vacuum coil fit alone is not enough | In progress | [Step 4 so far](steps/STEP_4_PLASMA_AND_COILS.md) |
| 5. Demonstrate a meaningful design advantage | Fair, reproducible comparisons with leading references and an independently verified, meaningful advantage | Not achieved | No results yet |
| MS1. Contact Proxima Fusion with strong evidence | A targeted Step 5 outcome: strong, reproducible, independently checked evidence that our design is better than the design Proxima is pursuing; then contact them | Not reached | [Evidence framework](squid_c/MS1_PROXIMA_COMPARISON.md) |
| MSX. Our end goal | Contribute to nuclear fusion for humanity by finding the best reactor design current technology can achieve | Long-term goal | — |

## Next actions

**Public release, alongside local research.** Goal: an outside contributor can start from a fresh
checkout, reproduce a small reference, evaluate a candidate, replay the report and
submit useful work without our local artifacts or chat history
([release specification](validation/PUBLIC_RELEASE.md)). The portable starter and
its local checks are done. Remaining before launch: a privacy and rights review of
the full history, the real clone URL, hosted CI, reviewer identities and branch
protection — see the [launch checklist](validation/REVIEW_POLICY.md#launch-checklist--requires-actual-hosting-work)
and the [publication inventory](validation/PUBLICATION_INVENTORY.md).

**Step 4A: local research resumed with the user's authorization.** Publication
remains separate; all scientific preflight gates still apply. The
[geometry-protected field-fit draft](optimization/PROTECTED_COIL_FIT_PROTOCOL.md)
is one possible next experiment, not a required method or an exclusive work
allocation. Its controller is qualified and its
[event storage](optimization/PROTECTED_RUNNER_STORAGE_RESULTS.md) is qualified.
The [source admission, raw snapshots, budget ledger and startup helpers](optimization/PROTECTED_RUNNER_RESULTS.md)
are now qualified separately. Their [integrated synthetic worker and graph audit](optimization/PROTECTED_CELL_RESULTS.md)
are now qualified in their synthetic scope. The
[source-bound native adapter and isolated process/resource orchestration](optimization/PROTECTED_NATIVE_PLUMBING_RESULTS.md)
also pass synthetic and read-only source qualification. Next: qualify
[independent saved-physics reconstruction](optimization/PROTECTED_PHYSICS_PROTOCOL.md),
then bind the execution checkpoint and run the registered diagnostic pilot. The
[second method review](optimization/PROTECTED_METHOD_REVIEW.md) supports a bounded
diagnostic pilot conditionally; its replay and claim-scope clarifications apply
before any native run.
Finer-grid acceptance remains a separate required phase.
