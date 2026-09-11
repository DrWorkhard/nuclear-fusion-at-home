# Controlled scalar versus spatial residual pilot — 2026-09-11

Protocol cb519cb; implementation 3ef165f. Four frozen runs, original guarded
physical problem and normalization, identical TRF settings and starting point.
No candidate holdout was used as feedback into any run.

## Reproduction and work

Both representations and both repeats use exactly 128 complete proposals,
including seven gradient probes. No evaluation fails; each over-budget request
is denied once. Proposal hashes, residual values, counters and extra-derivative
work reproduce. The independent audit passes, including exact archived
named-array/field identity. Both scalar histories reproduce the first 128
proposals of the previous 3000-proposal guarded study exactly.

| Quantity | Scalar representation | Spatial representation |
| --- | ---: | ---: |
| Best common merit | 2.531730262e-4 | 4.304976277e-5 |
| Best proposal | 128 | 127 |
| Full proposal evaluations / repeat | 128 | 128 |
| Requests / cache hits / denied | 247 / 118 / 1 | 221 / 92 / 1 |
| Extra one-point B calls / repeat | 0 | 131,072 |
| Extra one-point analytic VJPs / repeat | 0 | 131,072 |
| Extra full-grid B requests / repeat | 0 | 128 |
| Elapsed seconds, repeats 1 / 2 | 7.393 / 5.640 | 147.187 / 147.180 |

Every spatial proposal also evaluates the original eight-component vector and
Jacobian. Maximum scalar-merit and gradient identity errors across the entire
search are 4.139e-14 and 2.471e-14, below the fixed 1e-10 limits. Initial
directional-gradient error is <=6.535e-9. The lower common merit is therefore
not produced by reweighting or changing the scalar physical problem.

The approximately 5.88-fold merit reduction is an **equal-proposal-cap** result,
not an equal-compute win. The spatial arm uses about 20–26 times the observed
wall time here; cold/warm startup also affects the scalar timings. No statistical
performance or multi-start ranking is established.

## Unchanged independent physical acceptance

Both serialized candidates are evaluated with the frozen flux/geometry holdout,
then the continuous curvature and inter-coil enclosures. All results are retained.

| Reactor-scale quantity | Scalar | Spatial | Required |
| --- | ---: | ---: | ---: |
| Raw quadratic flux, 128x128 / 800-point coils | 1.081333773e-6 | 4.448798671e-7 | <=1e-8 |
| Unique total length, m | 219.9015009 | 219.9006686 | <=220 |
| Continuous curvature upper enclosure, 1/m | 0.88904065 | 0.99044062 | <=1 |
| Continuous inter-coil lower enclosure, m | 1.07908056 | 1.06968985 | >=1.06 |
| Finest sampled coil-plasma distance, m | 3.16380332 | 3.23289525 | >=1.3 |

Flux surface/coil-refinement screens pass. Both candidates satisfy the stated
geometry screens, including the interval-wide curvature/inter-coil bounds. The
spatial curvature bound is unresolved at N=200/400, passing only after refinement
(N>=800); unresolved levels are not relabeled as passes. Ordinary floating-point
enclosures are not directed-rounding interval proofs. Length/plasma clearance
remain sampled/refined checks, not continuous certificates.

Spatial raw flux is about 2.43 times lower than scalar, but still **44.488 times**
the 1e-8 acceptance limit. Both candidates are rejected. Mean field magnitudes
are 0.94614248 / 0.94612475 T; the change is not explained by a comparable collapse
of the mean field. The spatial candidate has less curvature and inter-coil margin;
do not call this a Pareto-dominating physical design.

## Decision and next work

The factorization is a verified useful experimental direction, not a feasible
baseline or a demonstrated compute-efficient method. Do not silently extend the
128-proposal cap. Before a larger controlled study, qualify a less expensive
full spatial Jacobian or matrix-free equivalent against the recorded matrices,
and declare a compute-aware comparison with repeated starts. The qualified
one-point Jacobian remains an independent reference for that work.

G2 remains open: no strong admissible magnetic/engineering baseline. G4's global
QI/maximum-J qualification and G5's physical finite-build/mechanical validation
are not affected by this pilot. No SoTA or SQuID-C readiness claim.

Evidence: `spatial-trf-pilot-v1/` and `spatial-trf-pilot-v1-{audit,holdout,
curvature,clearance}.json`. Scalar/spatial candidates and original common vectors
are preserved; no threshold, output or failed verdict was overwritten.
