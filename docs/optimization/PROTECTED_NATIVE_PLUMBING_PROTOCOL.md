# Protected native plumbing: qualification before field work

Registered 26 September 2026 after synthetic cell qualification at `ef23278`.
[Integrated results](PROTECTED_CELL_RESULTS.md) ·
[Original scientific protocol](PROTECTED_COIL_FIT_PROTOCOL.md) ·
[Method clarifications](PROTECTED_METHOD_REVIEW.md)

## Scope and boundary

Qualify the remaining source-to-adapter and parent/worker process connections.
This registration permits synthetic tests, small synthetic subprocesses and
read-only construction of contexts from already saved native data. **It does not
permit a new native field calculation, certificate study, equilibrium solve or
coil search.** A native pilot still needs the separately qualified physical
reconstruction/auditor and a committed execution checkpoint.

No search parameter, geometry/field limit, resolution or historical source changes.
Preserve the existing core/controller/ledger/store and their qualification identities.
Use fresh artifacts; failures and partial tails are evidence, never resumable runs.

## Source and native adapter contracts

1. Reuse `protected_coil_fit_inputs.sources(root)` unchanged. Separately bind the
   new code/tests/protocol and the completed synthetic qualification evidence.
   Build exactly the eight registered contexts: original geometry seed, admitted
   audit report 3 or 9, original historical seed operation/snapshot/arrays, target
   pair and fixed normalization. Load old arrays with their original hash-checked,
   no-pickle loader; do not impose the new canonical ZIP encoding on old evidence.
2. Provide an explicit `NativeAdapter` with `initialize`, `certificate`,
   `invalidate` and `bundle`, matching the qualified injected-cell interface.
   Native imports remain lazy and stubbed in this qualification. Reuse the frozen
   `run_clear_coil_field_start.make_model/execute` calls; preserve archived interior
   targets, full named physical coordinates and grids 256/64/64/32/0.
3. Both model constructions start at the original seed. The main model serves
   startup/search; the second serves only selected replay. Invalidate `_cache`
   explicitly before each bundle. Convert native metadata to plain JSON state
   and retain all sixteen raw arrays. No hidden extra evaluation or normalization.
4. The certificate adapter receives the original seed/report and full candidate
   coefficients, never the most recently accepted state as a replacement seed.
   Exact counts remain one initialization loop-A per model and nine requests per
   bundle; maximum 290 requests, 128 certificates and 32 bundles per cell.

## Time, disk and process supervision

Run serial cells in new owned POSIX process groups. Leave dependency installations
and external checkouts untouched. Set single-thread environment before worker
imports. Keep the original 3 GiB start reserve, 2 GiB ongoing reserve, 0.5-second
parent poll and five-second termination grace; terminate only the owned group.

The 1,800-second cell clock starts in the parent before config/launch work and
includes imports and source binding. The independent 600-second search clock:

- Starts immediately before forwarding the controller's `search_started` event.
- Includes the entire search call, completion checkpoint, report serialization
  and selection bookkeeping.
- Ends at the attempted replay-model initialization, only after checking the
  search deadline and before replay work. If replay initialization never occurs,
  the search clock stays active.

Journal proxies must forward unchanged payloads; no monkeypatch of the qualified
cell/controller. Use a dedicated bounded inherited control pipe for ordered
`search_started`, `search_ended` and `returned_result` messages. Bound framing and
types before parsing; each message fits one atomic pipe write. Send the search
start before potentially blocking phase-record persistence. The parent enforces
both deadlines even when the child is wedged inside native code. Strict finite,
forward shared-host monotonic clocks and parent identity are required.

Do not infer phase changes or successful completion by discovering worker JSON
files. The worker sends a returned reference only after `run_cell` actually returns
and source revalidation succeeds. The parent acknowledges it only after timely
successful exit, unchanged source/case/thread identities and checked result bytes.
Record the parent's received phase boundaries and acknowledgement separately.
Failed acknowledgement or post-computation source drift leaves an unadmitted run.
Never retry automatically or transfer unused budget between cells.

## Qualification and failure controls

- Build and validate all eight contexts read-only against the actual admitted
  source graph; preserve reference and selected targets and all old rejections.
- Stub native construction/execution to verify both original-seed models, exact
  class/method/grids, archive-source forwarding and complete metadata conversion.
  Reject changed sources, incomplete arrays and mismatched operation identity.
- Tiny synthetic subprocesses test normal acknowledgement, nonzero exit, missing
  returned reference, malformed/duplicate/out-of-order phase messages, truncated
  pipe data, parent disappearance and source/acknowledgement failure.
- Fake clocks test exact 600/1,800-second boundaries without long sleeps. Short
  injected test deadlines check termination of a wedged child/group. These are
  test-only controls, not configurable scientific run limits.
- Inject initial/live disk denials, journal/publication errors and failed signal/
  wait operations. Preserve successful prefixes, reject discovered result files,
  and ensure no success acknowledgement follows a poisoned execution.
- Independently review, run focused/public/docs/full regression, and bind exact
  committed sources and retained artifacts before closing this plumbing gate.

The architecture was independently mapped by `protected_budget_impl`; this is an
internal design review, not tested implementation. Physical reconstruction will
separately reuse the qualified independent target/metric/direct-B/A and cumulative
certificate auditors, with the protected low-mode FD directions. It must not reuse
the older full-space FD stencil or seed-only identity checks for changed candidates.
Even successful plumbing leaves native numerical replay, fine-grid acceptance,
realized-field transfer and work packages 4B–4D open.
