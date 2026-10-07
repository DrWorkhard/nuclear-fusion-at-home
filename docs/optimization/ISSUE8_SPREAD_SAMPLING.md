# Prospective test of a spread boundary sample layout

**Decision:** whether one fixed spatial layout merits work on a new public boundary
case. [Issue #8](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/8) identifies
mirror duplicates and structurally zero checks in the legacy 64-point helical sample.
This pilot tests a replacement layout against existing frozen candidates; it does
not change that case, its evaluator, candidate coefficients or acceptance gates.

Use the unchanged 64x64 reference boundary reconstructed by `fusion_public.dense`
from the committed reference401 input. Indices are `64*j+i`, with toroidal grid
index j={2,6,10,14,18,22,26,30} and poloidal index i={4,12,20,28,36,44,52,60}.
These 64 tensor-product midpoint samples cover half a field period, excluding
the symmetry planes and all mirror pairs. They use the corresponding existing
surface-area weights, renormalized over the sample. No random seed, adaptive
placement, optimizer or tuning against fields is involved.

Freeze three existing candidates before running: the public seed,
`length-headroom-six-coil`, and `millimetre-ranking-counterexample` (the published
+2 mm perturbation). They retain the original public case's physical-copy matrices,
signed currents and coefficient convention. Compute direct scalar fields at all
4096 boundary points with both 256 and 512 coil nodes. From the same fields,
record dense RMS, legacy-sample RMS and spread-sample RMS, plus both sparse layouts'
relative RMS error against the dense result. This separates spatial sampling from
filament quadrature; it is not an independent field implementation or hidden holdout.

Proceed to new-case work only if all preregistered checks pass:

- Every candidate's spread RMS is within 5% of dense at 512 coil nodes and closer
  than its legacy RMS.
- Every candidate's dense, legacy and spread RMS changes by at most 0.1% between
  256 and 512 nodes, relative to the 512-node value.
- The known counterexample remains worse than headroom on dense RMS, better on
  legacy RMS, and is correctly ranked as worse on spread RMS at 512 nodes.

A failed criterion means retain the negative pilot and do not promote or retune
this layout here. A passing pilot only warrants a separate new-case proposal;
three known examples cannot establish broad ranking reliability, a maximum-error
bound, full independent constraint count or physical acceptance.

One attempt, one process doing field arithmetic, one thread: 300 s driver including
its imports/startup, 360 s supervised total, 32 MiB aggregate output, 3/2 GiB initial/
live disk reserve and 5 s clock discrepancy tolerance. Reuse the previously reviewed
owned-process and final-receipt helper, hash-bound to its original source; explicit
outer checks enforce this smaller study's limits. The worker uses isolated Python
with site packages disabled and only the standard library. Save full B vectors,
signed normal errors, geometry, completed levels, failures, timings, exact source/
input/Python identities before/after, and the decision. No retries or larger grids.
Preserve the native environment and raw files; archive evidence separately and keep
one short result. Adversarial agent review is not external peer review.
