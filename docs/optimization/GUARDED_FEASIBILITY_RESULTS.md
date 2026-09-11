# Guarded feasibility construction: reproducible, geometry passes, flux fails

Date: 2026-09-10. Protocol a8ba079; search implementation/provenance d74662e.
Both frozen searches completed before any candidate holdout. Changes to curvature
sampling, length/flux reserves and solver are construction choices, not a
controlled comparison with the previous affine experiment.

## Search and independent acceptance

Both repeats stop at exactly 3000 full bundles, with 5942 requests, 2941 cache
hits, one denied over-budget request and no failed bundle. Physical proposal
hashes, values and counters match. Best attempt is 3000 in both; elapsed times
136.7104/136.3503 s. Merit decreases from 0.5 to 0.0002242348382, a 99.955% drop.
The separate adversarially tested ledger audit passes. This is not convergence.

The normalized starting vector was almost entirely the tighter length penalty.
The best vector still has flux component 0.02117307. Normalization factor
20808.48543 differs from the affine study: cross-study scalar merits are not
comparable. In particular, the large merit drop is **not** a similar improvement
in magnetic quality.

| Fixed acceptance quantity | Observed value | Limit | Result |
| --- | ---: | ---: | --- |
| Unthresholded quadratic flux, 128x128 surface / 800-point coils | 1.017520282e-6 | <=1e-8 | Fail: 101.752 times limit |
| Unique total length, reactor m | 219.900978977 | <=220 | Sampled/refined pass |
| Maximum curvature, continuous upper enclosure, reactor 1/m | 0.8763197223 | <=1 | Pass |
| Minimum inter-coil centerline clearance, continuous lower enclosure, reactor m | 1.0646590239 | >=1.06 | Pass |
| Coil-plasma distance, finest full-torus grid, reactor m | 3.174947045 | >=1.3 | Sampled/refined pass |

Both surface and coil flux-refinement screens pass. All seven curvature grids
pass; all sixteen physical coils are verified orthogonal copies of four bases.
Continuum enclosures use ordinary floating point with padding, not directed
rounding. Length/plasma clearance do not have interval-wide certification here.
Internal search clearance 1.10 m and length 219.9 m are not fully achieved even
though their looser, previously frozen physical acceptance limits are passed.

The candidate is rejected. Magnetic error is also worse than both failed affine
candidates; the geometric reserves and a different solver did not establish a
better feasible solution or a Pareto improvement.

## Failed replay exposed a separate portability defect

An additional fresh-context replay initially failed: SIMSOPT's lexical ordering
of runtime object names permuted curve blocks at the 9-to-10 numbering boundary.
The positional array assignment changed the field. This is a replay-adapter
defect, not evidence of wrong gradients within the original search context.

The original failure is retained. The first attempted mapping correctly rejected
the fourth coil's unsupported CurrentSum; its setup artifacts are retained too.
The final mapping follows the serialized coil/current graph and requires a
complete bijection of all 207 named free DOFs, including shared dependent-current
leaves. The archive's named values must exactly match the original saved array.

Remediated replay at 25cddc6 passes all checks with eight separately counted full
bundles: original/best residuals reproduce, inverse-mapped initial hash matches,
all sixteen curves/currents/regularizations differ by exactly zero, and the final
directional-gradient error is <=1.62318e-7 (limit 1e-6). A separate retrospective
audit verifies exact named array/field identity and best-vector hash in **all 14**
completed earlier oracle runs. No archived array or candidate was modified.

The failed replay's best-point spectrum belongs to the wrong geometry and must
not be interpreted. Correct replay gives effective Jacobian ranks 2 initially
and 3 at the candidate (8 residuals, 207 parameters; relative threshold 1e-10).
Inactive hinge constraints naturally have zero rows. These ranks alone do not
prove why progress is slow.

## Next investigation and limits

Before extending another budget, qualify a more informative residual/Jacobian
representation and examine constraint scaling. A candidate experiment can compare
aggregated flux residuals with a spatially resolved factorization, ideally keeping
the scalar objective identical. First require exact objective/gradient equivalence
on fixed fields, correct cross-process DOF mapping, and explicit accounting of
any additional field-derivative work. Then freeze a separate controlled search.
This is a hypothesis to test, not an established improvement or a novel-method claim.

G2 remains open. Finite-build self-intersection, credible mechanics, current
limits, full QI/maximum-J qualification, free-boundary robustness and canonical
SQuID-C reproduction remain separate unresolved gates.

Evidence: `guarded-feasibility-v1/`, `guarded-feasibility-v1-{ledger,holdout,
curvature,clearance,replay,replay-mapped-v2}.json`, `archived-dof-identity-v1.json`.
