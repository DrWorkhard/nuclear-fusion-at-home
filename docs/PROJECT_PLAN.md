# Roadmap and completion criteria

Updated 7 October 2026.
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

## Current priorities

The [assessment](review/STRATEGIC_REVIEW_RESOLUTION.md) finds no demonstrated path
from present results to the README's year-end reactor vision. Keep the ambition;
spend effort on decisions that test the path.

1. **Test benefit in actual coil fields.** Compare the original and improved
   Step 3 targets with matched fitting effort and evaluate interior fields,
   magnetic surfaces and benefit transfer using shared checks. The [first matched comparison](optimization/ISSUE25_MATCHED_TARGETS.md)
   leaves wide-domain benefit transfer unresolved because required wells are missing.
   A local [comparison](optimization/ISSUE26_INTERIOR_WELLS.md) restores the missing
   reference wells with lower interior error. Test interior fidelity in joint
   optimization and qualify realized flux labels before confirmation.
2. **Screen reactor feasibility now.** Expose assumptions and unknowns about
   power balance, pressure/confinement, magnets, blanket/shield space and heat
   exhaust before expensive optimization. Detailed simulations follow a decision
   need; boundary RMS alone does not determine their priority.
3. **Choose the next route by 24 October.** The fixed-target recipe has stalled
   ([decision](optimization/STEP4_RESEARCH_PROGRAMME.md)). After a fitter fix
   ([#52](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/52)), one coil-freedom probe ([#53](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/53)) chooses between a
   richer coil family and joint plasma/coil optimization ([#36](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/36)).
4. **Make the decisive test portable.** The local
   [dense target packet](validation/ISSUE10_DENSE_INTERIOR.md) passes numerical qualification.
   Publish it and reuse shared field/geometry checks; prefer a community benchmark.
   Aim to resolve this now;
   26 March 2027 is the outer MS0 decision target, not a six-month tooling project.

One method, shared checks, one short record per question.
[Active scope and workflows](review/ACTIVE_SCOPE.md) identify the code required. Maintain only code
needed for active work or reproduction; completed tools resolve at their recorded
Git revisions. Preserve evidence and raw data. Existing acceptance limits remain
unchanged. Dates allocate effort; they do not promise scientific success.
Unsolicited alternatives remain welcome. Publishing/contact need separate authority.
