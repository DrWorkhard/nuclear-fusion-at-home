# Registered-target coil-model adapter

Prospective component qualification, 7 October 2026. The decision is whether the
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
