# Publication inventory: history, size and privacy indicators

23 September 2026. Read-only release preparation, **not publication approval or a
complete security/rights audit**. This check does not change scientific results.
[Review policy](REVIEW_POLICY.md) · [Portable release result](PUBLIC_RELEASE_RESULTS.md)

## What was checked

At source `fae6c87fd3dcfdeee7df4d7dfd2674b5561bf1dc`, inventory all tracked files
at HEAD and every unique blob reachable from all four local Git refs. Read blob
bytes through Git without materializing another checkout. Apply five limited
credential/key-shaped patterns and two home-directory path patterns. Report counts
and, for credential-shaped matches, object/path locations—never matched values.

The scan contains seven positive and seven negative synthetic pattern controls.
An inline scan and the saved script agree under a structured comparison. Final
JSON output sorts keys. Initial wrapper lint errors were corrected; an initial
order-sensitive JSON comparison failed, whereas the final structural comparison
confirms identical inventory data. No data or history was modified to change results.

## Observed inventory

| Quantity | Observed at the recorded revision |
| --- | --- |
| Tracked files at HEAD | 1,541 |
| Uncompressed tracked file content | 325,093,781 bytes, about 325 MB |
| Reachable history | 285 commits, 1,655 trees, 2,611 unique blobs |
| Unique blob bytes scanned | 356,848,583 |
| Largest blob | 26,032,560 bytes |
| Blobs above 10 MiB / 50 MiB | 6 / 0; these are inventory bins, not a hosting-policy verdict |
| Selected credential/key-shaped matches | 0 across the five registered patterns |
| Unix home-path indicators | 366 historical blobs; 365 files at HEAD |
| HEAD path-indicator locations | 362 evidence files, one fixture and two documents |
| Windows home-path indicators | 0 |
| Distinct commit author/committer email identities | 1; values not printed |

Source digests, exact patterns, scope and results are retained in the
[inventory evidence](../../evidence/publication-inventory-v1.json). The small
portable starter remains a separate, locally verified entry point; its small
dataset does not mean the entire research checkout or its history is equally small
or publication-cleared.

Home-path indicators need individual review: some may be placeholders, others
machine-specific provenance. Counts are **not** an assertion that each match is a
sensitive disclosure. Likewise, no selected credential-shaped matches does not
prove the absence of secrets. Commit identity metadata requires intentional review.

## Reproduce and test

From the trusted repository root, with Python and Git available:

```bash
python -I -S scripts/publication_inventory.py
python -m pytest -q tests/test_publication_inventory.py
```

The inventory is a maintainer tool, not a requirement for the dependency-free public
demo. It reads the current HEAD/all local refs, so counts change as history grows.
The tests need the research test environment; the inventory itself uses only the
standard library and Git. Three temporary-repository tests pass in 3.19 s: deleted
synthetic credentials remain detectable in history, all selected patterns are
reported without matched values, and untracked content is explicitly outside scope.
Each test checks that the inventory leaves its working tree unchanged.

Closure repeat: 96 inventory/documentation/foundation/legacy-CLI tests pass in
6.82 s; 36 public starter tests pass in 0.313 s. Repository Ruff, documentation
structure and whitespace checks pass. Both saved inventory source hashes and all
16 prior portable software/data hashes match; no public numerical source changed.

## Limits and next actions

This scan does not inspect ignored/untracked files, unreachable/reflog-only objects,
remote-only refs, commit/tag message contents for credentials, encoded/compressed
payloads, every provider's credentials, arbitrary passwords or licensing rights.
The recorded results also do not automatically cover later commits, including the
commit that saves this checker and report. Repeat review for the exact release.

Before publication, adjudicate path/identity indicators, complete a stronger
content/security and rights review, and decide the intended publication scope.
Publishing the full history and producing a separately reviewed clean release
snapshot have different privacy/provenance trade-offs. Neither is approved here.
If a new public derivative is needed, retain the original research evidence and
hashes unchanged; never silently sanitize evidence in place or rewrite history.
This work did not push, contact anyone, configure GitHub or remove any files.
