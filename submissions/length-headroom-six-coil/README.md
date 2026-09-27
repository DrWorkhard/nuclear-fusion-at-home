# Six-coil fit with construction length margin

A reusable geometry from our [headroom study](../../docs/optimization/LENGTH_HEADROOM_EXPLORATION.md):
expanded-box trial1459, native producer revision `5a3c1d0`.
It lowers both public sampled errors, without changing the reference, evaluator
or public currents. It is **an exploratory candidate, not an accepted design**.

## Reproduce and modify

From the repository root, Python 3.11+; no installations or native artifacts:

```bash
python fusion.py public evaluate --candidate submissions/length-headroom-six-coil/candidate.json --output results/headroom-report.json
python fusion.py public audit --report results/headroom-report.json --output results/headroom-audit.json
```

Use fresh output paths. Copy the candidate to your own submission folder and
use `public set-coefficient` to edit named values. Report both scores and trade-offs.

| Public metric, 512 coil nodes | Reference | This geometry |
| --- | ---: | ---: |
| Sampled normal RMS | 0.304207 | **0.00174403** |
| Sampled interior-vector RMS | 0.380435 | **0.03610319** |

Local Python 3.12 and isolated Python 3.11 (`-I -S`) evaluation/replay passed
on 27 September 2026:
`report_replay_pass: true`, `independent_implementation: false`,
`physical_admission: false`. The trusted public evaluator is unchanged from
revision `39a1e13`; no separate-machine reproduction is claimed.
The older [shorter-coil example](../constraint-aware-shape52/README.md) remains
useful for the length/field trade-off, not as our lowest-error starting point.

## Native result and limits

The native search changes 198 named coefficients of six order-5 base coils
(24 physical coils). It penalizes lengths above 3.44 m and selects a completed
candidate with sampled lengths ≤3.45 m before fine field and geometry checks.
The acceptance length limit remains 3.5 m. The target is the original Goodman
reference401, not our improved Step 3 plasma.

Shared dense checks: normal RMS **0.00199627** versus 1e-4; maximum normal error
**0.00942578** versus 1e-3; interior RMS **0.01147939** versus 0.01. All three
field limits fail. Scoped geometry passes: length ≤3.474220 m, coil clearance
≥0.06831 m, plasma clearance ≥0.13307 m, curvature ≤10.04691/m.
These are padded floating-point bounds, not interval proofs or finite-build
engineering. Realized magnetic surfaces and plasma-benefit transfer remain open.

**Same geometry, different magnetic state:** native current is 308,140.584432 A
to preserve loop flux; the public case freezes 294,966.466322 A. Sampling also
differs. The public inner score therefore does not reproduce the native inner
score, and neither public score is an acceptance decision.

All coefficients/names exactly match native snapshot SHA-256
`84bbdf3eca274981dfff80c967b6fd623a1a40350e583407cbb7262c26820217`.
[Source evidence](../../evidence/coil-headroom-v3.json) binds the native selection,
fine arrays, geometry and retained failed setup. This small candidate is a
separately identified portable export; it does not replace that evidence.

## Attribution

Candidate data follow the starter's CC BY 4.0 attribution. Credit Goodman et al.'s
underlying plasma data as specified in the
[data provenance](../../examples/clear-coil-samples-v1/README.md#provenance-and-attribution).
The project generated these coil coefficients. No author endorsement, Proxima
affiliation, state-of-the-art advantage or reactor-performance claim is implied.
