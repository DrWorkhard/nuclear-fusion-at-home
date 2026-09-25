# Protected field-fit runner: software qualification

Registered 25 September 2026, before this execution-layer implementation.
[Search policy](PROTECTED_COIL_FIT_PROTOCOL.md) ·
[Qualified controller](PROTECTED_SEARCH_SOFTWARE_RESULTS.md) ·
[Qualified journal](PROTECTED_RUNNER_STORAGE_RESULTS.md)

The user authorized continued local Step 4 research and independent agents.
Publication is a separate workflow, not a prerequisite to local research. This
registration does not authorize a native experiment until all its scientific and
software prerequisites pass; the original pilot draft and numerical limits remain.

## Scope and immutable limits

Implement the missing execution components without changing the controller or
the qualified field/geometry arithmetic. First qualify them synthetically, retain
failed tests, commit exact sources and bind results. Native construction and its
independent physical audit require a further explicit readiness decision based
on that evidence and both internal method reviews. Finer-grid acceptance remains
a separate phase; no component pass completes Step 4.

Per construction cell: ten startup bundles, one fresh search seed, at most twenty
field trials, one fresh-model selected-state replay; at most 32 full bundles,
128 certificates (10 + 1 + 116 + 1) and 290 native requests (two initializations
plus nine per bundle). No cross-cell budget sharing, retries or extra model
construction. Startup/search use one model initialized at the original geometry
seed; replay uses the second model, also initialized at that seed. Certificate
rejection is a recorded outcome, not numerical failure or a field evaluation.

Each model initialization requests exactly loop A at 256 points. Each full
bundle explicitly invalidates the model cache and requests, in order:
boundary B (4,096 points), inner B (3,072), loop A (256), boundary B_vjp (4,096),
inner B_vjp (3,072), loop A_vjp (256), boundary A (4,096), inner A (3,072),
loop B (256). Native calls are reserved durably before dispatch and matched to
one outcome. A cache hit is still a request. Native failure, malformed callback,
guard or persistence failure poisons the execution object; no recovery or retry.

## Components and required checks

1. **Budget ledger.** Explicit model/operation identifiers, exact request ordering,
   per-phase and total attempt/completion counts, no unpaired/replayed callbacks.
   Every reservation precedes callback work; completion follows validation and
   durable publication. Test both model sequences, every cap and boundary, failed
   dispatch/completion, duplicate/mismatched/out-of-order work, and record failures.
   Bind certificate and bundle identifiers; budget validity alone cannot validate
   the controller trajectory or physical assertions.
2. **Immutable snapshots.** Exclusive fresh files; finite JSON and finite named
   numeric arrays only, no pickle/object payloads. File flush/fsync/close and
   directory fsync precede returned hash/size references. Retain partial tails on
   error; do not overwrite or resume. Snapshot references enter a journal only
   after persistence. Test mutations, malformed data, overwrite and I/O failures.
3. **Source admission.** Reuse prior binders without weakening their historical
   reference graphs. Require the exact accepted 52-state perturbation audit,
   successful four-cell numerical field-start qualification and its four retained
   physical rejections; keep full named seed mappings, targets, archives and code
   identities. Test individual required flags, sources and missing/changed records.
   A read-only real-data preflight may verify availability; it is not a field run.
4. **Composition.** Only after these pieces qualify, connect them to the controller
   and counted-field callbacks under synthetic doubles. Require an exact replay,
   independent completed-trajectory audit, all reservations/raw results and final
   externally bound receipts. Inject storage/guard/native/certificate failures at
   representative boundaries; completed-prefix evidence must survive and dispatch
   must stop. A self-consistent fabricated physics history stays physically unverified.

Validate the native-specific exact-index/boolean schemas and finite clocks; do not
silently accept booleans as counters or normalize mismatched parameter identities.
The single-writer POSIX assumptions of the journal apply to storage as well. This
is an owned research workspace, not a sandbox for untrusted PR execution or a
hardware power-loss guarantee. Hashes establish byte identity, not authenticity.

## Resource and completion gates

No installation, dependency sync or pinned-checkout edits. Existing one-thread
1800-second whole-cell and 600-second search limits, 3 GiB starting / 2 GiB ongoing
disk reserve, serial fresh worker processes and no competing heavy jobs remain.
No native run merely to debug the runner. Unit/fault tests, public checks, docs,
Ruff, full native-environment regression, independently authored review and exact
source/result binding precede a component qualification claim. Record partial
completion explicitly; an implemented component is not a qualified native runner.
