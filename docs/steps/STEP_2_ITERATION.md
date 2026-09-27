# Step 2 result: reproducible design iteration

**Complete, 13 September 2026**, in the registered local scope, in the same
acceptance run as [Step 1](STEP_1_FOUNDATION.md). English summary of the German
[detailed results at the freeze tag](../validation/REPRODUCING_RESULTS.md); that report
and the evidence files remain authoritative.
[All steps](README.md) · [Roadmap](../PROJECT_PLAN.md) · [Status](../STATUS.md)

## What the step had to show

That we can load a reference, change or optimize it, save the result, evaluate it
independently and repeat — with a real optimizer, and exactly reproducibly. A new
best design, feasibility or a ranking of methods was deliberately not required.

The registered protocol `docs/validation/FOUNDATION_ACCEPTANCE_PROTOCOL.md` at that tag
fixed a small real cycle before running it:

- Start from the already qualified SLSQP current minimum and its start matrix;
  reuse the existing numerical kernels unchanged, with the same Gauss–Newton/trust
  options, coordinate scaling (0.01), 207 named parameters and 1e-8 selection tolerance.
- Budget: two arms of 24 complete bundle attempts each, including 16 start replays.
- The solver must actually run and evaluate at least one point other than the
  start. Both parameter/value paths, the selection and the work counts must repeat
  exactly. Stopping at the budget is not convergence.
- A separate auditor recomputes the parameter mapping and Gram matrix; all four
  independent candidate checks run on the resulting candidates.

## Result

The final audit confirms all three Step 2 gates.

| Check | Observed result |
| --- | --- |
| Real iteration | Per arm: 24 bundles including 16 start replays; 49 requests, 24 cache hits, one refusal at the cap, no failed evaluations; eight solver-iteration reports |
| Exact reproducibility | Both complete parameter/value paths, the selection and the work counts are identical; 22 shared and 52 per-arm checks pass |
| Independent candidate checks | All four checks, both candidates, every resolution; 61 additional source/classification/computation checks each |

Both candidates are **correctly rejected**: their fine raw flux error is
8.191663957639298e-8 against the limit 1e-8, although geometry and the extra
native screens pass. The selected field came from start replay 12, not from a new
solver gain; the solver did evaluate other points, and both runs stopped at the
budget without proven convergence. The earlier, better research value of
8.129882e-8 is preserved unchanged.

## What it does not show

A feasible coil design, a better optimizer or convergence. The cycle demonstrates
that iteration and independent evaluation work and are reproducible; the physical
limits stayed unchanged and rejected both candidates.

## Evidence

- [Iteration audit](../../evidence/foundation-acceptance-v2/cycle-audit.json)
- [Candidate checks](../../evidence/foundation-acceptance-v2/holdouts/summary.json)
- [Final audit](../../evidence/foundation-acceptance-v2/summary.json)
- Commands for a single cycle and its audit: [detailed results at the freeze tag](../validation/REPRODUCING_RESULTS.md)
  (native research environment required).
