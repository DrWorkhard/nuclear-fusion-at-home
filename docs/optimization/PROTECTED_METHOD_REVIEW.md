# Protected field fit: second independent internal method review

25 September 2026. Reviewer: independent agent `protected_method_review`.
[Original draft](PROTECTED_COIL_FIT_PROTOCOL.md) ·
[Execution qualification](PROTECTED_RUNNER_PROTOCOL.md) · [Index](README.md)

## Recommendation and scope

**Support a bounded diagnostic pilot, conditional on the remaining execution and
physical-audit gates.** The reviewer found no new algorithmic defect in the
qualified controller or separately implemented trajectory auditor. This is an
independently authored internal review, not external peer review, a test run or
permission to skip the native prerequisites. The reviewer ran no native jobs and
changed no files.

The review used HEAD `228b78d53d831f0b0a4bcb5e52e1b88dec421e82` and these source identities:

| Source | SHA-256 |
| --- | --- |
| Original draft | `d851a1c7080c2bffcfd8b955fe94f9bdc884c78d0c6da17e169ea1462328acbb` |
| Controller | `94ad704b54c853c3c9fbd05f988429ac674b447ff4e10e9511ac50118e2fee11` |
| Trajectory auditor | `b1356dadba909e95625d67164aa238cc7500a1a8514a01e7199d8bcfb1da5798` |

The geometric prerequisite's actual hash also matches the original draft's pin.
The old draft is preserved, rather than rewritten to hide its ambiguities.

## Required clarifications and disposition

1. **Historical replay means the historical seed.** The earlier startup study
   used unweighted full-space finite-difference directions; the protected pilot
   uses low-mode `sqrt(P)`-weighted directions with full-coordinate indices.
   Their eight probe states cannot replay bit-for-bit. The executable runner must
   exactly reproduce the original seed's value, full gradient, metrics, snapshot
   and numerical arrays, then independently qualify its eight new probes and
   repeat seed. NPZ container bytes need not match when their array bytes do.
   Do not reuse the old `qualification_points`/`derivative_checks` unchanged.
2. **There are exactly two models.** Startup, the new search-seed evaluation and
   search trials share the first original-seed model, explicitly invalidating its
   cache before each bundle. Only the final selected-state replay creates another
   model, also at the original seed. A “fresh search seed” means a fresh evaluation,
   not a third initialization. This schedule is explicit in registration `7602404`.
3. **Objective descent is not automatically physical improvement.** Own `J`
   includes fixed-target normalization and geometric penalties, whereas normal
   RMS divides by local magnetic-field magnitude. Lower `J` need not lower either
   reported field-error metric. Passing the 1% refinement check also cannot resolve
   every arbitrarily small gain. For this diagnostic pilot, report the distinct
   objective and physical-metric changes and numerical checks, but make **no
   resolved fine-grid improvement or Pareto-dominance claim** without a separately
   preregistered matched-grid, metric-specific numerical-resolution margin. This
   restriction is fixed before results; thresholds remain unchanged.

The first two clarifications are executable requirements for integration tests.
The third takes the reviewer's explicitly offered conservative reporting option;
it does not change the absolute physical acceptance criteria or enable Step 4
completion from diagnostic output alone.

## Checks made by inspection

- `P` is applied once. Maximum per-base-coil D0 normalizes physical displacement;
  inactive coefficient bits remain unchanged.
- Every certificate is cumulative against the original seed; geometric rejection
  does not consume a field trial. A conservative rejection is not physical impossibility.
- Selection excludes finite-difference probes and rejected trials, with first-seen
  ties. Fresh selected-state replay is not a second full search trajectory.
- Fine calculations freeze the selected coarse current and cannot influence selection.
- Construction maxima per cell: 32 bundles, 128 certificates, 290 native requests.
  Fine phase: 80 further requests; total 370 per cell / 2,960 for eight cells.
- The scalar trajectory auditor explicitly leaves field, gradient, geometry and
  source truth unverified. Historical seed-only identity helpers are not candidate
  validators; new checks must preserve original-seed provenance explicitly.

## What the experiment can teach us

It can test whether reproducible low-mode descent lowers the optimization
objective while retaining certified geometry, and identify whether conservative
geometry bounds stop useful motion. At most twenty accepted 1 mm steps permit
only about 20 mm cumulative D0 movement before further certificate restrictions;
the starting normal RMS is about 2,700 times its physical limit. A negative or
modestly positive local experiment cannot establish optimality, impossibility,
method superiority, a completed 4A/Step 4, or MS1.

Remaining native prerequisites: qualified source-bound execution and raw storage,
independent physical reconstruction, runtime startup qualification and the separate
fine phase. The source-data availability check is recorded in the runner results,
not treated as execution of any of those calculations.
