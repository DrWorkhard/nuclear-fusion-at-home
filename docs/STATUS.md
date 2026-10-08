# Scientific status

Updated 8 October 2026; fifteen study archives are published with remote tag/commit
identities and manifest retrieval verified. The #66 retention archive remains local
pending redistribution review; publication does not change scientific qualification.
[Roadmap](PROJECT_PLAN.md) · [Step conclusions](steps/README.md)

**No accepted coil design or demonstrated reactor advantage.** The new matched
reference-target fit reaches boundary RMS **0.001932**, about **19×** its limit,
and interior RMS **0.01072**, also failing. The improved-target fit also fails.
[Matched-target evidence](optimization/ISSUE25_MATCHED_TARGETS.md) finds incomplete
wide-domain action diagnostics in both actual coil fields; benefit transfer remains unresolved.
The [original paired label grid](optimization/ISSUE48_FULL_GRID.md) qualifies
20/20 reference launches and 18/20 improved-target launches; its paired map fails.
The local [shallow-well comparison](optimization/ISSUE26_INTERIOR_WELLS.md) recovers
both reference core cells with a lower-interior-error candidate (35/35 screened
cells). Its [label grid](optimization/ISSUE48_CONTINUATION_LABELS.md) qualifies
19/20 points; the full grid remains unqualified.
[Saved-point diagnosis](optimization/ISSUE48_CONTINUATION_RECURRENCE.md) finds
angular reversals in the failed trace. Topology and benefit transfer remain unknown.
**The next research route is joint plasma/coil optimization.** The local
[coil-freedom probe](optimization/ISSUE53_COIL_FREEDOM.md) lowers boundary RMS by
3.78%, missing its 50% hurdle. Its interior RMS passes its individual limit, but
both boundary gates fail. Clock/load limitations prevent controlled-throughput
or causal/global claims. Present evidence does not substantiate the README's
reactor-design timeline.

## Established results and their limits

Full records are preserved at [evidence-archive-2026-10-04](https://github.com/DrWorkhard/nuclear-fusion-at-home/tree/evidence-archive-2026-10-04),
archive commit [`68db098`](https://github.com/DrWorkhard/nuclear-fusion-at-home/commit/68db098b664bb072854b687040e103aaafee463c). Links below pin those original
bytes; source revisions identify each study's producer, not the archive date.
The [archive workflow](validation/REPRODUCING_RESULTS.md) explains retrieval.

| Work | Result | Limit | Source state |
| --- | --- | --- | --- |
| [Steps 1–2](steps/README.md#steps-1-and-2-foundation-and-repeatable-iteration) | Selected references and repeatable independent iteration checks pass | Capability, not design success; broader W7-X comparison 60/63 | [`1aa28b6`](https://github.com/DrWorkhard/nuclear-fusion-at-home/commit/1aa28b6b9b30e7724f58134c813f71a7eb4c4f4a) |
| [Step 3](steps/README.md#step-3-vacuum-plasma-diagnostic) | Vacuum bounce-action variance improves 11.17% wide / 4.85% narrow | Both domains informed construction; not confinement or power | [`f285fbdf`](https://github.com/DrWorkhard/nuclear-fusion-at-home/commit/f285fbdf0eb21cea060a2f34c391da901a8dad35) (dirty; verify code hashes) |
| [Boundary calibration](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/68db098b664bb072854b687040e103aaafee463c/evidence/boundary-control-calibration-v1.json) | QUASR refined RMS 2.27e-6; LPQA mean/max reproduced | Boundary component only; coarse-grid near-zero error misleads | [`9270692`](https://github.com/DrWorkhard/nuclear-fusion-at-home/commit/9270692b77846869dab5b0c602878766d912fad6) (dirty; verify code hashes) |
| [Matched restart](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/68db098b664bb072854b687040e103aaafee463c/evidence/coherent-restart-v1.json) | RMS 0.004889, 55.27% lower, 8.64% less current; scoped geometry passes | Both 1,200-bundle budgets exhausted; boundary fails | [`c1fdddf`](https://github.com/DrWorkhard/nuclear-fusion-at-home/commit/c1fdddf122268f60ff3f7c3e5e1f879238f77a2c) |
| [Interior screen](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/68db098b664bb072854b687040e103aaafee463c/evidence/coherent-interior-v1.json) | Best RMS 0.04029, 73.66% below matched control | All five snapshots fail 0.01 | [`8fae8b0`](https://github.com/DrWorkhard/nuclear-fusion-at-home/commit/8fae8b0f9478ebb64873e4608bbd2fb0597c6a4f) |
| [Longer/wider fits](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/68db098b664bb072854b687040e103aaafee463c/evidence/coherent-longrun-v2.json) | Wider boundary/interior RMS 0.001948 / 0.009770 | Interior passes; length bounds unresolved; boundary fails | [`eb458ef`](https://github.com/DrWorkhard/nuclear-fusion-at-home/commit/eb458ef84c4495cd091495f4d69a25ebbcb5aee1) |
| [Length headroom](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/68db098b664bb072854b687040e103aaafee463c/evidence/coil-headroom-v3.json) | Boundary/interior RMS 0.001996 / 0.01148; length bound 3.474220 m | Geometry passes; fields fail; expanded box gains only 2.64% boundary RMS | [`5a3c1d0`](https://github.com/DrWorkhard/nuclear-fusion-at-home/commit/5a3c1d02f90746b9fd061d1174fa02f9e58784d6) |
| [Earlier failures](validation/REPRODUCING_RESULTS.md) | Fine clearance, objective alignment and current-only studies exposed limitations | Remain failures; no retired method is relabelled successful | Per archived record |

Acceptance still requires boundary RMS **1e-4**, maximum normal error **1e-3**
and interior RMS **0.01**, plus the [Step 4 requirements](steps/STEP_4_PLASMA_AND_COILS.md).
Geometry bounds use padded floating point, not interval proofs or finite-build
engineering. Solver stopping does not prove an optimum.

## Reproduce or contribute

The [best portable geometry](../submissions/length-headroom-six-coil/README.md)
is available; public sparse and dense diagnostics are not physical acceptance.
Use [historical revisions](validation/REPRODUCING_RESULTS.md) for full methods,
budgets and failure records. Evidence and raw artifacts retain their identities;
Git does not back up ignored data.

The local [dense interior checker](validation/ISSUE10_DENSE_INTERIOR.md) reproduces
both frozen targets; checks share one machine.
[Ubuntu public replay](validation/SERVER_REPRODUCTION_20261002.md) provides
portability evidence. External physics review, native research reproduction,
backup/restore and complete-history rights clearance remain open.
[Software checks](logbook/VALIDATION_LOG.md) · [Hosting/review policy](validation/REVIEW_POLICY.md).
