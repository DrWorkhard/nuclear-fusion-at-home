# Receipt-bound proposal coil diagnostics

Prospective component qualification, 7 October 2026. The decision is whether the
[qualified fitting adapter](ISSUE37_COIL_ADAPTER.md) can feed proposal snapshots
through the same fine-field and continuous-geometry checks as archived targets.
The [joint diagnostic entry points](../../src/fusion_baselines/joint_coil.py)
reconstruct each target afresh through trusted solver-receipt intake. Candidates
cannot supply target arrays or normalization. Freeze a private snapshot copy;
require its input/Wout/parent binding, named physical coordinates and fixed current
mapping; recheck all bound sources and receipts after every diagnostic.

`coil_check` shares its existing native-coil mapping, field sampling and metric
implementations between the two routes. The reference401/selected401 wrappers
retain their registry gates. No limits, normalization, current signs, quadrature
grids or error formulas change. Joint wrappers also reuse existing `coil_fit.fine`
and continuous geometry checks. A numerical-check pass is distinct from the
reported boundary, interior, current and geometry acceptance gates.

## One cached-seed diagnostic qualification

Use only the unchanged plus-target startup snapshot from local immutable
`evidence-issue37-coil-adapter-v1` at archive
`bf305779d02d4583bf13799f4d54cbcc11441296`, and the already qualified plus solver
receipt/Wout from `evidence-issue37-solver-qualification-v1` at archive
`b8d629a192d933ce22de523a57ca854a4c156963`. Pin exact bytes before execution.
No new solve, optimization, candidate adjustment, extra proposal or retry.

One **180 s total budget**, both UTC/monotonic clocks (5 s disagreement limit),
one native thread, 256 MiB aggregate output and 3/2 GiB initial/live disk reserve.
An external process-group watchdog owns interruption and cleanup. Charge native
startup, all repeated target intake, hashes, diagnostics, serialization and final
checks to that budget. Keep failures and late results; none can pass qualification.

Run fine boundary checks at 128² with shifts 0 and 0.5, 512 coil nodes; then
interior levels (32,256), (64,256), (64,512); then existing continuous geometry
refinement. Require all independent B/A comparisons to pass the unchanged 1e-12
gate, exact frozen snapshot identity and unchanged source/native/receipt hashes.
Report every existing physical gate and metric, including failures. Do not require
this unoptimized seed to pass physical gates to qualify the software route.
No current renormalization is permitted during diagnostics. Compare all independent
field arrays in a fresh archive replay; record its limits separately from original
native execution. Archive full arrays/records, retaining only a short active summary.

Review source and exact launcher before execution. This checks only the cached
plus snapshot and these diagnostic routes. Direct tracing, ideal-action scoring,
joint orchestration and the common realized-field endpoint remain separate
prerequisites. Full joint execution and physical admission stay disabled.
Agent review is not external physics review; cached solves remain chargeable under
the future joint-arm protocol.
