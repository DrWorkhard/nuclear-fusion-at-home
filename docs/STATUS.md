# Scientific status and evidence

Updated 27 September 2026.
[Overview](README.md) · [Roadmap](PROJECT_PLAN.md) · [Step results](steps/README.md)

## Bottom line

We can reproduce selected references, iterate designs and verify a local
vacuum-plasma improvement. Our best geometry-checked exploratory coil fit reaches
normal-field RMS **0.001996**, about **20× the 1e-4 limit**, with interior RMS
**0.01148**, still above 0.01. Step 4 remains in
progress: there is no accepted new coil design, demonstrated state-of-the-art
advantage or MS1 result.

## Established results and their limits

| Work | Result | Limit |
| --- | --- | --- |
| [Steps 1–2](steps/README.md) | Selected reference calculations and repeatable independently evaluated iteration pass their defined checks | Capability, not a new feasible design; broader W7-X comparison remains 60/63 |
| [Step 3](steps/STEP_3_PLASMA_TARGET.md) | Vacuum bounce-action variance falls 11.17%; the narrower-domain comparison improves 4.85% | One diagnostic/configuration, not measured confinement, pressure or reactor performance |
| [Boundary calibration](optimization/REFERENCE_CALIBRATION.md) | QUASR 952 refined RMS is 2.27e-6; LPQA mean/max reproduce on the tested half-period grid | Boundary-component control, not an end-to-end Goodman positive; coarse sampling misleads |
| [Matched coil restart](optimization/COHERENT_COIL_EXPLORATION.md) | Wider low modes reach RMS 0.004889, 55.27% below the original-box control, at 8.64% less current; both endpoints pass scoped continuous geometry | Both 1,200-bundle caps exhausted; boundary limits fail |
| [Interior fields](optimization/INTERIOR_FIELD_EXPLORATION.md) | Best snapshot reaches vector RMS 0.04029, 73.66% below its matched control; all fifteen numerical rows pass | All five candidates fail the 0.01 interior limit; topology and Step 3 benefit transfer remain open |
| [Longer/wider fits](optimization/LONGER_COIL_EXPLORATION.md) | Same-box RMS 0.004713 passes scoped geometry; wider RMS 0.001948 has interior RMS 0.009770, passing that component | Wider length upper bounds unresolved; both boundary gates still fail, no topology/benefit transfer |
| [Length headroom](optimization/LENGTH_HEADROOM_EXPLORATION.md) | Expanded-box boundary RMS 0.001996 with scoped geometry passing; length upper bound 3.474220 m; portable candidate available | Interior RMS 0.01148 and both boundary gates fail; solver stopping is not physical acceptance |
| [Earlier negative studies](validation/REPRODUCING_RESULTS.md) | Exposed missed fine clearances, poorly aligned objectives and limited current-only gains | Closed methods are frozen, not converted into successful designs |

Current limits remain normal RMS **1e-4**, maximum normal error **1e-3** and
interior-vector RMS **0.01**. Meeting the **1e-2 exploratory signal** justifies
further investigation, not acceptance. Geometry checks use padded floating-point
bounds; they are neither interval proofs nor finite-build engineering models.

## Reproducibility and remaining work

The active repository now concentrates on normalized coil fitting and shared
checks. Closed code, tests and detailed reports resolve at the
[freeze tag](validation/REPRODUCING_RESULTS.md); tracked scientific evidence and
local raw artifacts retain their identities. Git does not back up ignored data.

Independent numerical checks here usually mean separately specified calculations
on the same machine. External domain-expert review, separate-machine research
reproduction and backup/restore verification are not established.
[Step 4](steps/STEP_4_PLASMA_AND_COILS.md) retains all unfinished physical
requirements; [SQuID-C comparison](squid_c/README.md) needs more than suitable data.

Latest software checks belong in [current verification](logbook/VALIDATION_LOG.md),
not the scientific result tally. Historical public qualifications are in
[release evidence](validation/PUBLIC_RELEASE_RESULTS.md). Hosting, hosted CI and
publication clearance remain pending.
