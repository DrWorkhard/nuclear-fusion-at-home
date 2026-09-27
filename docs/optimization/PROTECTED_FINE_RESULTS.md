# Protected coil-fit pilot: complete fine results

26 September 2026. [Registration](PROTECTED_FINE_PROTOCOL.md) ·
[Coarse search](PROTECTED_COIL_FIT_RESULTS.md) ·
[Software qualification](../../evidence/protected-fine-qualification-v1.json) · [Index](README.md)

## Result

**All eight fixed candidates complete fine validation and pass numerical
qualification. None passes the physical field limits.** Independent continuous
and four-grid geometry checks pass for every candidate; current limits also pass.
The failures are normal-field RMS, maximum normal-field error and interior-vector
RMS—not a failed execution or an inconsistent reconstruction.

This closes the registered pilot's required fine phase. It does **not** close
realization/transfer 4A, coupled improvement 4B, pressure/confinement 4C or finite
build/robustness 4D. No accepted new coil baseline, resolved fine-grid gain,
state-of-the-art result or MS1 advantage follows.

| Fixed candidate | Fine normal RMS | Fine interior-vector RMS | Numerical checks | Absolute field/geometry |
| --- | ---: | ---: | --- | --- |
| reference-n6-N | 0.274721643 | 0.363347250 | Pass | Fail |
| reference-n6-V | 0.274710370 | 0.363318999 | Pass | Fail |
| reference-n8-N | 0.267946321 | 0.357205968 | Pass | Fail |
| reference-n8-V | 0.267936149 | 0.357198235 | Pass | Fail |
| selected-n6-N | 0.274782102 | 0.364110181 | Pass | Fail |
| selected-n6-V | 0.274771319 | 0.364077093 | Pass | Fail |
| selected-n8-N | 0.268007493 | 0.357922049 | Pass | Fail |
| selected-n8-V | 0.267997688 | 0.357913475 | Pass | Fail |
| **Limit** | **0.0001** | **0.01** | All prescribed checks | Every gate |

Displayed normal RMS uses diagnostic level 2: 128×128 boundary points and 512
coil nodes. Interior RMS uses level 5: three 64×64 interior surfaces and 512 coil
nodes. They are different diagnostic grids, not a newly combined evaluation.
Acceptance checks **all six rows**, including the shifted boundary grid. These
errors remain about 2,680–2,748 and 36 times their respective limits. “Selected”
in a case name identifies the Step 3 plasma target, not a winning method.

## Execution and independent checks

- Clean execution checkpoint: `e0ac3f775a375255ee6d2355137b19d733fa1498`.
  Runtime source admission and canonical manifest round-trip pass in 17.945 s.
- The serial CLI exits zero and explicitly returns the complete eight-case
  summary after 1,360.380 s. Source-before and source-after are identical,
  344,230 bytes, SHA-256
  `2a4a1dd9ec1e5e8766de554b77de32cd7aa31cd5e9f88a04c9feba40da113e46`.
  No tracked changes, environment synchronization or competing heavy study.
- Exactly **640 native requests / 4,423,680 queried points**, including 64
  original-seed initializations. With construction: 2,573 requests, below the
  original 2,960 ceiling. No new optimization, derivative probes or equilibrium.
- Independent reconstruction: 64 initializer scalars, 48 metric rows and 144
  flux grids. All **576 sampled B/A statistics / 36,864 vectors / 110,592 scalar
  components** pass; maximum relative error **5.612042e-15**, limit 5e-10.
  Initializer discrepancy is at most 6.514979e-16, also below 5e-10.
- All **40 refinement comparisons** pass. Largest relative change is
  **0.019256%**, below the prescribed 1% OR 1e-7 absolute rule.
  All **504 flux checks** pass, maximum relative discrepancy 8.834875e-16,
  limit 1e-6. Selected coarse currents remain frozen; no fine recalibration.
- Eight original-seed cumulative certificates and **32 direct geometry grids**
  pass independent reconstruction and physical geometry limits. Every grid
  checks both full-torus target surfaces and every physical coil pair:
  12,352 pair/grid comparisons in total. Enclosure slack remains zero.
- The preceding clean full regression has 4,883 passing tests and 334 existing
  warnings. A separate post-run record review rehashes 707 directly referenced
  files / 377,039,908 bytes and reconciles counts/outcomes. It does not repeat
  field mathematics or generically re-expand historical source envelopes.
- An independently authored internal review confirms the explicit return,
  eight acknowledgement/configuration chains, all 1,800 journal events and
  each 80-request schedule. It rehashes 2,933 files / 429,116,251 bytes, including
  all 224 new raw archives, and verifies three historical commit references.
  It finds no mismatches. This is a broader reference traversal than the main
  record review, not another field/geometry recomputation or fresh historical
  source admission. Its initial current-file comparison of a historical edge
  was corrected to the explicitly pinned Git object; no study data changed.

Large immutable data remain in `artifacts/protected-fixed-fine-v1/`; execution
logs, source admission and review records are under `artifacts/protected-fine-v1/`.
The [evidence record](../../evidence/protected-fine-results-v1.json) binds the
explicit result and exact reports. Internal reviews are not external peer review.

## What we learned and what follows

For these eight candidates and prescribed grids, the large field mismatch
survives finer resolution while the geometry remains acceptable. This supports
changing the search approach rather than attributing the mismatch to this tested
sampling resolution. It is not a proof of global convergence or impossibility.

The earlier coarse searches stopped at a conservative cumulative curvature
bound; their modest gains are retained as coarse results. Passing these fine
checks alone does not satisfy a separately preregistered matched-grid improvement
margin, and cannot establish Pareto dominance or plasma-benefit transfer.

The subsequent [local curvature study](../geometry/LOCAL_CURVATURE_RESULTS.md)
certified two previously blocked proposals under unchanged limits. Their
[field comparison](FIXED_FIELD_PROBE_RESULTS.md) found small gains, still far from
acceptance. Current follow-up is diagnosis and reference calibration under the
[research programme](STEP4_RESEARCH_PROGRAMME.md); none of these follow-ups
changes this study's selection, thresholds or negative field verdicts.
