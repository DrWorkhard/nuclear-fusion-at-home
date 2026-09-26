# Local whole-homotopy curvature: twelve-state results

26 September 2026. [Protocol](LOCAL_CURVATURE_PROTOCOL.md) ·
[Software qualification](LOCAL_CURVATURE_PROGRESS.md) · [Index](README.md)

## Result

**All twelve fixed states pass the new curvature component and its separate
checker. Both previously curvature-rejected proposals now pass the complete
local geometry classification, with the seven other gates unchanged.** This
establishes conservatism of the old bound on these two proposals, not their field
quality or a generally larger useful search region. Their fields remain unmeasured.
The old decisions and original evidence are preserved.

| Fixed group | States | Old geometry pass | New local geometry pass |
| --- | ---: | ---: | ---: |
| Original seeds | 2 | 2 | 2 |
| Eight coarse selections | 8 | 8 | 8 |
| Frozen curvature-only rejections | 2 | 0 | 2 |

The rejected states are reference-n6-N trial 94 / iteration 17 / backtrack 0 and
reference-n8-N trial 50 / iteration 12 / backtrack 0. The exact named coordinates
and every recorded physical transformation are unchanged. The check covers the
entire straight coefficient path from the original seed, not only its endpoints
or sampled curvature. These are padded binary64 analytical bounds, **not rigorous
interval proofs**.

## Work and retained evidence

Execution at clean `c7562cafc1cb2d228d64c9e624343f25649c9b16` exits zero after
45.184 s and explicitly returns the complete study. Source and clean status
match before/after. No retry, raised limit, concurrent heavy job, environment
sync, field calculation, gradient or equilibrium solve.

- All **336 physical-curve instances** pass construction and independent checking.
  Each side evaluates **285,528 rectangle bounds**. The complete trees have
  142,596 split nodes and 142,932 passing leaves; all splits happen along the curve
  parameter. No pending, unresolved, arithmetic-failed or deadline leaf occurs.
- Each of 24 state phases reconstructs the original geometry gates. The original
  curvature failures remain false for the two rejected states; all seven other
  original gates match and pass. The new classification is a separate result.
- Every passing bound is strictly positive and <=12/m. The largest is
  11.9999293313/m. Adaptive subdivision stops at the threshold, so this number is
  **not** an estimate of true maximum curvature or an optimized safety margin.
- Producer phases take 1.483–2.676 s and audits 1.218–1.928 s, versus separate
  120 s caps. Largest combined scientific report size is 3,665,803 bytes per
  state, below 64 MiB. These timings describe this run, not a portable benchmark.
- Main's read-only saved-graph reconciliation rehashes 747 direct references /
  31,376,319 bytes, checks explicit returns, all copy identities, unchanged gates,
  byte/work counts and state classifications. It does not rerun numerical bounds
  or recursively replay the historical source graph.
- Independent internal record review checks 870 unique files / 48,322,630 bytes,
  1,321 reference edges and 26 Git objects, including all new execution files.
  All 24 explicit parent returns and source/checkpoint chains reconcile; no
  mismatch. It separately checks saved tree coverage and split choices, not
  numerical bounds, original runtime or disk measurements. Maximum work per
  curve is 1,473 attempted bounds, well below 16,383; maximum t depth 12 of 14.

[Machine-readable evidence](../../evidence/local-curvature-results-v1.json) binds
the study, both reviews and all fixed-state summaries. Raw reports remain under
`artifacts/local-curvature-v1/execution/`; the full
regression before execution passes 5,110 tests. Software success, a tighter
geometric check and physical acceptance are separate claims.

## Scientific consequence and next experiment

We can now test the two already frozen proposals' fields without confusing a
conservative geometric rejection with an actual violation. The minimal proposed
follow-up compares those proposals with their own reference-N selections: four
fixed states, matched diagnostic grids, original coarse flux normalization and
currents frozen for refinement. No optimizer or adaptive candidate selection is
needed to answer that first question.

That field experiment needs its own registration and independent checks. It has
not run. No field limit, physical admission, Step 4A–4D completion, state-of-the-art
advance or MS1 follows from this geometry result.
