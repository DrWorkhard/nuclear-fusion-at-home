# Bounded matching of realized-flux launch labels

**Inconclusive: the two arms do not jointly qualify.** Four physical launch rays
in each frozen [issue25 fit](ISSUE25_MATCHED_TARGETS.md) were adjusted toward an
estimated enclosed-flux label of 0.75. All eight nominal estimates reach the label
tolerance, but one improved-target estimate fails quadrature qualification.
This does not establish physical mismatch or lost benefit; it blocks a claim
that the pair has reliable matched flux labels under this protocol.

| Final diagnostic | Reference fit | Improved-target fit |
| --- | ---: | ---: |
| Maximum estimated-label residual from 0.75 | 3.86e-5 | 7.75e-5 |
| Phase-to-phase estimated-label spread | 4.02e-5 | 7.93e-5 |
| Qualified lines, including unchanged control | 5/5 | 4/5 |
| Largest final quadrature failure | None | theta=0: 4.25e-5, limit 1e-5 |

## Method and stop rule

The [qualification study](ISSUE48_REALIZED_LABELS.md) supplied starting estimates.
For nominal target VMEC theta={0,pi/2,pi,3pi/2} at s=0.75,phi=0, use the physical
ray `(R,Z)_new=(R,Z)_axis+rho*((R,Z)_original-(R,Z)_axis)`, with rho in [0.95,1.05].
Coils, currents, target normalization and the s=0.25 control launch stay frozen.
Both arms use 321 turns and symmetry-checked phi=0/pi sections.

The prospective rule allows a square-root initializer, then exactly one bounded
secant if the first round qualifies. First-round estimates undershoot and some
fail 1024/2048-point quadrature. A declared adaptive check recomputes all saved
trajectory prefixes at 4096/8192 angular and 24 radial nodes, with unchanged
thresholds, edge denominator and raw trajectories. Both first-round arms then
qualify, permitting the single secant. Original failures remain failures.

After correction and the same refinement, selected theta=0 has angular-quadrature
change 4.25387e-5 against 1e-5; its finest Stokes discrepancy 1.80e-6 passes. The
pilot stops here with no more refinements or retries. Each trace arm is bounded
to 900 s / 256 MiB (960 s supervisor); each paired saved-trace refinement to 600 s
(660 s supervisor), one thread and the original 3 GiB / 2 GiB disk reserves.

## Evidence and next decision

Prepared archive [evidence-issue48-launch-matching-v1](https://github.com/DrWorkhard/nuclear-fusion-at-home/tree/evidence-issue48-launch-matching-v1),
commit [`896180e`](https://github.com/DrWorkhard/nuclear-fusion-at-home/commit/896180e939b0234aea29ab33621a73aad6c5d20a).
Publication is pending; the tag currently exists in the isolated local checkout.
The clean trace producer is `30ba2ea921d94bfb309742f01a43173a555fb0e2`; its committed
protocol precedes both rounds. The archive also binds the external refinement
scripts and explicitly records evaluator-source verification after execution.
It includes both rounds, raw traces, scales, failures, derived reports, commands,
hashes and replay. Full-prefix A labels replay without the local-only Wouts;
full retracing/target controls still require those original inputs.

The numerical blocker can be diagnosed on saved traces in a separately declared
method check. These four geometric phases do not replace the original 16-alpha
PEST action domain. Even a numerical match would not prove invariant nested
surfaces, equal-alpha sampling, confinement or benefit transfer. No field or
geometry acceptance limit changes, and the stopped pilot is not relabelled a pass.
