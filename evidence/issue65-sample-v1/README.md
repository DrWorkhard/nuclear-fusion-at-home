# Partial community sample intake

Clean local producer/evaluator: `f485fbd79013fa3f469eb75661effb96051a0b28`.
Question: can a joined boundary/requirements/coil sample support prediction of
achieved normalized coil-field error without new simulations? Select the first
CoilStellaration results/eval row, not a best-performing design. This bounded
attempt is inconclusive: requirements join and arithmetic pass; actual coil and
boundary joins are unavailable. This is not a qualified dataset or native replay.

`inspection.json` preserves the complete result and hashes of all inputs/code.
`inputs/issue65-sample/` holds raw JSON response bodies, selected normalized
response headers, pinned source text, attribution and acquisition limits/URLs.
Headers exclude cookies and transport-only fields and strip trailing whitespace;
original headers remain under `/private/tmp/issue65-*.headers`. Upstream files
are text only, never imported or executed. Three Git blob identities were
verified from decoded API bytes against pinned upstream source
`03d1dc236044b97c5bd2fdf608a151754f9479dd`.

Dataset service `x-revision` headers identify CoilStellaration
`286a268c664938519af6ceacfb4ec8143f64e20e` and ConStellaration
`8da71572eb63ce93e77ce89bec0d7c30b7eba89e`. Saved JSON bodies are SHA-256-bound;
they were not independently matched to full Parquet bytes. Service slice URLs
are mutable: on reacquisition require matching revision headers and exact IDs,
no truncated cells, no partial response and exactly one joined record. Published
shard hashes/sizes are metadata, not downloaded-payload verification.

The requirements ID joins, including scalar settings shared with the results.
Forty normalized distance/length/curvature/torsion summary identities are
recomputed. Neither those identities nor the baseline flag establish geometry
or field validity. Baseline conditioning uses achieved metrics, and the positive
flag coexists with 17.7593% shortfall against requested plasma clearance.
Reported five unique coils, order seven and nfp three are outside our public
six/order-five/nfp-two case contract. No truncation or acceptance change is made.

Coil and boundary filters first timed out (30 s), then returned HTTP 500
`ResponseNotReady`. A subsequent error-body read reports index loading; one later
poll still times out for coils and reports loading for the boundary. Retain these
failed attempts. Stop acquisition here; do not infer absent data or call the
sample unusable for all tasks. Smallest next check is the missing joins after
index availability, then verify actual conventions/metric grids before choosing
a compatible trusted evaluator. No new design generation is justified here.

Limits declared before row acquisition: 64 MiB total downloads, 16 MiB/file,
30 s/request, 128 MiB new storage, 2 GiB live disk reserve. Every successful
response is far below those caps. This is a read-only, bounded sequence of
requests, not a benchmark with an outer timing supervisor. No Parquet engine,
upstream package, native environment change or full shard download was needed.

Saved replay requires only Python 3.11+: in a clean shallow checkout of the
producer run `python -I -S -B scripts/inspect_community_sample.py --output
FRESH_JSON_PATH` (do not use `-O`). It should reproduce `inspection.json` exactly;
source data are committed there. Archive `replay.py --manifest-sha EXPECTED_SHA`
first verifies the archived manifest and recorded source hashes, then invokes
the same inspector in its checked-out source state; only the output producer SHA
differs at the archive commit. This is same-code arithmetic replay, not an
independent field/equilibrium calculation. No network calls occur during replay.

Dataset card declares MIT; code license credits Proxima Fusion. Preserve the
included license and upstream attribution. No separate dataset LICENSE was
present in the inspected tree. This local archive is unpublished and does not
expand redistribution rights or prove durable remote availability. Existing raw
inputs and all failed-response evidence remain intact.
