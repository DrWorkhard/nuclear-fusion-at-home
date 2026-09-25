# Protected runner: durable event-storage qualification

Registered 25 September 2026, before implementation or tests. This is the next
software component after [controller qualification](PROTECTED_SEARCH_SOFTWARE_RESULTS.md),
not permission to execute the [unqualified native pilot](PROTECTED_COIL_FIT_PROTOCOL.md).

## Contract

Implement a small standard-library event journal for the controller's synchronous
`record(event)` callback. Use a fresh directory and exclusive, numbered files;
never overwrite a recorded event, restart a failed writer or silently resume a run.
Each canonical UTF-8 JSON record binds its sequence index, previous record's
SHA-256 and a private serialized payload. Return a count/head receipt only after
the file is flushed/fsynced, closed and the containing directory is fsynced.
Sync creation of the fresh journal directory too. This POSIX research component
does not claim Windows support or survival guarantees beyond the OS/filesystem.

Any validation/write/flush/fsync/publication failure poisons that writer: all
later calls fail before further writes. Preserve every previously successful file
and any partial failing tail for diagnosis. Do not erase or reinterpret a
reservation as proof that a native call did not happen. The controller already
stops if recording fails; test that composition directly.

Reader checks use an externally supplied count/head receipt, not an inferred head:
exact sequential filenames and schemas, finite JSON, no duplicate keys/symlinks,
hash-chain consistency and exact receipt identity. Reject missing, extra,
truncated, reordered or changed records. Bound one record to 8 MiB, the journal
to 2,048 records and JSON nesting to 64 levels. These are defensive storage caps,
not changes to the scientific/native-call budgets. Receipts and hashes are integrity
checks, not signatures; a fabricated journal plus fabricated receipt is not proof
of provenance, correct physics or an authorized run.

## Required tests before qualification

- Successful round trips, signed zero, Unicode, private payload copies and exact
  no-overwrite behavior; fresh outputs only, strict JSON and receipt schemas.
- Mutations: changed/missing/extra/partial files, duplicate keys, nonfinite values,
  noncanonical encodings, wrong sequence/previous hash/head/count and symlinks.
- Inject open, short-write, flush and file/directory-fsync failures. Successful
  prefixes remain byte-identical; no subsequent write or callback work is permitted.
- Connect a completed synthetic protected search to the journal, read it through
  the separate reader and pass its reconstructed events to the existing scalar
  trajectory auditor. Inject reservation-record failure and prove no geometry/field
  callback begins afterward. A failed tail must not masquerade as a completed run.
- Run focused tests, public controls, documentation/Ruff checks and full regression
  before calling this component qualified. Preserve failures and bind sources/results.

## Explicit non-goals and next dependencies

No native field/equilibrium study, method tuning or physics-threshold change.
This component alone does not implement source admission, the 290-request / 128-
certificate cell ledger, raw-array snapshots, cell orchestration, independent
physical audits or fine-grid acceptance. Those remain separate runner prerequisites,
as does the second independent method review. Step 4 stays In progress.
