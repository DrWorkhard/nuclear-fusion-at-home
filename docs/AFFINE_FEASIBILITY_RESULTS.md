# Fixed affine-coordinate feasibility study v1

Protocol c7e6ae1 and implementation 3ac761f preceded the four runs on 2026-09-10.
All runs use physical x=x0+0.01*y, the unchanged eight-component normalized
problem and the same seven physical directional probes. Physical x, not y, is
used by the oracle cache, ledger, best-candidate selection and serialization.

## Search and repeatability

| Method (each repeated twice) | Bundles per run | Best common merit | Stop |
| --- | ---: | ---: | --- |
| L-BFGS-B | 1500 | 0.02009712609 | Exact budget cap |
| Pinned AL | 1500 | 0.01009954549 | Exact budget cap |

One shared normalization bundle is outside the per-arm budget. Both repetitions
have identical physical proposal hashes, vector values, counters and stop status.
Each L-BFGS-B run has 1501 requests, zero cache hits and one denied evaluation;
each AL run has 36,448 requests, 34,947 cache hits and one denied evaluation.
There are no failed backend evaluations or budget overshoots. Best candidates
are solver proposals at attempt 1500, not gradient probes. Neither search is
shown converged; each best result occurs at the budget endpoint.

L-BFGS-B wall times: 68.21/70.28 s; AL: 115.14/106.67 s. Equal oracle bundles
are not equal wall time. The maximum physical directional-gradient discrepancy
is 8.843e-9, unchanged from the earlier normalized study.

The prior immediate L-BFGS-B return disappears. Its first solver merits are now
0.5, 126719.03, 113.55, 0.82020, 0.49960, followed by continued progress. This
supports the coordinate-scale/line-search hypothesis in this specific problem;
it does not identify a unique general failure cause. Scaling changes effective
physical stopping tolerances too. Previous failed runs are not overwritten.

AL has the smaller final common merit at genuinely equal consumed bundle counts
for this start. This is not a multi-start method ranking, a feasible-design claim
or a SoTA advance. Deterministic repetitions are not independent initializations.

## Physical-problem and ledger audit

`scripts/audit_affine_equivalence.py` independently checks serialized metadata
against the preceding normalized study: identical DOF names/order, source-parent
field hash, surface/case hashes, thresholds, component scales, normalization and
all seven physical probe x hashes/values. It verifies the one-LF fixture change,
every arm's best selection and physical-array hash, contiguous evaluation ledger,
request partition and exact budget stop. All checks pass. It makes no new physics
calls and cannot replace candidate validation. The preserved historical producer
lineage gap of the warm-start fixture is not repaired by this experiment.

Machine-readable search evidence: `evidence/affine-feasibility-v1/`;
audit: `evidence/affine-feasibility-v1-equivalence.json`.

## Completed independent candidate validation

Both candidates fail flux, length **and curvature**. Exit 2 is retained; none of
the hard thresholds is relaxed. Buffered optimization clearance remains 1.10 m,
versus the predeclared acceptance floor 1.06 m.

| Finest metric | L-BFGS-B | AL | Required |
| --- | ---: | ---: | ---: |
| Unthresholded quadratic flux | 2.19672433e-7 | 1.55617716e-7 | <=1e-8 |
| Unique total length, reactor m | 220.00052601 | 220.00123472 | <=220 |
| Maximum sampled curvature, reactor 1/m | 1.00355069 | 1.03114211 | <=1 |
| Sampled inter-coil centerline gap, reactor m | 1.06866280 | 1.07334891 | >=1.06 |
| Sampled coil/plasma gap, reactor m | 3.17573056 | 3.05875952 | >=1.3 |

Both flux-refinement checks pass. The field errors remain about 22 and 16 times
above the cut-in. Length exceeds the bound by 0.526 and 1.235 mm, not waived.
Mean surface |B| is 0.946127/0.946124 T; this is not a full current certification.
The independent holdout costs 25.61/25.90 s outside optimization budgets.

At the optimization's 200 points the independent curvature audit sees only
0.988367/0.995540 per reactor m: both below the limit. At 20,000 points both
violate it. This is a genuine off-grid constraint gap, independently confirmed
using compiled derivatives and position-only circumcircle witnesses; see
CURVATURE_ALIASING_RESULTS.md. Zero coarse curvature penalty is not a hard
continuous-curve feasibility certificate.

The existing Fourier distance bound was also applied unchanged to both new
candidates. Continuous inter-coil centerline lower bounds are 1.06843025 and
1.07312751 reactor m, above 1.06. This check uses ordinary floating point, not
directed rounding, and does not certify single-coil self-intersection, actual
mesh enclosure, plasma clearance or mechanics. It cannot repair the failed
flux/length/curvature screens.

Evidence: `affine-feasibility-v1-holdout.json`,
`affine-feasibility-v1-continuous-clearance.json` and
`affine-feasibility-v1-curvature-witnesses.json` under `evidence/`.

Next priority: qualify an off-grid curvature constraint before committing to
larger optimization campaigns. Neither algorithm has proved infeasibility of
the problem; these are rejected finite-budget candidates, not an impossibility
result. A feasible multi-start baseline and full engineering admission remain open.

Ten coordinate-adapter tests pass, including analytical chain rule, round trip,
ownership, invalid inputs and physical-coordinate budget/best selection. Full
local suite: 123 passed; updated detached test clone: 122 passed, one absent-W7-X
skip. Ruff passes; eleven existing fixture deprecations and pinned AL's `disp`
option warning are retained.

After adding the three curvature-witness test groups, the complete local suite
passes 126 tests; the updated detached clone at e9fde75 passes 125 with the one
expected W7-X skip and remains clean. Ruff passes. A recursive integrity check
of all nine new affine evidence files verifies all 37 unique referenced
path/SHA-256 pairs. These are local checks, not a hosted CI witness.

Reproduce into fresh paths with the benchmark environment and the established
single-thread/MPI/font-cache settings:

```sh
PYTHONPATH=src MPLCONFIGDIR=/private/tmp/fusion-mpl-cache OMPI_MCA_btl=self \
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python \
scripts/qualify_optimization_oracle.py --affine-feasibility \
--output evidence/affine-feasibility-new --raw artifacts/affine-feasibility-new
```
