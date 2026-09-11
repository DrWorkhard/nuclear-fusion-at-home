# Bounce-action measurement v1 — results, 2026-09-09

Protocol commit: 75c0ba8. Implementation commit before data evaluation: 372a63f.
All preregistered bounded measurement screens pass for nfp=1,2,3. This is a
numerical measurement result, not a new QI design or full QI qualification.

| Case | Largest ordered-well J change, 801->1601 | Largest envelope change across refinements | Runtime |
| --- | ---: | ---: | ---: |
| nfp=1 | 3.5498e-5 relative | 6.6400e-4 | 33.63 s |
| nfp=2 | 5.2984e-5 relative | 2.7227e-4 | 14.08 s |
| nfp=3 | 1.0836e-4 relative | 3.0987e-4 | 19.82 s |

The frozen action-change limit was 1e-3. Each envelope cell had its own
max(0.002,5% of previous envelope) limit; all pass. Complete-well alpha coverage
is 100% at all three surfaces and five pitches for every resolution. There are
no censored wells in these sampled traces. This does not prove coverage of
unsampled pitch, alpha, radial positions or near-separatrix trajectories.

The parabolic analytic control converges with relative errors 1.4895e-5,
9.2323e-7 and 5.7461e-8 on 257,1025,4097 points. The independent endpoint-singular
segment quadrature differs by 7.2786e-8 (limit 1e-6). A deliberate 1% modulation
in well length recovers a 0.02 envelope spread.

An independent replay of all saved actions using 128-point Gauss-Legendre
quadrature checked 12,960 well integrals and every raw trace hash. Largest
relative discrepancies are 5.4105e-10, 4.6785e-10 and 5.1230e-10. This comparison
checks integration of the same piecewise-linear B(l), not correctness of the
shared VMEC field-line tracer.

Evidence: evidence/qi-measurement-v1/nfp1.json, nfp2.json, nfp3.json and
quadrature-verification.json. Raw arrays are hashed compressed files under
artifacts/qi-measurement-v1/. Source parsing emits a legacy invalid-escape
SyntaxWarning; no numerical trace warnings or error messages were captured.

The finest envelope ranges are 0.00122–0.04057, 0.00132–0.02599 and
0.00240–0.02925. These are diagnostic spreads across complete wells, not a
ranking of the three designs: the cases use different physical pitch grids.

The scientific qualification flag remains false. Outstanding: independent
tracing, well-family identity, pitch/radial refinement, contour topology and
finite-pressure maximum-J assessment. The legacy residual's convergence failure
is retained; this experiment does not repair or relabel that objective.

Reproduction (existing evidence is never overwritten):

```bash
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  environments/vmecpp/.venv/bin/python scripts/qualify_bounce_action.py
OPENBLAS_NUM_THREADS=1 .venv/bin/python scripts/verify_bounce_action_evidence.py \
  evidence/qi-measurement-v1/quadrature-verification.json \
  evidence/qi-measurement-v1/nfp1.json evidence/qi-measurement-v1/nfp2.json \
  evidence/qi-measurement-v1/nfp3.json
```

A fresh reconstruction needs the pinned Goodman data and VMEC++ environment.
To rerun locally, use an isolated checkout with no existing experiment outputs.
