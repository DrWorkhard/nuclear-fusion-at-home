# Scientific status

Updated 4 October 2026; no new scientific result.
[Roadmap](PROJECT_PLAN.md) · [Step conclusions](steps/README.md)

**No accepted coil design or demonstrated reactor advantage.** The best
geometry-checked fit has boundary RMS **0.001996**, about **20×** its limit,
and interior RMS **0.01148**, also failing. All coil fits use reference401;
transfer of the improved Step 3 target is untested. Present evidence does not
substantiate the README's reactor-design timeline.

## Established results and their limits

Links below lead to original evidence or the completed-step summary.

| Work | Result | Limit |
| --- | --- | --- |
| [Steps 1–2](steps/README.md#steps-1-and-2-foundation-and-repeatable-iteration) | Selected references and repeatable independent iteration checks pass | Capability, not design success; broader W7-X comparison 60/63 |
| [Step 3](steps/README.md#step-3-vacuum-plasma-diagnostic) | Vacuum bounce-action variance improves 11.17% wide / 4.85% narrow | Both domains informed construction; not confinement or power |
| [Boundary calibration](../evidence/boundary-control-calibration-v1.json) | QUASR refined RMS 2.27e-6; LPQA mean/max reproduced | Boundary component only; coarse-grid near-zero error misleads |
| [Matched restart](../evidence/coherent-restart-v1.json) | RMS 0.004889, 55.27% lower, 8.64% less current; scoped geometry passes | Both 1,200-bundle budgets exhausted; boundary fails |
| [Interior screen](../evidence/coherent-interior-v1.json) | Best RMS 0.04029, 73.66% below matched control | All five snapshots fail 0.01 |
| [Longer/wider fits](../evidence/coherent-longrun-v2.json) | Wider boundary/interior RMS 0.001948 / 0.009770 | Interior passes; length bounds unresolved; boundary fails |
| [Length headroom](../evidence/coil-headroom-v3.json) | Boundary/interior RMS 0.001996 / 0.01148; length bound 3.474220 m | Geometry passes; fields fail; expanded box gains only 2.64% boundary RMS |
| [Earlier failures](validation/REPRODUCING_RESULTS.md) | Fine clearance, objective alignment and current-only studies exposed limitations | Remain failures; no retired method is relabelled successful |

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

Independent numerical checks generally mean separate calculations on the same
machine. [Ubuntu public replay](validation/SERVER_REPRODUCTION_20261002.md) provides
portability evidence. External physics review, native research reproduction,
backup/restore and complete-history rights clearance remain open.
[Software checks](logbook/VALIDATION_LOG.md) · [Hosting/review policy](validation/REVIEW_POLICY.md).
