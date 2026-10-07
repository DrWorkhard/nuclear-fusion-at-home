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
to the README's year-end reactor vision. Prioritize decisions that test it.

1. **Test benefit in actual coil fields.** Compare the original and improved
   Step 3 targets with matched fitting effort and evaluate interior fields,
   magnetic surfaces and benefit transfer using shared checks. The [first matched comparison](optimization/ISSUE25_MATCHED_TARGETS.md)
   leaves wide-domain benefit transfer unresolved because required wells are missing.
   Diagnose shallow-well fidelity and qualify realized flux labels before confirmation.
2. **Screen reactor feasibility now.** The [conditional envelope screen](engineering/ISSUE27_ENVELOPE_SCREEN.md)
   rejects some scaled scenarios; a coupled operating point remains missing.
   Specify power balance, pressure/confinement, magnet, shielding and exhaust
   assumptions before reactor-scale optimization.
3. **Move to joint plasma/coil optimization.** The completed local
   [coil-freedom probe](optimization/ISSUE53_COIL_FREEDOM.md) missed its hurdle;
   the [programme](optimization/STEP4_RESEARCH_PROGRAMME.md) now calls for a bounded
   joint feasibility protocol ([#37](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/37)).
   Its [first attempt](optimization/ISSUE37_JOINT_RESULT.md) stopped on clock disagreement;
   the [awake follow-up](optimization/ISSUE37_AWAKE_RESULT.md) missed the ideal-gain hurdle.
   [Smaller-step validation](optimization/ISSUE37_STEP_VALIDATION_RESULT.md)
   retains a 3.258% ideal gain. The [paired fitting screen](optimization/ISSUE37_FIT_COUPLING_RESULT.md)
   passes nonregression; absolute field errors fail. The
   [fixed-coil surface test](optimization/ISSUE37_BOUNDARY_RESPONSE.md) gains only 1.394% RMS
   and worsens peak error/flux. Retain the validated target; moving-coil optimization
   remains untested. Preserve gates; no automatic fit extensions or expensive diagnostics.
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
