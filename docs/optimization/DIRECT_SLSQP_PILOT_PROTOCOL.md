# Direct-inequality SLSQP construction pilot v1 — 2026-09-11

Preregistered after passing fixed-state qualification, before new optimization.
This changes the construction formulation; it is not an objective-equivalent
comparison against the earlier squared-penalty TRF experiments.

## Frozen search

Use the original promoted LPQA warm start, never an optimized spatial candidate.
Preserve the qualified direct backend byte-for-byte: 207 named physical DOFs,
raw flux / 1e-6 objective, all 137 positive-pass inequalities, beta=512, four
unique/16 physical coils, 200-point field curves, 1600-point curvature curves,
32x32 flux surface and 64x64 full-torus plasma-distance surface. All construction
targets and physical admission limits stay unchanged. Total-current dependence
and regularizations remain exactly those of the original archived field.

Two sequential repeats, same start. Each arm has a hard cap of 256 complete
value/Jacobian bundles, including nine initial seed-46 directional probes at
eps=1e-5,1e-6,1e-7,1e-8. All rows must pass normalized finest-step error <=1e-6.
Use physical x=x0+0.01*y, analytic objective and constraint gradients, SciPy SLSQP,
ftol=1e-10, maxiter=100000; no restart, objective alteration, or after-the-fact
budget extension. Record actual consumed work and stop reason, even early failure.
Wall time is measured, but this is not a same-time method comparison.

Count every request, exact-last-point cache hit, completed/failed bundle and
denied over-cap request. Any failed bundle stops the arm; preserve partial
evidence and do not relabel upstream retries as free. Snapshot every 25 proposals.
Both repetitions must have identical proposal hashes, values, counts and stop
reason. The proposed inequality backend's work counters describe logical sample
sets; the raw-minimum reporting pass repeats the distance calculations.

## Candidate selection fixed before search

For g>=0 define maximum violation v=max(0,-min(g)). Among completed proposals
with v<=1e-8 choose minimum raw objective, ties resolved by first observation.
If none meets that *construction screen*, choose smallest v, then objective.
This tolerance only chooses a candidate; it never changes physical admission.
Record every row, violations, selection key and best physical array. Save its
serialized field without an uncounted new evaluation. Also record the solver's
terminal coordinates; they may not be the best completed proposal.

## Independent post-search acceptance

After both repeats and accounting/array identity audit, evaluate both best fields
with the unchanged fine-grid flux/geometry holdout and continuous curvature /
inter-coil bounds. Additionally check the four native MSC and arclength-variance
metrics at coil resolutions 200, 800, 3200 against original native thresholds;
require the final pair's relative change <=1e-6 (denominator max(1,abs(last))).
Check native all-16-coil linking number equals zero at resolutions 200 and 800,
with no downsampling. These are additional bounded screens, not certified
nonlocal self-intersection or full mechanical/topological admission.

No holdout feedback into either frozen arm. All candidates, failures and
resolution levels remain in the record. A passing small pilot would justify
a stronger classical/multi-start benchmark, not SoTA, validated QI transport,
engineering readiness or SQuID-C reproduction.
