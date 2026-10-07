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
   Diagnose shallow-well fidelity and qualify realized flux labels before confirmation.
2. **Screen reactor feasibility now.** Expose assumptions and unknowns about
   power balance, pressure/confinement, magnets, blanket/shield space and heat
   exhaust before expensive optimization. Detailed simulations follow a decision
   need; boundary RMS alone does not determine their priority.
3. **Move to joint plasma/coil optimization.** The completed local
   [coil-freedom probe](optimization/ISSUE53_COIL_FREEDOM.md) missed its hurdle;
   the [programme](optimization/STEP4_RESEARCH_PROGRAMME.md) now calls for a bounded
   joint feasibility protocol ([#37](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/37)).
   Its [first local attempt](optimization/ISSUE37_JOINT_RESULT.md) was interrupted by
   host clock disagreement; the [awake follow-up](optimization/ISSUE37_AWAKE_RESULT.md)
   completed but missed the ideal-gain hurdle. The registered
   [smaller-step screen](optimization/ISSUE37_STEP_SCALE_RESULT.md) reduces training
   score 3.22%. Validate this fixed point's phase/resolution behavior before another
   coil comparison. Preserve previous verdicts and gates; register validation first.
   Qualify a common realized-field endpoint before claiming benefit; missing
   surfaces or wells restrict the next pilot to feasibility.
4. **Make the decisive test portable.** Supply the missing target data and reuse
   existing field/geometry checks so contributors can address the actual
   bottleneck. Prefer an existing community benchmark. Aim to resolve this now;
   26 March 2027 is the outer MS0 decision target, not a six-month tooling project.

One method, shared checks, one short record per question.
[Active scope and workflows](review/ACTIVE_SCOPE.md) identify the code required. Maintain only code
needed for active work or reproduction; completed tools resolve at their recorded
Git revisions. Preserve evidence and raw data. Existing acceptance limits remain
unchanged. Dates allocate effort; they do not promise scientific success.
Unsolicited alternatives remain welcome. Publishing/contact need separate authority.
