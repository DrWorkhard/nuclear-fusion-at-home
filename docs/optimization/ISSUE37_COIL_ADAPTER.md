# Registered-target coil-model adapter

Component qualification registered and executed on 7 October 2026. The decision is whether the
[receipt-bound plus equilibrium](ISSUE37_SOLVER_QUALIFICATION.md) can enter the
existing normalized coil model with the exact original six/order5 seed and
unchanged objective, derivatives, current rule and geometry penalties.
[`joint_coil.py`](../../src/fusion_baselines/joint_coil.py) consumes the trusted
parent receipt through numerical intake, binds the frozen seed hash, reconstructs
the model on the proposal boundary and recomputes the seed's signed unit flux.
Only scalar currents are renormalized; named coordinates and geometry stay fixed.

Snapshots carry the proposal input, Wout and parent-receipt identities and the
original reference B² normalization. They cannot masquerade as reference401 or
selected401; those registries and acceptance paths remain unchanged. The adapter
can freeze a completed fitting row's coefficients/currents for future diagnostics;
serialization itself is not evidence that the row wins selection or passes gates.
The typed invalid-trial followup `4ceaedc914dcbb47f890a7bf788daef768c29370` is included:
only known numerical objective-domain failures are recoverable during search.

## Single startup check

Use the preserved original seed at SHA256
`84bbdf3eca274981dfff80c967b6fd623a1a40350e583407cbb7262c26820217` and the existing
plus Wout `09c3b2afdbdc1da5b5d668590b60088d8b011c0abf0337fd2ec7fc170e8cf38d` with
its trusted qualification receipts. No new equilibrium solve, optimizer iterations,
other seed/proposal or retry. This is a cached-input software check, not a joint arm.
Charge its intake, identity verification, native startup and reporting to one
120 s budget; one thread, 256 MiB output, 3/2 GiB initial/live disk reserve.
Use both UTC/monotonic deadlines with 5 s maximum disagreement and an external
process-group watchdog. Preserve all failures and late results as ineligible.

Invoke unchanged `coil_fit.search` through its usual two named derivative directions
and two finite-difference steps, plus exact objective/gradient repeat. Replace only
the optimizer invocation with an explicit no-iteration return; it must be reached
exactly once after passing startup. Retain every startup/probe row. Serialize the
startup seed row under its own name, verify exact original coefficients and names,
new-target current normalization and unchanged receipt/source/native module hashes.
Report field and geometry terms separately; no feasibility requirement is imposed
on this unoptimized seed. A failed derivative or identity check blocks integration.

Freeze the source before execution and obtain read-only adversarial review first.
The generated evidence belongs in a separate archive, including exact launcher,
driver, native module hashes and reproduction requirements. Agent review is not
external physics review. Success clears only this fitting adapter's startup path;
the full joint comparison, ideal-action scoring, proposal diagnostics and common
realized-field endpoint remain separate prerequisites. Cached solves must be
charged/recomputed under the future joint-arm protocol.

## Startup result

At clean producer/evaluator `59f5a00aeba48f45b5e55aacf54cbbcdd8fc414f`, the single
cached-plus startup **passed** in 14.465 s (total supervision 14.783 s).
All ten evaluations completed, all four derivative checks passed (maximum absolute
error 1.629e-8), and objective/gradient repeated exactly. Original named geometry
remained exact; new-target base current was 308361.650354 A. Seed boundary RMS
0.00245112 and maximum 0.00999555 are unoptimized sampled diagnostics above the
physical acceptance limits. There were no optimizer iterations or new solves.

Local archive `bf305779d02d4583bf13799f4d54cbcc11441296`, prepared tag
`evidence-issue37-coil-adapter-v1`, preserves all 29 raw files (265,710 bytes),
original seed, exact scripts and replay instructions. Its 36-entry manifest SHA256
is `c06fe1212d8fc9af40788f9e80d3e5660b82c85811bbdebc770e8b5f4f9cb13a`.
Replay also requires the separate solver archive and preserved native environment;
neither is silently included. Publication is pending. Fresh shallow producer checks
passed 388 research tests (20 adapter tests), 61 public tests, docs, Ruff and diff.
Fresh shallow replay verified 68 source/input/native-file bindings and reproduced
numerical intake and all ten startup rows exactly in 5.841 s; it did not rerun the
solver or re-attest original timing. Read-only adversarial review preceded execution.
Full joint execution and physical acceptance remain disabled.
