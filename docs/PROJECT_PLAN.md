# Roadmap and completion criteria

Updated 8 October 2026.
[Overview](README.md) · [Status](STATUS.md) · [Step results](steps/README.md)

## Roadmap

Stellarator plasma/coil design is our current route toward MSX. Completed steps
cover their stated local scope, not a complete reactor.

| Step / milestone | Completion requires | Status |
| --- | --- | --- |
| 1. Establish a reliable foundation | Reproduce selected references and correctly accept/reject candidates. | Complete (local reference tools) |
| 2. Make design iteration reproducible | Change, save, independently evaluate and repeat a real iteration. | Complete (iteration workflow) |
| 3. Improve our own plasma target | Confirm the registered vacuum diagnostic improvement. | Complete (vacuum study) |
| 4. Develop plasma and coils together | Realize and preserve plasma benefits with practical coils; [requirements](steps/STEP_4_PLASMA_AND_COILS.md). | In progress |
| 5. Demonstrate a meaningful design advantage | Verify practical benefit against leading matched references. | Not achieved |
| MS0. Publish a useful open coil benchmark | Attributed challenge, calibrated checks and separate-machine reproduction. | Planned |
| MS1. Contact Proxima Fusion with strong evidence | Show our design is better than their relevant design, then contact them. | Not reached |
| MSX. Our end goal | Make nuclear fusion happen in 2030 for humanity through the best reactor design current technology can build, with power output comparable to today's nuclear plants. | Aspirational 2030 goal |

MS1 needs a versioned Proxima reference, matched conditions and independently
checked reproducible benefits. Improving our own seed is insufficient. MSX's
2030 target is aspirational, not a validated delivery schedule or a claimed
global optimum. It does not relax scientific or engineering acceptance.
[Future comparison](squid_c/README.md).

Proposed [early feedback (#29)](review/ISSUE29_FEEDBACK_PACKET.md): permissioned
technical review before MS1, preserving its evidence requirements. Adoption and
outreach remain pending.

## Current priorities

The [assessment](review/STRATEGIC_REVIEW_RESOLUTION.md) finds no demonstrated path
from present results to the README's reactor vision. Keep the ambition;
spend effort on decisions that test the path.

1. **Test benefit in actual coil fields.** Compare the original and improved
   Step 3 targets with matched fitting effort and evaluate interior fields,
   magnetic surfaces and benefit transfer using shared checks. The [first matched comparison](optimization/ISSUE25_MATCHED_TARGETS.md)
   leaves wide-domain benefit transfer unresolved because required wells are missing.
   The [paired label grid](optimization/ISSUE48_FULL_GRID.md) remains unqualified.
   A [lower-error continuation](optimization/ISSUE26_INTERIOR_WELLS.md) restores
   missing wells, but its [19/20 label grid](optimization/ISSUE48_CONTINUATION_LABELS.md)
   also fails. The [local diagnosis](optimization/ISSUE48_BOUNDED_RETURN.md)
   ends without resolving that contour. Require a qualified realized-coordinate
   construction before launch matching; further local solver variants need a new
   decision-relevant reason. Test interior fidelity in joint optimization.
2. **Screen reactor feasibility now.** Expose assumptions and unknowns about
   power balance, pressure/confinement, magnets, blanket/shield space and heat
   exhaust before expensive optimization. The [conditional space screen](engineering/ISSUE27_ENVELOPE_SCREEN.md)
   excludes some scaled copies; it supplies no operating point. Detailed modelling
   follows a decision need.
3. **Pilot joint plasma/coil optimization.** The completed
   [coil-freedom probes](optimization/ISSUE53_COIL_FREEDOM.md) missed their hurdle.
   Preregister the bounded feasibility pilot (#37/#59/#63), use the existing
   optimizer work (#39) and record costs/plasma variables (#64). Qualify
   derivatives and realized-field endpoints before their respective claims;
   do not extend the completed probes.
4. **Make the decisive test portable.** The published
   [dense target packet](validation/ISSUE10_DENSE_INTERIOR.md) passes numerical qualification.
   Reuse its shared field/geometry checks; prefer a community benchmark.

   26 March 2027 is the outer MS0 decision target, not a six-month tooling project.

One method, shared checks, one short record per question.
[Active scope and workflows](review/ACTIVE_SCOPE.md) identify the code required. Maintain only code
needed for active work or reproduction; completed tools resolve at their recorded
Git revisions. Preserve evidence and raw data. Existing acceptance limits remain
unchanged. Dates allocate effort; they do not promise scientific success.
Unsolicited alternatives remain welcome. Publishing/contact need separate authority.
