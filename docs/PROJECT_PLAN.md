# Roadmap and completion criteria

Updated 2 October 2026.
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

1. **Simplification implemented.** Closed code/tests/reports now resolve at
   `research-freeze-2026-09-27`. The working normalized coil fit, shared
   checks and public starter remain. [Reproduction](validation/REPRODUCING_RESULTS.md).
2. **Map the working fit's trade-offs.** Construction headroom resolves length
   bounds but sacrifices the interior component pass. Wider boxes now give only
   modest gains, with no active coefficient bounds. Inspect stopping/conditioning
   before further extension; explore separately labelled coil
   families. Check the best two or three with the shared fine evaluator and
   continuous geometry. Acceptance limits stay unchanged.
3. **Decide on 24 October.** The 1e-2 exploratory signal is met, but interior
   fidelity and benefit transfer remain open. Use the
   [programme](optimization/STEP4_RESEARCH_PROGRAMME.md) to decide what merits
   further work, not to declare success from a boundary score.
4. **Deliver something reusable toward MS0**, targeted for 26 March 2027.
   Assess contribution to existing community benchmarks first. The present
   sparse starter is not yet a portable full-grid challenge.

Pressure, detailed engineering and SQuID-C intake are deferred until a coil set
is within 10× of the field limit; they remain necessary for later completion.
Exploration uses [short records and proportionate checks](validation/RESEARCH_WORKFLOW.md).
Dates are decision targets, not promises of scientific success. The repository is
public on [GitHub](https://github.com/DrWorkhard/nuclear-fusion-at-home) since 2 October 2026; contact and artifact
publication need separate authorization. The
[launch checklist](validation/REVIEW_POLICY.md#launch-checklist--requires-actual-hosting-work)
records the remaining operational prerequisites.
