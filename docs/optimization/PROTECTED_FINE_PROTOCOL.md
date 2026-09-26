# Protected selected candidates: separate fine acceptance

Registered 26 September 2026, before fine implementation or native execution.
[Coarse results](PROTECTED_COIL_FIT_RESULTS.md) ·
[Original registration](PROTECTED_COIL_FIT_PROTOCOL.md) ·
[Method limits](PROTECTED_METHOD_REVIEW.md) · [Index](README.md)

Planning by `protected_budget_impl` and independent read-only review by
`cell_integration_review` checked the fixed work totals and numerical primitives.
Initializer-current, point-count, offset, dtype and outcome clarifications are
incorporated below. These internal reviews ran no native work or tests. This
registration permits implementation and qualification, **not native execution**
before the separate committed qualification/execution checkpoint. Original
scientific thresholds and completed coarse selections remain unchanged.

## Scope and input

Validate all eight originally selected coarse states, including seed fallbacks,
in the original case order. A failed or missing coarse case remains unavailable;
it is never an implicit fallback or an omitted case. Require the explicitly
returned complete coarse-study reference and successful per-case parent return,
graph audit and independent saved-physics reconstruction before fine admission.
Fine results cannot alter selection. This is acceptance of fixed candidates,
not another optimization phase or a resolved improvement study.

Preserve the complete original coarse source graph, including its repository
metadata, as historical evidence. Bind new fine sources as a separate layer;
recheck every pinned input/artifact and source byte. Do not regenerate the old
graph at the fine commit or add general repository-identity exceptions. Contexts
bind original seeds/reports, both targets, selected full named coordinates,
cumulative certificate, selected bundle and immutable coarse snapshot/current.

## Numerical work

Exactly eight fresh original-seed models per case, with explicit case N/V method.
Each initialization calls loop A at 256 points once. Six diagnostic grids, ordered
as `(nphi, ntheta, ncoil, ninner, offset)`:

1. `(64,64,256,32,0)`
2. `(128,128,256,32,0)`
3. `(128,128,512,32,0)`
4. `(128,128,512,32,0.5)`
5. `(64,64,256,64,0)`
6. `(64,64,512,64,0)`

Each executes boundary B, interior B, loop A, boundary A, interior A, loop B,
with point counts `nphi*ntheta`, `3*ninner**2`, 256 repeated for B/A counterparts.
Two separate flux models have 256/512 coil nodes and the base diagnostic grid.
Each executes three line grids (256/512/1024 angular points, A then B), then six
fan grids (16 then 32 radial points, each with 256/512/1024 angular points,
B then A). Line requests use `ntheta` points and fan requests `nrho*ntheta`.
Total: `6*(1+6)+2*(1+18)=80` native requests per case, 640 for eight;
original construction-plus-fine ceiling remains 2,960. No gradients, new field
warm-ups, equilibrium solves, candidate changes or budget transfer.
The exact fine point-request total is 552,960 per case / 4,423,680 for eight,
including the eight 256-point initializations; repeated queries count separately.
The diagnostic half-grid offset shifts boundary phi/theta only; its coil
quadrature and initialization loop remain unshifted. This is separate from
the half-shifted coil samples in the direct geometry phase below.

Reserve operations before dispatch; persist exact callbacks, sequence, quantities,
point counts, attempts/completions and raw references. Successful raw publication
precedes operation completion. A swallowed hook/storage error poisons the cell.
Initialize at the original seed, assign selected coordinates explicitly and
verify their bits before diagnostics AND flux. The existing flux operation does
not assign x. Freeze the selected coarse current; do not call the unfrozen
snapshot helper or recalibrate to a finer flux. Record each initializer's
original-seed flux separately from the selected coarse snapshot.

## Independent saved-data checks

Use frozen target/metric/direct-field, refinement and flux primitives with
explicit method/grid and `diagnostic=True`; new storage-loading adapters must
not change their maths. Reconstruct each of eight initializer flux scalars from
the original seed at that model's coil resolution. Reconstruct all six metric
rows and all eighteen flux grids. Direct sampled B/A: 72 statistics, 4,608 vectors,
13,824 components per case. Retain all per-operation comparisons, not only maxima.
Those counts exclude the eight initializer scalar checks. Initializer “unit” flux
means the original seed at signed 100,000 A physical currents, NOT 1 A or the
selected/coarse scaled current. Independently integrate original-seed loop A
at 256 loop points and that model's coil resolution, with the original symmetry
current signs; compare each scalar at `5e-10` relative and zero absolute tolerance.

Unchanged tolerances: metric reconstruction `5e-10` relative / `1e-12` absolute;
direct B/A `5e-10` relative; the five original refinement pairs 1% relative OR
`1e-7` absolute; two complete 27-check flux blocks plus nine cross-coil comparisons
at `1e-6`. The initializer tolerance is the explicit separate value above.
Check all absolute field/current/geometry gates: normal RMS `1e-4`, normal max
`1e-3`, interior-vector RMS `.01`, 500 kA, 3.5 m, 12/m, 60 mm and 80 mm.

## Geometry and storage codec

Independently recompute the selected cumulative certificate against its ORIGINAL
seed/report. Sample four grids `(256,0)`, `(512,0)`, `(1024,0)`, `(1024,.5)`;
both source-bound 256-square full-torus target surfaces and every physical pair
are mandatory: 276 pairs for n6, 496 for n8. Record exact producer sampling work.
Independently reconstruct targets/curves/distances/witnesses using the existing
sample audit, original comparison tolerances and zero enclosure slack.
Specifically, retain `5e-12` relative / `1e-12` absolute direct-geometry raw
comparison tolerances. Read new geometry archives with canonical dtype-preserving
`read_arrays`, not the historical reader that coerces all arrays to floating point.

Only `curvature_available` receives `protected-geometry-mask-v1` encoding:
boolean `(nphysical,ncoil)` -> same-shape uint8 containing only 0/1, with explicit
original dtype/shape descriptor. Reject wrong/missing/extra descriptor, nonbinary
values or wrong dtype/shape. Restore a new boolean array before the unchanged
auditor. Preserve all other arrays and integer witnesses exactly. Do not broaden
the existing numeric-only snapshot storage contract.

## Separate no-search execution boundary

Register a separate 1,800-second fine-cell deadline measured by the parent before
configuration/source admission/import/launch. No search clock or fictitious
search-start/end messages. One canonical bounded returned-reference control
message is sufficient; its fine-specific schema must reject extras, duplicates,
oversized/nonfinite data and forward-time violations. Validate source/config/
case/threads/PIDs/clocks, exit zero and complete owned-process-group cleanup
before acknowledging the returned result. Never discover a completion file.

Retain serial POSIX execution, four thread variables equal to 1, 3 GiB starting /
2 GiB live reserve, .5-second polls, five-second TERM grace and bounded one-second
KILL/reap. Retire cleanup authority when the owned group disappears. Cooperative
worker parent checks do not promise kill-on-parent-death or untrusted-code
isolation. Parent callbacks are trusted to return; this is not an externally
supervised guarantee against a hung parent callback. Posthoc independent audits are separately timed and disk-guarded.
No automatic retry/resume. Stop the study on execution/source/audit/publication
error, preserve completed references and failed prefixes, mark later cases unrun.

## Qualification and outcome

Add only fine-specific contracts/ledger/codec, explicit native adapter, saved-data
auditor and no-search launcher/supervisor. Reuse frozen helpers at appropriate
boundaries, not construction's coarse schema or the old seed-only whole audit.
Require independent code review, focused/public/docs/full tests, committed source
qualification and a committed execution checkpoint before any native fine call.
Test both classes/methods, changed and fallback coordinates, stale flux model x,
wrong original seed/current/source, all exact work sequences/masks/pairs/surfaces,
over-budget/reentrant/swallowed errors, disk/time/pipe/process-group failures and
failed final publication. Include an explicitly nonphysical real subprocess test.

Distinguish complete software execution, independently consistent saved data,
numerical resolution/flux qualification, and absolute field/geometry acceptance.
A faithfully calculated threshold failure is retained as a complete negative
result: finish all mandatory operations and comparisons, not early skip them.
Use explicit distinct outcomes: `complete_execution` for a fully acknowledged
worker, `arithmetic_consistency` for complete independent reconstruction,
`fine_numerical_qualification` for reconstruction plus all five refinement and
63 flux checks, and `absolute_field_geometry_pass` only when numerical
qualification, all six rows' physical limits, the selected continuous certificate
and all four independently verified geometry grids pass. Do not reuse the old
cross-N/V seed identity gate for distinct selected candidates.
Malformed, inconsistent or incomplete evidence cannot pass. Keep resolved
fine-grid improvement, Pareto dominance, realized-field transfer, Step 4, SoTA and
MS1 false. No claim of every full-grid field or gradient being independently
verified, QI/confinement benefit or finite-winding engineering follows.
