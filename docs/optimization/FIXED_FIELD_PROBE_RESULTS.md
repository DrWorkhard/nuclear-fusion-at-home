# Fixed proposal fields: small resolved gains, absolute limits still missed

26 September 2026. [Protocol](FIXED_FIELD_PROBE_PROTOCOL.md) ·
[Qualification](FIXED_FIELD_PROBE_PROGRESS.md) · [Index](README.md)

## Result

Both previously curvature-blocked proposals improve normal-field RMS beyond the
preregistered empirical numerical margin. Only the six-base-coil case also clears
the interior-vector margin. Both require less current. This establishes a small
useful extension beyond the former curvature certificate on these two fixed
steps, not a generally effective search method or an acceptable coil design.

| Measurement | Six base coils: predecessor → proposal | Eight base coils: predecessor → proposal |
| --- | --- | --- |
| Normal RMS, shifted fine grid | 0.2747216432 → 0.2745649473 | 0.2679463207 → 0.2677716465 |
| Relative normal reduction | 0.057038% | 0.065190% |
| Normal gain / required empirical margin | 1.5669582e-4 / 1.5106806e-7: resolved | 1.7467425e-4 / 1.3923978e-7: resolved |
| Interior-vector RMS, finest inner grid | 0.3633472495 → 0.3627490760 | 0.3572059680 → 0.3567899973 |
| Interior gain / required empirical margin | 5.9817354e-4 / 4.8926027e-4: resolved | 4.1597067e-4 / 5.4934295e-4: unresolved |
| Current, fixed during refinements | 283,050.459 → 281,674.756 A | 210,475.105 → 209,610.793 A |

Normal limits remain RMS `1e-4` and maximum `1e-3`; interior-vector RMS remains
`0.01`. **Every state on every grid fails all three field-quality gates.** All
currents pass the unchanged 500 kA gate. Normal error is still about 2,680–2,750
times its limit. Neither energy efficiency, complete engineering feasibility,
Step 4A–4D, a state-of-the-art improvement nor MS1 is established.

## Fixed comparison and interpretation

The four states were fixed before fields: original reference-N selections
(trials 93 and 49) and the exact next proposals (94 and 50). Their geometry was
already independently certified by the [local curvature study](../geometry/LOCAL_CURVATURE_RESULTS.md).
The old negative decisions remain intact. Each state has six matched resolutions,
its own original-seed coarse flux normalization and that coarse current frozen
for refinement. No gradient, optimization, candidate selection, retries or raised
caps occurred during this experiment.

The normal claim requires positive deltas on all four boundary grids and a gain
above `1e-7 + 4*(control variation + proposal variation)` on both finest grids.
The vector claim uses all three inner grids with its separate margin. All
numerical prerequisites pass. These margins are empirical diagnostics, not
rigorous discretization bounds or confidence intervals. The unresolved vector
gain is retained as unresolved, despite its favorable displayed sign.

Both proposals also pass their original strict counterfactual Armijo inequality:
native objective `0.03533745124199698 <= 0.03574020711548009` (six coils),
`0.032719557082775776 <= 0.03304822327847573` (eight). Independently reconstructed
objectives agree with those decisions. This does not retroactively accept them
into the old search. All sampled normal maxima decrease as well, but no resolved
maximum-error claim was registered. Current reductions are 0.4860% and 0.4106%;
current alone is not a reactor power-consumption model.

## Actual work and verification

The committed checkpoint runs once at clean
`4f13685453037afdf24263665d3a9fa1009e82f1`, exits zero after 347.381 s and explicitly
returns its study index. Before/after source identities and clean status match.

- 24 owned models, exactly **168 native requests / 804,864 requested points**.
- All 24 original-seed initializer checks and metric reconstructions pass.
- Independent sampled B/A reconstruction covers 144 statistics / 9,216 vectors
  (27,648 scalar components); largest relative error `1.4787768e-15`, limit `5e-10`.
- All 20 refinement checks pass; largest `abs(fine-coarse)/coarse` is
  `0.0001924957082`, below `0.01` (alternative absolute limit `1e-7`).
- All 24 diagnostic loop-flux checks pass; largest relative error
  `4.4174371e-16`, limit `1e-6`. These are not the full omitted line/fan/Stokes
  flux qualification or a field-topology/confinement check.
- Main replays all four saved parent-return validations with original control
  frames. This is same-code metadata replay, not a second field calculation.
- A separately authored internal review rehashes all 449 new execution files and
  1,554 reference identities /184,293,441 bytes, independently reconstructs the
  scalar decisions and reconciles all work. It checks 540 current source files,
  25 runtime files, 112 original physical copies and 672 model-copy bindings.
  Its graph expands 428 JSON documents; 370 older JSON leaves are hashed but
  deliberately not recursively interpreted. No new B/A or geometry calculation
  occurs in this review, and it is not external peer review.
- The existing 5,654-test clean regression qualifies the unchanged implementation;
  its 334 warnings remain recorded. It does not establish physical acceptance.

All four phases explicitly complete. Recorded supervisor intervals are
75.839/60.492 s and 79.943/66.072 s (producer/audit), below the separate 600 s
limits. These intervals precede final parent replay/publication; they are not
independent measurements of the entire phase. Final complete flags include the
parent deadline checks. Final charged payloads are 28,004,655 and 30,594,524 bytes,
below each pair's 512 MiB cap; the shared study index is charged fully to each pair.
These are recorded observations, not portable performance guarantees.

On all four macOS child exits, attempted group signalling records `EPERM` after
exit was observed. The qualified supervisor then reaps the owned leader and
confirms the group is absent; records report `reaped=true`, `retired=true`,
`signalled_before_reap=false`. This is the reviewed deferred-error path, not a
claim that the signal itself succeeded.

## Reporting corrections retained

The first summary helper rejected the older pretty-printed input manifest when
it used the canonical new-run JSON reader. It was corrected to verify the exact
registered bytes before parsing; the failed invocation is retained. No scientific
run was retried. Its subsequent display formula divided refinement differences
by `max(abs(coarse), abs(fine))`; a separate retained correction uses the registered
coarse denominator. The maximum happens to be identical, and actual acceptance
always used the correct predicate. No decision changed.

An intermediate chat update also read the current-delta sign backwards. The saved
comparison defines it as proposal minus control: both currents **decrease**.
The table above uses the individual states, independently of that sign convention.
Original measurements, summaries and corrections remain linked, not overwritten.

## Consequence

Proceed to a separately registered small continuation experiment from the two
fixed proposals, retaining normal-objective selection and independent checks.
The original seed remains the geometry reference. Tighter curvature does not
remove conservative clearance limits or justify extrapolating these tiny gains
to feasibility. A parallel diagnosis of the large target-field mismatch is
appropriate before investing in longer searches.

[Machine-readable results](../../evidence/fixed-field-probe-results-v1.json) bind
the explicit study, saved rows, reviews, corrections and qualification. Raw arrays
and reports remain under `artifacts/fixed-field-probe-v1/`; this is native local
evidence, not a standalone portable public evaluation bundle.
