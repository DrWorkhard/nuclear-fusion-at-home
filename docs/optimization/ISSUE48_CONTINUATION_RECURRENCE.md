# Prospective saved-point diagnosis of the continuation failure

**Decision:** whether the failed s=0.5, geometric theta=pi reconstruction in the
[continuation grid](ISSUE48_CONTINUATION_LABELS.md) has sampled recurrence consistent
with simple monotonic angular drift, or additional reversals that require a more
specific reconstruction diagnosis. This is an exploratory explanation of an
observed failure, not a confirmatory physics or surface-classification claim.
No new trajectories, fields, coils, targets, launch matching or gate changes.

Freeze five existing cases before processing their saved crossings: continuation
indices 8/9/10/11 (all four mid-radius phases) and original reference401 index 10
(the same phase as the failing continuation point). The three other continuation
phases and historical reference point are qualifying controls. Inputs resolve at
archives `191875d231b396e5960cbd9460a37a6c462b6381` and
`2ee186bb347245072c98d983a42b06f8e02a16a9`, respectively. Their original producers
are `3198a16c006e731aa62dba1588fd69d17bfa0c05` and
`130347fe29e03852e257a63d0ce6ab9f828d2c85`. Bind both manifests and every consumed
report/array before and after processing. Original qualification verdicts stay fixed.

Reuse the unchanged angle, gap, recurrence, interpolation and exact-circle controls
from `70619a97df51cd8ccc34d7265e540cb26a2d70db`. Select the first 640 chronological
pooled phi=0/pi crossings, excluding the launch event, then split into 320 per plane.
Use the original target-axis polar center. Report physical R,Z return RMS at
10/11/12 full toroidal turns, prefix gaps at 80/160/320 same-plane crossings, the
last-160 gap, and all eleven residue sequences' sampled angular span, net advance,
total variation and resolved direction changes. Eleven is fixed because the
recorded continuation transform is near −6/11 (failed point −0.54574596).
NumPy unwrap and the existing 1e-8-rad resolved-step cutoff remain unchanged.

Repeat the existing polar-spline positive-radius check at 160/320/640 pooled
crossings and interval Gauss orders 4/8. This is not an integral calculation or
label replacement. Exact rational, near-rational and well-sampled circular controls
must pass. Retain every case, prefix and interpolation failure. Reversals or large
gaps characterize these finite samples only; neither proves islands or loss of a
surface. Monotonic samples do not establish future coverage or a completion time.

One saved-array attempt: 60 s driver / 75 s supervised total, one thread, 256 MiB
aggregate output, 3/2 GiB initial/live disk reserves and 5 s clock tolerance.
Reuse the reviewed owned-process supervision and final-receipt functions from
`3198a16c006e731aa62dba1588fd69d17bfa0c05`, with scoped termination handling.
Native tracing/equilibrium packages are disabled in the child. No Wout is required.
The launcher verifies clean committed code, frozen inputs/environment before/after
and process cleanup. No retries, longer traces, adjusted residue count or thresholds.

A difference from the controls can identify the next bounded question; it cannot
requalify the contour or support automatic retracing. Preserve the 19/20 grid
verdict and the original #25/#48 results. Archive complete diagnostics separately
and keep one short result record. Geometric angle is not common PEST alpha; no
nestedness, confinement or benefit-transfer claim follows. Agent review is not
external physics review. Archives and new results remain local pending publication.
