# Bounded route to the missing community coil record

This follows partial intake archive `9f3d4a5a9cbb0b85a6e07cf40bb5cc4e390e237c`.
Decision: the index identifies the shard, but does not locate an API row. Stop
this range route; obtain the filtered record or an explicitly verified row offset.
No geometry, fields, labels, independent families or training readiness is qualified.

The first `rows` response contains ID `D9jBQhBtwBzy7kAd8yNoEy6`, not the selected
`DRSySxvjUFWt5VLxPVRW37N`. The published 10,850,062-byte ID index matches its LFS
SHA-256 `a7e119bc38f8e2f26cbafb072c0ed159abf40c1ff8a93c7b7a870fdf2afbe2c1`.
It maps the selected ID to `coilsets/part-2.parquet`; index ordinal 312697 is not
an API offset. The first API ID occurs at index ordinal 43830, disproving identical
ordering. `index-lookup-v1.json` records the exact query and temporary reader.
Dataset revision stays `286a268c664938519af6ceacfb4ec8143f64e20e`.

One bounded range attempt at clean producer `4b32a9b44db61b77b5161b59159c76d41b0c04fd`
saved six verified HTTP 206 ranges, 10,683,474 bytes. The next 772-byte request
stopped at curl's size guard because its redirect response was 1,026 bytes; no
data from that request was admitted. This is a failed lookup, not a source-data
failure. Earlier attempt `fbf8ca5bcd14cd4f108ea624646cb2f9ea898e73` lacked a required
filesystem metadata method; a second invocation stopped at the dirty-tree guard.
Both downloaded zero bytes. All failures/logs remain, with original paths under
`/private/tmp/issue65-range-id-*`. Full raw headers remain there; archived headers
retain only status, date, length and range fields without redirect tokens/cookies.

Clean producer `fea6982cb91d74e83499735b96091fc0263bae57` reused the six saved ranges
without network reads. Footer counts are 100016/100010/100024 rows in shards 0/1/2;
3,410 row groups in shard 2 have ID min/max intervals containing the selected ID.
This does not identify its row. It makes a further unindexed scan unattractive
within the frozen 60-request route; it does not prove every possible retrieval
method exceeds the budget. Full shard hashes were not verified by these slices.

Limits: original acquisition 64 MiB download, 16 MiB/file, 30 s/request; this
attempt additionally 180 s, 32 MiB range data, 60 requests, 3/2 GiB free reserves,
one reader thread and 128 MiB DuckDB memory. Attempt 3 stops after 6.727335 s;
offline metadata completes in 0.204681 s. Final receipt writing is outside the
last checkpoint, with no outer supervisor. The 128 MiB intake storage allowance
was not audited across all later Git preservation/checkouts; do not claim an
aggregate workspace bound. No new native computation, full shard download or
native-environment modification occurred.

DuckDB 1.4.3 and fsspec 2025.12.0 were extracted only to a temporary directory,
from official hash-verified wheels. `cost-and-scope.json` binds wheel hashes and
sizes; package metadata, licenses and 113 installed-file identities are retained.
Wheel binaries remain external at `/private/tmp/issue65-*.whl`; original reader
is `/private/tmp/issue65-parquet-reader-v1`. The source dataset card declares MIT;
retain Proxima Fusion attribution and the earlier intake's rights qualifications.

Offline reproduction at the final producer, with that separately verified reader:
`python -I -S -B scripts/locate_community_sample.py --reader READER
--tree ARCHIVE/evidence/issue65-routing-v1/hf-coilstellaration-tree-v1.json
--reuse ARCHIVE/evidence/issue65-routing-v1/attempt-3 --metadata-only --output FRESH_DIR`.
Require `downloaded_bytes=0`, no requests, counts and candidate-group count above;
run without network permission. Same-code metadata replay is not independent
physics or fresh retrieval. The manifest uses paths relative to repository root
and binds source code plus every payload file. This archive is local-only and
does not supersede the original scientific verdict or claim #65 completion.
