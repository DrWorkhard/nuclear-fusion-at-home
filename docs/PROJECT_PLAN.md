# Roadmap and completion criteria

Updated 27 September 2026.
[Overview](README.md) · [Status](STATUS.md) · [Step results](steps/README.md)

## Roadmap

Stellarator plasma/coil design is our current route toward MSX. MS0 creates a
useful open result before a possible reactor-design advantage.

| Step / milestone | Completion requires | Status | Results |
| --- | --- | --- | --- |
| 1. Establish a reliable foundation | Reproduce selected references and accept/reject correctly; no new design required | Complete (local reference tools) | [Step 1](steps/STEP_1_FOUNDATION.md) |
| 2. Make design iteration reproducible | Change, save, independently evaluate and repeat; no new design required | Complete (iteration workflow) | [Step 2](steps/STEP_2_ITERATION.md) |
| 3. Improve our own plasma target | Independently confirm a registered boundary/equilibrium improvement | Complete (vacuum study) | [Step 3](steps/STEP_3_PLASMA_TARGET.md) |
| 4. Develop plasma and coils together | Realization/transfer, coupled improvement, pressure/confinement and finite-coil robustness (4A–4D) | In progress | [Step 4](steps/STEP_4_PLASMA_AND_COILS.md) |
| 5. Demonstrate a meaningful design advantage | Fair leading-reference comparison and independently verified practical benefit | Not achieved | — |
| MS0. Publish a useful open coil benchmark | Portable attributed challenge, calibrated gate interpretation, control matrix and separate-machine reproduction; target 26 March 2027 | Planned | [Programme](optimization/STEP4_RESEARCH_PROGRAMME.md) |
| MS1. Contact Proxima Fusion with strong evidence | Strong reproducible evidence that our design is better than Proxima's relevant design; then contact them | Not reached | [Evidence framework](squid_c/MS1_PROXIMA_COMPARISON.md) |
| MSX. Our end goal | Contribute to nuclear fusion for humanity by finding the best reactor design current technology can achieve | Long-term goal | — |

## Next actions

**Calibration checkpoint, by 10 October.** The [saved-field diagnosis](optimization/FIELD_RESIDUAL_RESULTS.md)
and [boundary-reference comparison](optimization/REFERENCE_CALIBRATION.md) are
complete: one boundary-positive control and reproduced LPQA mean/max conventions,
but no end-to-end Goodman control. Keep the remaining model/geometry distinctions
explicit; no automatic threshold relaxation.

**Then: time-boxed exploration, through 24 October or ten research sessions.**
Map field error against clearance/curvature using existing tools and alternative
starts/objectives. The [objective comparison](optimization/NORMALIZED_OBJECTIVE_EXPLORATION.md)
improves field error only with geometry violations. [Constraint-aware fitting](optimization/CONSTRAINED_COIL_EXPLORATION.md)
now gives a geometry-checked adaptive fit at RMS 0.1517 with higher current; better
sampled fits have unresolved clearance. Normalized current-only fits help modestly.
The paired shape test stopped at its derivative guard; diagnose its scale before retry.
Fine RMS below 1e-2 with geometric gates is a
triage signal, not acceptance. If it is not reached, change the investigated
family/approach instead of automatically extending protected local search.
The [programme](optimization/STEP4_RESEARCH_PROGRAMME.md) defines scope,
decision rules, controls and retained negatives.

**Alongside: make the bottleneck contributable.** Target a portable full-grid
Step 4 challenge and four issue-ready tasks by 26 October; preserve the small
starter as the entry path. Stage a privacy/rights-cleared release, verified
hosted CI and an independent reproduction. Hosting, contact, storage destination
and archive publication still require the owner's authority; no external action
is implied by this plan. Follow the [launch checklist](validation/REVIEW_POLICY.md#launch-checklist--requires-actual-hosting-work).

Use the [two-lane workflow](validation/RESEARCH_WORKFLOW.md): lightweight,
clearly labelled exploration; preregistered independent confirmation for claims.
Dates are decision targets, not promises of scientific success. MS0 can deliver
a useful negative benchmark; it does not replace Step 4, MS1 or MSX.
