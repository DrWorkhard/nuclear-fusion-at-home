# Realized-flux label qualification

The two frozen [issue25 fits](ISSUE25_MATCHED_TARGETS.md) have phase-dependent
realized enclosed-flux labels at target s=0.75. This reproduces the
[issue48](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/48) concern
and extends it to the improved-target fit using both original, hash-bound Wouts.
The result supports an exploratory [launch-matching pilot](ISSUE48_MATCHED_LAUNCHES.md),
not a benefit-transfer claim or verified magnetic surfaces.

| Target VMEC theta at phi=0 | Reference fit | Improved-target fit |
| --- | ---: | ---: |
| 0 | 0.715221 | 0.714935 |
| pi/2 | 0.736404 | 0.733172 |
| pi | 0.724353* | 0.721087 |
| 3pi/2 | 0.736403 | 0.733172 |

Labels are signed A-contour flux divided by the same-oriented target-edge flux.
The target s=0.25 control labels are approximately 0.246689 and 0.248563.
Currents, coils, target normalization and original inputs remain frozen.
These are geometric VMEC theta launches, not the action diagnostic's PEST alpha.

## Qualification and retained failures

Neither initial 160-crossing arm qualifies. At 320 crossings, all five selected
starts and four reference starts meet the preset reconstruction checks. The
reference theta=pi start still fails angular coverage (0.492 rad) and held-out
radial error (0.651 mm). Sampling a smooth target contour at its observed angles
produces comparable 0.748–0.767 mm errors, supporting a sampling explanation without
proving the actual trajectory is smooth or island-free.

*For that one reference start, pooling phi=0/pi sections after off-symmetry B/A
covariance and axis checks reduces gap/error to 0.240 rad/0.0392 mm. Individual-plane
failures remain archived. This is an adaptive mixed-method exploratory set, not
a uniform preregistered five-start pass. Symmetry may permute island components.

The fixed criteria require completed crossings; prefix-label change and alternating
subset spread below 5e-4; gap below 0.4 rad; held-out radius below 0.1 mm; and quadrature/
finest-grid Stokes discrepancies below 1e-5 in normalized flux. Dense reconstruction
controls use label error below 5e-4. Stokes uses the same native field implementation;
it is a discretization check, not independent physics validation. Each arm was
bounded to 900 s / 256 MiB, single-threaded; the targeted follow-up to 300 s.

## Evidence and reproduction

Prepared archive [evidence-issue48-label-qualification-v1](https://github.com/DrWorkhard/nuclear-fusion-at-home/tree/evidence-issue48-label-qualification-v1),
commit [`13c0800`](https://github.com/DrWorkhard/nuclear-fusion-at-home/commit/13c080034604b52dcb59baee41edf450bfd56d3c).
Publication is pending; the tag currently exists in the isolated local checkout.
Original clean producers: `23acc8de0892a3a77b669cd9a90dd693a452354a` (160),
`a7b6e1030dbfc88fe40b86a8ce5cddd081230796` (320), and
`fe6336aaa50cab67f97ae3811773633cb3bf43aa` (two sections). Their committed protocols
precede execution. Reports, original failures, raw traces, hashes and replay are
in the archive. Replay checks full-prefix/separate-plane A labels from saved
traces; full retracing/target controls still need the explicitly local-only Wouts.
Use [measure_flux_labels.py](../../scripts/measure_flux_labels.py) at each recorded
producer and the archived commands. Numerical qualification does not establish
nesting, equal-alpha sampling, confinement or physical acceptance.
