# Current verification

Updated 27 September 2026. Git retains earlier verification records.

## Fixed-candidate interior screen completed

Clean implementation `8fae8b0` evaluates all five fixed snapshots at all three
levels. Best fine interior-vector RMS is **0.04029150094**, **73.6556% below**
the matched control's 0.1529415940. Every candidate still fails the 0.01 limit.
No optimization, VMEC solve, current renormalization or physical acceptance.

- Worker **6.747 s**, supervisor **7.292 s**, 14,580,923-byte family; within the
  180/185 s and 128 MiB limits. 138,240 native B points, 5,120 A points and
  1,920 independent sample comparisons. All fifteen numerical rows pass.
- All **80 source hashes** verified unchanged. Separate saved-array arithmetic
  recomputes all fifteen vector-error/per-surface/field-amplitude/loop-flux
  summaries and sampled B/A comparisons. Four prior geometry reports are joined
  to exact matching snapshots, not recalculated.
- Largest interior-grid RMS change: 5.723e-5. Coil-node refinement changes RMS
  by at most 2.776e-17; these are empirical resolution checks, not error proofs.
- The original seed's finest interior RMS reproduces 0.37123798260413354.
- MPI logs one sandbox TCP bind warning; the single-thread worker and checks
  complete. Stderr remains preserved; MPI networking was not enabled.

[Result and limitations](../optimization/INTERIOR_FIELD_EXPLORATION.md) ·
[Source-bound evidence](../../evidence/coherent-interior-v1.json).

## Software and retained failure

The exact-flux repair passes **51 focused tests** (0.89 s), including committed
input identity and rejection of a one-ULP change. It uses the original saved
−0.03141592653589793 Wb, with no tolerance relaxation. The failed recomputation
from π/100 is retained at the freeze tag/cleanup commit.

Latest public check: **48 tests pass** (3.243 s); focused Ruff, documentation and
whitespace checks pass. The cleanup commit `fbfbe47` retains the 404-test active
regression and local Python 3.11/3.12 copied-tree qualification. No new dependency
sync or hosted CI run.

Next work is a longer/wider trade-off study, not more acceptance machinery.
Realized topology, Step 3 benefit transfer, pressure/engineering and MS1 remain
open. Optional dependency pruning and independent backup/reproduction remain
unverified as documented previously.
