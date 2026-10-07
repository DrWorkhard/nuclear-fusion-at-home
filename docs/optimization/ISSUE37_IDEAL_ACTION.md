# Registered ideal-target action scoring

Component qualification registered on 7 October 2026. The decision is whether
the [joint feasibility protocol](ISSUE37_JOINT_FEASIBILITY.md) has a usable,
complete ideal-plasma selection score and separate held-out phase check before
integrating the full comparison. Reuse `vmec_trace.trace_geometry` and the frozen
`coil_bounce.period_actions` kernel. This measures ideal-target action variance;
the common actual-coil physics endpoint remains null.

`joint_action` requires exact original-reference intake or the trusted new-target
solver receipt. Training uses 801 toroidal samples, 16 equally spaced phases
starting at zero, two field periods, all five registered surfaces and all seven
fixed physical bounce pitches. Each phase must have exactly two complete wells,
each contained in its registered period. Missing, extra, censored or crossing
wells make the entire score ineligible. Save complete trace arrays and every
failed pitch's wells on every phase; never average a reduced domain. Structural
errors, generic exceptions and resource interruptions propagate as failures.

The held-out phase grid has 32 phases offset by pi/32, evaluated with 1601 and
3201 toroidal samples. The frozen convergence rule is
`abs(S1601-S3201) <= .001*max(abs(S1601),abs(S3201),1e-12)` for the same target.
Only the future trusted driver may compare candidates: freeze its selected
target, Wout, coil coefficients and currents before requesting held-out scores.
This component cannot certify selection timing or physical acceptance.

## Single original-reference qualification

Use only the original local reference Wout at SHA256
`83dc45b911a1e8290c3e97c7e28d4de28fcff6021b93d55df2f91d6dd3751c5e`
and committed reference input. Evaluate training, holdout and refinement once,
in that order. No new equilibrium solve, coil fit, proposal score or retry.
An analytic two-well control independently checks normalized phase variance;
failure tests check complete-domain rejection and trusted intake routes.

One **600 s total budget**, monotonic and UTC clocks (5 s discrepancy limit),
one native thread, 256 MiB aggregate output, 3/2 GiB initial/live disk reserves.
An external process-group watchdog includes setup, repeated intake, all scoring,
compression and final reporting. Preserve partial outputs; a killed or late run
cannot qualify. Freeze source and obtain read-only adversarial review of the
exact driver/launcher before execution. No other controlled job runs alongside it.

Record every score and domain failure, timing, input/source/native identities and
saved-array hashes. Software qualification requires all three evaluations to
complete with unchanged identities and exact saved-array score replay; report
full-domain eligibility and refinement convergence separately, including failure.
Archive complete evidence separately and keep its concise conclusion here.
Original Wout availability is local-only unless explicitly included in that archive.
Agent review is not external physics review. Full joint execution remains disabled
pending orchestration; qualification timing is not a comparative performance claim.
