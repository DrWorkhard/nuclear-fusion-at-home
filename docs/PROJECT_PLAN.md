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

**Step 4A: continue useful movement and diagnose the large field mismatch.** Publication remains
separate. The [eight-case native pilot](optimization/PROTECTED_COIL_FIT_RESULTS.md) completes
construction and independent coarse verification at `2015ac5`. Every case makes
small field-error reductions, then stops at the cumulative curvature bound.
The [complete fine study](optimization/PROTECTED_FINE_RESULTS.md) now passes
numerical and geometry checks for all eight fixed selections; every candidate
still fails field-quality limits. Its software has 4,883 passing full-regression
tests. The separate [local homotopy curvature study](geometry/LOCAL_CURVATURE_RESULTS.md)
now certifies all twelve fixed states, including two previously rejected proposals,
with independent checking and unchanged limits. Its full regression passes 5,110
tests. The [matched-grid field comparison](optimization/FIXED_FIELD_PROBE_PROTOCOL.md)
now [completes all 168 requests](optimization/FIXED_FIELD_PROBE_RESULTS.md) at clean
`4f13685`. Both normal gains resolve under preset empirical margins; only the
six-coil interior gain resolves. Currents decrease, but all absolute field limits
still fail. Its [implementation and independent
reviews](optimization/FIXED_FIELD_PROBE_PROGRESS.md) pass 544 focused and 5,654
full-regression tests at clean `b10c47f`. Next: a separately registered one-step
normal-objective continuation with geometry protection and gradient checks,
alongside saved-field diagnosis of the roughly 2,700-fold normal-error gap.
Do not extrapolate tiny local gains to feasibility or reset the geometry origin.
The
[second method review](optimization/PROTECTED_METHOD_REVIEW.md) defines the reporting
limits: small coarse gains do not establish resolved fine-grid improvement.
Other useful approaches remain welcome; this pilot is not an exclusive work allocation.
