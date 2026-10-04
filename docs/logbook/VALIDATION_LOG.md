# Current verification

4 October 2026. Archive base `68db098`; migration rebased onto `a32f30d`.
The incoming README typo correction and separate sparse interior diagnostic are
preserved. Archiving changes no runtime code, evaluator or scientific result. [Archive procedure](../validation/REPRODUCING_RESULTS.md) · [Status](../STATUS.md)

Archived 944 historical files (326,449,769 bytes) outside the default main tree.
The annotated `evidence-archive-2026-10-04` tag points to
`68db098b664bb072854b687040e103aaafee463c`; its published tag-object ID is
`6755d9ed09d034897a1a6106eb1be08a5a16cfc3`. GitHub rule 24350200 now blocks
updates/deletion of all `evidence-*` tags, preserving the original tag protections
and no-bypass policy. Historical payloads were removed only from the index;
all local originals remain intact and ignored.

| Check | Result |
| --- | --- |
| Remote archive identity | Tag object and peeled commit match local Git |
| Archived payload preservation | All 944 original Git blobs match local files; SHA-256 and size unchanged |
| Historical links | All 18 distinct pinned evidence/attribution-file targets resolve in the archive |
| Public suite | 60 passed in the integrated isolated checkout |
| Documentation, maintenance and native-input tests | 69 passed |
| Real native intake | Nine input hashes and both target grids pass |
| Docs, Ruff, `git diff --check` | Pass |
| Fresh-clone core checks | 60 public tests, 40 maintenance tests, docs and Ruff pass |
| Fresh-clone public release | All eight operations pass in the integrated isolated checkout |
| Fresh-clone archive retrieval | All 944 retired files absent from main and recoverable byte-for-byte from the tag |
| Hosted CI | Required on the pushed commit before updating protected main |

Main now has 106 tracked files, under 0.8 MB of content, versus 1,048
files / 327.22 MB at the archive base; the two additional source/test files came
from the incoming diagnostic. Two active reference inputs total
208,154 bytes and retain their original hashes. Root README and runtime code match incoming main; public candidate JSON,
native environment and raw experiment outputs are unchanged.
No native solve or broad numerical regression is needed for this storage-only
change. Fresh-clone checks prove the ignored historical payload is unnecessary
for core/public workflows. The first clone check exposed two stale attribution
links in NOTICE.md; these now pin the archive and the repeated check passes.
Incoming code was inspected and executed only in a separate checkout with an
empty environment; the native research environment was not synchronized.

The previous refactor's native regression, objective-equivalence comparison and
smoke-run record remain in the archive at `docs/logbook/VALIDATION_LOG.md`.
Historical dirty states remain dirty; their base SHA alone is insufficient.
Neither this tag nor the push backs up ignored raw runs or native environments.
The archive changes checkout contents, not Git history size or scientific claims.
The owner-requested migration uses the documented sole-maintainer review
exception only after the required CI checks pass.
