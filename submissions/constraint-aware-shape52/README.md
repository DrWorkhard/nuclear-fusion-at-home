# A checked exploratory shape to reproduce and improve

This is the geometry of shaped/full trial 52 from our
[constraint-aware study at the freeze tag](../../docs/validation/REPRODUCING_RESULTS.md)
(`docs/optimization/CONSTRAINED_COIL_EXPLORATION.md` there).
It improves both public sampled scores without changing the trusted evaluator,
case, currents or reference. It is **not an accepted reactor design**.

## Reproduce with the public starter

From the repository root, Python 3.11+ with no package installation:

```bash
python fusion.py public evaluate --candidate submissions/constraint-aware-shape52/candidate.json --output results/shape52-report.json
python fusion.py public audit --report results/shape52-report.json --output results/shape52-audit.json
```

Choose fresh output names if these already exist. Expected approximate scores
at 512 coil nodes:

| Public metric | Unchanged reference | This geometry | Change |
| --- | ---: | ---: | ---: |
| Sampled normal RMS | 0.304207 | 0.170953 | −43.80% |
| Sampled interior-vector RMS | 0.380435 | 0.292176 | −23.20% |

Actual local evaluation and replay passed on 27 September 2026, with
`report_replay_pass: true`, `independent_implementation: false` and
`physical_admission: false`. Replay uses the same evaluator; it is not a second
physics implementation or a separate-machine reproduction. Public evaluator
code is unchanged from project revision `39a1e13`.

Copy this candidate to your own submission folder to explore another change.
Report both scores and any trade-off; the reference packet remains unchanged.

## What was optimized and what this file preserves

The native study optimized 198 named order-5 Fourier coefficients of six base
curves (24 physical coils, two field periods). Its local-normalized field
objective used length, curvature and clearance penalties. Trial 52 was chosen
adaptively from saved search points for additional clearance, then frozen before
finer fields and independent continuous-geometry bounds. It was not selected by
these public sample scores. It is not a preregistered confirmation result.

The exported coefficients and all 198 names exactly match native snapshot SHA-256
`2492d83ad3392069be5bfe8ae35b2e98ca0419916517e96065e017bcf15417e9`.
The [source evidence](../../evidence/constrained-coils-slack-v1.json) records the
full local provenance, including original trials and the selection sweep.
The small candidate file and commands above suffice for public reproduction;
private native artifacts are not needed for that calculation.

**Identical geometry does not mean identical magnetic state.** The public case
fixes base-current magnitude at 294,966.466322 A. The native fit uses
324,791.877578 A to restore its target flux, giving full-grid normal RMS 0.151679.
The public evaluator does not restore flux after a shape edit. A common current
scale leaves same-point normalized normal error unchanged; different sampling/
weights explain the normal-score difference. Field amplitude, flux and the
interior-vector score do change with current. The subsequent
[native interior screen](../../docs/optimization/INTERIOR_FIELD_EXPLORATION.md)
measures RMS **0.3123243**, still above its 0.01 limit. This does not change
the frozen-current public result above.

Native scoped continuous bounds: length ≤2.081313 m, curvature ≤11.065107/m,
coil separation ≥147.712 mm, plasma clearance ≥80.714 mm. These are independently
checked padded floating-point bounds, not interval proofs or finite-build
engineering. Boundary error still greatly exceeds the native acceptance limits;
topology, plasma-benefit transfer, pressure and robustness remain open.

## Attribution

Candidate data follow the starter's CC BY 4.0 attribution; see
[data provenance and license](../../examples/clear-coil-samples-v1/README.md#provenance-and-attribution)
for Goodman et al.'s underlying plasma data. The project generated and optimized
these coil coefficients; no author endorsement or Proxima affiliation is implied.
Compared with the bundled starter, only the named coefficient values change.
