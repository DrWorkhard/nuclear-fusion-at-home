# Receipt-bound proposal coil diagnostics

Component qualification registered and executed on 7 October 2026. The decision is whether the
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

## Result

The single qualification passed at clean producer/evaluator
`86c41991ae061e6fad5b2a12bdc58706169c9b70`: 25.531 s driver, 25.759 s supervised,
clock discrepancy below 0.00021 s. Maximum independent field discrepancy was
5.908e-16; physical mapping 3.670e-15. Frozen scale stayed 3.0836165035402443.
Geometry/current/flux gates passed. Boundary RMS/max and interior gates failed:
worst fine RMS 0.002451116292, maximum 0.009995554386; finest interior RMS
0.012895263145. These retained failures are unoptimized seed diagnostics, not a
joint result. No solve, optimization or tracing ran.

Local archive `2b447838c523e6c63ce647aa379e8837d4bd46f5`, prepared tag
`evidence-issue37-coil-diagnostics-v1`, preserves all 22 raw files (6,575,718 bytes),
exact scripts and replay recipe. Its 28-entry manifest SHA256 is
`d1a62ae25d1cab2d8909978af687b36b4254b5be3fcc694ba0161e07bf80d22a`.
Publication is pending; the separate solver archive and native environment remain
explicit dependencies. Fresh shallow array replay verified 67 source/input/native
bindings, reproduced every saved independent B/A comparison with zero discrepancy
and field metrics exactly in 0.430 s. It did not repeat native fields, numerical
intake, geometry, solver execution or historical timing. Fresh shallow producer
checks passed 413 research tests (25 focused), 61 public tests, docs, Ruff and diff.
Read-only adversarial review preceded execution; full joint execution stays disabled.
