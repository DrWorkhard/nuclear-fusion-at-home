# Scientific status and evidence

Updated 26 September 2026.
[Overview](README.md) · [Roadmap](PROJECT_PLAN.md) · [Step results](steps/README.md)

## Bottom line

We can reproduce selected references, iterate designs and verify a local
vacuum-plasma improvement. **We have no newly accepted coil design, completed
Step 4, state-of-the-art advantage or MS1 result.** The immediate task is to
calibrate the coil comparison and map achievable field/geometry trade-offs,
not extrapolate small local gains.

## Established results and their limits

| Work | Scientific result | Limit |
| --- | --- | --- |
| [Steps 1–2](validation/FOUNDATION_ACCEPTANCE_RESULTS.md) | Selected W7-X/Goodman references and repeatable local design/evaluation workflows pass their defined checks | Workflow capability, not a new feasible design; broader W7-X file comparison remains 60/63 |
| [Step 3](steps/STEP_3_PLASMA_TARGET.md) | Vacuum bounce-action variance decreases 11.17%; the registered narrower-domain comparison improves 4.85% | One proxy and configuration; not measured confinement, finite pressure, global QI or reactor performance |
| [Step 4 coil starts](geometry/CLEAR_COIL_INITIALIZATION_RESULTS.md) | Twelve starting sets pass scoped continuous geometry checks; selected plasma clearance is at least 98.2 mm versus 80 mm required | Padded floating-point bounds, not rigorous interval proofs or finite-build engineering |
| [Protected fit and fine checks](optimization/PROTECTED_FINE_RESULTS.md) | Eight fixed selections pass numerical/geometry checks; fine normal RMS remains 0.26794–0.27478 | Every selection fails field-quality gates; a certified geometric path does not ensure a useful magnetic field |
| [Newly certified fixed steps](optimization/FIXED_FIELD_PROBE_RESULTS.md) | Normal RMS decreases another 0.057%/0.065% beyond preset empirical margins; both currents decrease; one interior-error improvement resolves | Other interior gain unresolved; all absolute field-error gates still fail; no general search-method advantage |
| [Gate calibration](optimization/STEP4_RESEARCH_PROGRAMME.md) | Analytic/component controls exist; no matched end-to-end positive control has established that a known-good coil design passes this Step 4 profile | Pilot limits are not universal standards; archived LPQA raw-flux failures are a different comparison |

The current normal-RMS limit is **1e-4**, maximum normal error **1e-3** and
interior-vector RMS **0.01**. The roughly 2,700-fold normal-error gap is real;
its cause and reachability remain unresolved. No threshold has been relaxed.

## Negative results and independence

The [first actual-coil pilot](optimization/COUPLED_COIL_PILOT_RESULTS.md) was
rejected, including fine clearances of only 1.8–6.7 mm. Older
[LPQA searches](optimization/CURRENT_START_GN_RESULTS.md) also remain rejected
under their own raw-flux profile. Failed numerical controls and revised claims
remain in the relevant result reports and evidence; current lessons are in the
[research notes](logbook/README.md). Git retains superseded assessments.

Here, independent numerical checking means separate specified calculations,
usually on the same machine. No external domain-expert review or separate-machine
research reproduction is established. Backup/restore status is unverified.
[SQuID-C readiness](squid_c/SQUID_C_READINESS.md) still requires physics and
engineering qualification as well as suitable data.

Software tests and release checks are recorded in
[Step 4 methods](steps/STEP_4_PLASMA_AND_COILS.md#tools-and-detailed-evidence) and
[release evidence](validation/PUBLIC_RELEASE_RESULTS.md), not counted as new
scientific results. Hosting, CI, artifact publication and contributor growth
are pending operational work. The [research programme](optimization/STEP4_RESEARCH_PROGRAMME.md)
defines decision dates and indicators.
