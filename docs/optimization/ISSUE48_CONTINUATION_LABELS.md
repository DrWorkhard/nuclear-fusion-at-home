# The continuation still lacks a complete qualified flux-label grid

**Decision: diagnose the middle-surface reconstruction before launch matching.**
The candidate that recovered the [shallow core wells](ISSUE26_INTERIOR_WELLS.md)
qualifies at **19/20** nominal flux-label launches under the unchanged #48 estimator.
All 20 traces complete at least 320 transits and all controls pass, but the launch
at s=0.5, geometric theta=pi fails six reconstruction checks. The complete grid
and that surface's aggregate remain unqualified.

The failed point's angular gap is **1.240256 rad** (limit 0.4), last-prefix label
change **0.0424514** (limit 0.0005), and worst held-out radius error **0.0027803 m**
(limit 0.0001). Subset labels and full/subset quadrature also fail. Its final label
estimate 0.53154 is an unqualified observation, not a realized-surface label.
Every failed estimate and raw trace is retained.

| Nominal s | Continuation max absolute offset | Continuation phase spread | Historical reference max offset |
| --- | ---: | ---: | ---: |
| 0.10 | 0.002664 | 0.003835 | 0.001236 |
| 0.25 | 0.004130 | 0.005222 | 0.004145 |
| 0.50 | Unqualified | Unqualified | 0.011721 |
| 0.75 | 0.040281 | 0.016237 | 0.034779 |
| 0.90 | 0.084890 | 0.016664 | 0.068137 |

A surface receives qualified statistics only when all four phases and controls
pass. Historical reference values come from the qualified original #25 reference
fit in local #48 archive `2ee186bb347245072c98d983a42b06f8e02a16a9`, producer
`130347fe29e03852e257a63d0ce6ab9f828d2c85`; it was not retraced here. These offsets
are descriptive context. Different optimization histories prevent causal attribution.
Lower interior RMS and shallow-well recovery do not establish accurate surface labels.

The preregistered test reused five nominal s values and four geometric phases,
direct 512-node fields, tol=1e-10, a 321-transit stop and pooled phi=0/pi crossings.
The same interval Gauss estimator, convergence/subset/coverage gates, independent
A-line check and analytic/target controls remain unchanged. The candidate is
pjckoch's public interior continuation with frozen current 305178.2427715842 A;
the exact snapshot comes from the preceding #26 archive. Original reference401
Wout/input and target flux −0.03141592653589793 Wb remain fixed. No fitting,
adaptive tracing, retry, threshold relaxation or regenerated target was used.

Clean producer/evaluator and full prospective protocol:
`3198a16c006e731aa62dba1588fd69d17bfa0c05`. One attempt completed in **991.365 s**
within 1,800 s total, one native thread, a 256 MiB aggregate cap, 3/2 GiB disk
reserves and 5 s clock tolerance. Source/input hashes and 1,662 recorded native
package files matched before/after; owned process-group cleanup completed.

Local archive: `191875d231b396e5960cbd9460a37a6c462b6381`, prepared tag
`evidence-issue48-continuation-labels-v1`; not published or remotely verified.
Its 66-file manifest SHA256 is
`09bfe306edc73524f0c1d1270424b70ec605969f9d61e0293e6732b392395316`.
It preserves 49 original raw files (58,491,480 bytes), code/tests, protocol,
controls, frozen snapshot, commands and replay. The original Wout remains external,
with its identity and availability recorded. Original outputs/environments are intact.
Fresh shallow replay verifies all 66 files and 48 distributed source bindings,
recomputes 131 A-line integrals within 7.78e-16 of recorded labels, and reproduces
the failed qualification. It does not repeat trajectories, native B, Wout geometry
or timing; earlier-prefix/plane and B-fan checks use saved arithmetic.

Geometric theta is not PEST alpha. Reconstruction does not establish nestedness,
islands, lost surfaces, confinement, common action coordinates, benefit transfer or
reactor feasibility. No physical gate changed; #48 remains open. Read-only
adversarial agent review found no result-level blocker; it is not external peer review.
