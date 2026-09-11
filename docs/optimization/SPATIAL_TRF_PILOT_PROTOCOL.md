# Controlled residual-representation pilot v1 — 2026-09-11

Declared after full-grid and single-point analytic VJP qualification, before
optimization. Test the representation, not different weights or acceptance limits.

Use the original guarded preparation, unchanged field/curve grids, targets,
207 physical parameters, x=x0+0.01*y, and frozen normalization from the guarded
study. Start every arm at that same original physical point; verify its hash.
No best-candidate warm start. Hold construction and solver settings fixed.

Two representations: scalar (eight common components) and spatial (replace
only the flux component by its 1024-entry objective-preserving factorization).
Run the same dense exact TRF solver/options as guarded construction. Two repeats
per representation; each has a cap of **128 complete proposal evaluations**,
including seven original seed-42 directional probes. Original gradient tolerance
and repeat-identity tolerances remain unchanged. No feedback from holdouts.

This cap is **not equal computational work**. Each active spatial proposal adds
1024 single-point B calls and 1024 analytic VJPs; time/count these separately.
Both representations evaluate the original full common vector/Jacobian first.
For every spatial proposal require scalar merit and exact gradient identity to
relative/normalized tolerance 1e-10. Count any failure and stop; do not silently
switch representations. Retain the original common vector for every proposal.

Best selection uses the solver's residual merit and retains the full physical
array and serialized field. Check the archived arrays and proposal accounting.
If both arms repeat, run the unchanged 128x128/800 flux and 20,000-point geometry
holdout, continuous curvature and inter-coil enclosures on both first-repeat
best fields. A failure or unresolved bound cannot be waived.

Interpretation: an equal-proposal-cap pilot can show different search paths and
candidate quality. It cannot establish compute efficiency, multi-start ranking,
convergence or SoTA. The 128 proposal cap is short and fixed, not a feasibility
guarantee. Further experiments require separate declarations, not an unlogged
budget extension. All existing physics/engineering/SQuID-C gates remain in force.
