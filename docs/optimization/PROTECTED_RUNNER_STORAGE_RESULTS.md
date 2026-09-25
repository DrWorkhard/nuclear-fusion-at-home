# Protected runner: event-storage results

25 September 2026. [Protocol](PROTECTED_RUNNER_STORAGE_PROTOCOL.md) ·
[Controller result](PROTECTED_SEARCH_SOFTWARE_RESULTS.md) · [Index](README.md)

## Assessment

The new `protected_search_journal` component passes 47 focused tests; combined
with the unchanged controller and scalar trajectory auditor, **155 tests pass**.
The completed full-regression report records **2,229 passes, zero failures/errors/
skips**. Source and artifact identities are bound in the
[qualification record](../../evidence/protected-runner-storage-v1.json).
This qualifies synchronous event storage, not the complete native runner, a new
field fit or Step 4 completion.

## Interface and guarantees

`EventJournal(fresh_directory)` is a callable record sink for the controller.
Each call serializes a private finite JSON payload into an exclusively created
numbered file with an index and previous-record hash. The receipt (record count
and final SHA-256) advances only after file flush/fsync, close and directory fsync.
Directory creation is synced as well. The original payload and returned receipts
are not live aliases of internal state.

`read_events(directory, receipt)` requires a caller-supplied receipt; it never
guesses completion from the files present. It checks exact filenames, schemas,
indices, hashes, canonical finite JSON and size/depth bounds. The decoded events
can then be passed to the separate controller auditor. A valid chain alone says
nothing about author identity, physical truth or whether a whole study finished.

Any recording error poisons the writer. Later calls cannot write or dispatch work;
an error-record attempt does not hide the original exception. Previously successful
bytes remain unchanged, and any failed tail is retained. A directory with such a
tail cannot pass as the older completed receipt or be silently resumed. Fresh
directories are mandatory, including after a directory-creation sync failure.

Scope is a single-writer POSIX research workspace. This is not an adversarial
filesystem sandbox, a concurrent writer, Windows qualification, hardware power-loss
proof or automatic recovery protocol. A malicious writer able to replace all
records and the receipt can invent a consistent history; source/physical audits
and trusted checkpoint binding must remain separate.

## Actual checks

- Initial 38 tests: **38 pass in 0.39 s**. Expanded suite: **154 pass in 6.68 s**.
  A final bounded-directory-enumeration control brings this to **155 pass in 5.05 s**,
  comprising 47 journal tests and the prior 108 controller/auditor controls.
- Real tiny-file round trips, Unicode/signed zero, private payload/receipt copies,
  no-overwrite rules and storage caps pass. Reader controls reject changed,
  missing, extra, partial, duplicate-key, nonfinite, reencoded, wrongly indexed,
  wrongly hash-linked, symlink and malformed-receipt inputs.
- Injected open, short-write, flush, close, file-fsync, directory-fsync and interrupt
  failures leave successful prefix bytes unchanged and stop subsequent writes.
  An injected reservation failure prevents geometry/field callback dispatch.
- Both registered classes complete synthetic search → journal → reader → separate
  trajectory audit, each with 82 events; the verdict retains false physical flags.
  A separate control shows storage can faithfully carry an invented physical claim;
  it does not endorse that claim.
- Repository Ruff passes. No native field calculation, new equilibrium, installation
  or cleanup was performed for these component tests.
- The 47 separate public tests pass in 3.726 s. The docs checker initially failed
  because concurrently created `docs/steps/` pages were not yet indexed. The other
  session completed those changes at `c3faa29`; documentation and 14 documentation/
  release tests then passed. The initial failure remains in the validation log.

Initial/expanded JUnit are retained under
`artifacts/protected-runner-storage-v1/initial-tests.xml`, `targeted-tests.xml`
and `bounded-reader-tests.xml`. Their JUnit durations are 0.376, 4.970 and 5.044 s;
earlier quoted times are console observations, not a timing comparison.
No new numerical failure was observed in this component phase.

## Committed-source qualification

Registration `7a210ac`; implementation `fc831f3`. The completed full regression's
JUnit records 2,229 passes in 248.079 s, starting at 23:16:26 +02:00. The final
console/exit status was not recovered after the process session expired, so no
warning total is inferred from the previous regression. The XML is complete and
no pytest process remains. This is local native-environment evidence, not hosted CI.

All eight listed sources match their named commits, and all four retained JUnit
files are size/hash bound. The code/tests for storage, controller and auditor
remain identical to `fc831f3`. The full suite also includes the roadmap-test update
at `c3faa29`, committed before the recorded pytest start. A user README-only commit
`4374b5e` arrived during the run; this was not a frozen whole-checkout test. No
scientific source, limit, dependency or original evidence was changed for it.

Closure checks: all eight committed source identities, four artifact hashes/sizes
and four JUnit summaries match. After these documentation updates, 169 focused
storage/controller/auditor/documentation tests pass in 5.81 s; 47 public tests pass
in 3.849 s. Documentation structure, repository Ruff and whitespace checks pass.

## Remaining runner work

Implement the exact per-cell native/certificate budget ledger, immutable
raw-array snapshots, source admission and orchestration; preserve the draft's
32-bundle / 290-native-request / 128-certificate caps. The second internal method
review, independent physical reconstruction and all fine-grid gates still precede
any claimed field improvement or physical admission.
