# Partial community sample: labels before learning

**Decision: inconclusive for a qualified joint-design sample.** The first
CoilStellaration evaluation row supplies a verified requirements join and
consistent scalar normalization. Its actual coil/boundary joins remain unavailable.
Do not train or generate new designs from this intake result. The cheapest next
check is those two records once the service index is available, followed by
convention and metric-grid verification with a compatible trusted evaluator.
This is partial work on #65, following the [readiness inventory](COMMUNITY_DATA_READINESS_V1.md).

Task considered: predict achieved normalized coil-field error from boundary,
requirements and coil geometry. Selection was `results/eval` row zero, without
performance filtering. Saved CoilStellaration responses identify revision
`286a268c664938519af6ceacfb4ec8143f64e20e` through service headers; they have local
SHA-256 identities but were not independently matched against full Parquet bytes.
Requirements `DQinz2Bpbcvv3fxpfsR6wxB` joins exactly. Coil
`DRSySxvjUFWt5VLxPVRW37N` and boundary `DMWkGVU6JZjx8Sx3ky4z4qB` remain
unverified after 30 s timeouts and HTTP 500 `ResponseNotReady`/index-loading replies.
The boundary service identifies ConStellaration revision
`8da71572eb63ce93e77ce89bec0d7c30b7eba89e`. This does not establish missing data.

| Finding | Consequence |
| --- | --- |
| Pinned loader conditions on achieved `desc_metrics/*`, not requested `reqs/*`. Achieved plasma clearance is 0.748747 versus requested 0.910434: **17.76% short**, despite a positive baseline flag. | Preserve both quantities and flag semantics; baseline inclusion is not acceptance of every requested bound. |
| Forty summary normalization identities reproduce to scaled error below 3.34e-16, using reported minor radius 0.133628 m. | Arithmetic agreement only; no distances, fields or surfaces independently recomputed. |
| Upstream field error is pointwise `abs(Bn)/abs(B)`; flattened means/maxima are reported. | These labels cannot replace our area-weighted RMS, target normalization or interior/realized-benefit checks. |
| Reported five coils per half-period, order seven, three field periods; source schema uses `[sin(N), ..., sin(1), const, cos(1), ..., cos(N)]` and per-coil amperes. | Outside our fixed six/order-five/nfp-two public contract. No truncation/relabeling. Actual coefficients, current signs, symmetry and physical coordinate scale still need payload verification. |
| REGCOIL and DESC results share boundary/requirements ancestry; both benchmark track flags are true. | Keep related variants together. Row IDs or upstream split names do not establish independent families or unseen-family validation. |

The dataset card declares MIT; the inspected tree has no separate dataset LICENSE.
Retain Proxima Fusion credit and the pinned code license. No upstream code was
executed or installed. Raw metric grids, producer fidelity, complete failure
coverage, geometry duplicates and target-field identity are unqualified; the
positive flag is retained as source data rather than promoted to our label.

Limits declared before row acquisition: 64 MiB total download, 16 MiB/file,
30 s/request, 128 MiB new storage and 2 GiB disk reserve. No full shard or native
simulation was needed; requests and failures are preserved. Clean local
producer/evaluator: `f485fbd79013fa3f469eb75661effb96051a0b28`. Upstream source
`03d1dc236044b97c5bd2fdf608a151754f9479dd` was inspected as text; three Git blob
identities were verified. This source revision is not proof of dataset production.

Local annotated tag `evidence-issue65-sample-v1`, archive
`9f3d4a5a9cbb0b85a6e07cf40bb5cc4e390e237c`, payload
`evidence/issue65-sample-v1/`; 26-file root-relative manifest SHA-256
`9406c286a873848619cf5800c5ae87b0d1c8c1c8e94761bd8464c53516aa786c`.
The archive README gives source-bound inspection/replay commands. Saved replay
checks hashes and repeats the same arithmetic without network/native tools;
it is not independent physics reproduction. Original responses remain under
`/private/tmp/issue65-*`; archived headers retain relevant fields only.
The snapshot is unpublished and remotely unverified. #65 remains open.

**Bounded retrieval follow-up:** row access works, but the hash-verified 10.85 MB
published ID index gives shard paths, not matching API row offsets. The selected
coil lies in shard 2. A 10.68 MB range attempt stops at a redirect-response size
guard; saved metadata leaves **3,410 possible row groups**. Stop this route under
its 60-request limit; obtain the filtered record or a verified row offset instead.
No full shard hash, selected coil payload or new physics label was verified.
Temporary DuckDB/fsspec readers leave the native environment unchanged. Original
failed attempts remain; total storage across later archive/checkouts was not
audited against the 128 MiB intake allowance, so no aggregate compliance is claimed.
Final metadata producer `fea6982cb91d74e83499735b96091fc0263bae57`; local tag
`evidence-issue65-routing-v1`, archive `fa5db5db664f58386cdb9f7ada2f0558b1139b10`,
payload `evidence/issue65-routing-v1/`, root-relative 35-file manifest SHA-256
`a92046d277739c8c28986b7e33406c8a5aa07be2c0261f5f776997bfb64b335c`.
Its README specifies offline, same-reader metadata replay and every failure;
publication and complete sample qualification remain pending.
