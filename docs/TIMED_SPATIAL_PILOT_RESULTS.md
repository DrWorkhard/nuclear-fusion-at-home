# Equal-wall-clock scalar versus batched spatial pilot — 2026-09-11

Protocol 919fc6f, finalized before execution with implementation 8d21af5.
Four runs share the original guarded physical problem, start, normalization and
TRF settings. Completed traces and independent accounting audit: 7ae7c08.

## Search and reproducibility

| Arm | Complete proposals | Stop time (s) | Best common merit |
| --- | ---: | ---: | ---: |
| Scalar 1 | 6358 | 300.007159 | 2.060565373e-4 |
| Scalar 2 | 6571 | 300.039253 | 2.050913903e-4 |
| Batched spatial 1 | 770 | 300.057142 | 3.737640288e-5 |
| Batched spatial 2 | 763 | 300.008441 | 3.742149933e-5 |

Each arm stops on one time denial, without failed physical evaluations. The
entire common prefix of each repetition pair agrees in physical hashes and
values; terminal proposal counts differ with timing and are not called identical
full trajectories. Shared warmup is recorded separately. Overruns are retained,
not rounded into an assertion of exact 300-second runs.

Spatial identity errors across every proposal are <=5.322e-14 for merit and
<=2.598e-14 for its gradient. Additional spatial work is respectively 12,320 /
12,208 physical-coil contractions, twice as many geometry-derivative requests,
and 12,320 / 12,208 current VJPs. No single-point VJP calls are used. The audit
also verifies archived named parameters against the saved field and best array.

## Independent physical rejection of all four candidates

The unchanged holdout evaluates every repeat, not only the better result.
Flux below is unthresholded, on the final 128x128 surface with 800-point coils.
Curvature upper bounds cover the continuous Fourier curves at N=12,800;
inter-coil lower bounds supplement the all-120-pair N=20,000 node check.
Bounds use ordinary floating point with padding, not directed rounding.

| Arm | Raw flux (limit 1e-8) | Length (m; limit 220) | Curvature upper (1/m; limit 1) | Clearance lower (m; minimum 1.06) |
| --- | ---: | ---: | ---: | ---: |
| Scalar 1 | 9.745341534e-7 | 219.900943 | 0.863332952 | 1.058019185 |
| Scalar 2 | 9.721954774e-7 | 219.900939 | 0.862592117 | 1.057959679 |
| Batched spatial 1 | 4.146141104e-7 | 219.900644 | 0.990380074 | 1.069512969 |
| Batched spatial 2 | 4.148650127e-7 | 219.900644 | 0.990380937 | 1.069514530 |

All pass flux quadrature refinement, length, curvature and the coil/plasma
distance screen (minimum 3.187 m versus 1.3 m required). Both scalar candidates
fail flux and inter-coil clearance: even sampled distances 1.05817 / 1.05811 m
are below 1.06 m, so this is a violation witness, not merely a loose lower bound.
Both spatial candidates fail flux, by factors 41.461 / 41.487. Their curvature
bounds are unresolved at N=200/400 and pass from N=800; all levels are retained.

## Interpretation and next decision

At this fixed start and approximate equal wall time, spatial flux is about
2.34–2.35 times lower than scalar. This is a bounded computational result, not
statistical hardware characterization, a multi-start ranking, Pareto dominance,
a feasible baseline, or a SoTA design advance. Lower penalty merit does not
enforce hard constraints; the longer scalar runs even cross a clearance limit.

Next qualify smooth explicit inequalities using raw geometric metrics before
any separately preregistered constrained search. This changes the construction
formulation; it must not be sold as another objective-equivalent comparison.
The existing holdout thresholds remain unchanged. G2 and SQuID-C readiness stay
open, as do the separate QI and physical engineering gates.

Evidence: `evidence/timed-spatial-pilot-v1/summary.json`,
`evidence/timed-spatial-pilot-v1-audit.json`,
`evidence/timed-spatial-pilot-v1-holdout.json`,
`evidence/timed-spatial-pilot-v1-curvature.json`, and
`evidence/timed-spatial-pilot-v1-clearance.json`.
