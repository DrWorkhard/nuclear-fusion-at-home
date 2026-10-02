# Publication inventory: history, size and privacy indicators

Updated 2 October 2026. Read-only release preparation, **not a complete security
or rights audit**. Published on 2 October 2026 as the public repository
[DrWorkhard/nuclear-fusion-at-home](https://github.com/DrWorkhard/nuclear-fusion-at-home): complete history of `main`
plus the tags `foundation-pre-scope-2026-09-13` and `research-freeze-2026-09-27`.
The owner chose to publish the full history, including the local-path provenance
and author metadata described below.
[Review policy](REVIEW_POLICY.md) · [Portable release result](PUBLIC_RELEASE_RESULTS.md)

## Latest check

At source `a5de268e3d69e08959f289b603ce6d2db04597cc`, the inventory inspected
committed HEAD files and all unique blobs reachable from local Git refs. The
uncommitted README date edit and this subsequent report are outside that snapshot.
Five credential/key-shaped patterns and two home-path patterns were applied;
seven positive and seven negative synthetic controls passed.

| Quantity | Observed at the recorded revision |
| --- | --- |
| Tracked files at HEAD | 1,081 |
| Uncompressed tracked file content | 328,047,070 bytes |
| Reachable history | 373 commits, 2,251 trees, 3,471 unique blobs, one tag object |
| Unique blob bytes scanned | 385,329,705 |
| Largest blob | 26,032,560 bytes |
| Blobs above 10 MiB / 50 MiB | 6 / 0; inventory bins, not a hosting-policy verdict |
| Selected credential/key-shaped matches | 0 across the five patterns |
| Unix home-path indicators | 401 historical blobs; 398 files at HEAD |
| HEAD path-indicator locations | 397 evidence files and one fixture |
| Windows home-path indicators | 0 |
| Distinct commit author/committer email identities | 1; value not printed |

The reference-manifest SHA-256 returned by the inventory is
`91d912da66f752f34aaaa0d5c5b6e76df1b9251cd2c3c185b45347d3ac1d75b0`.
The earlier [inventory evidence](../../evidence/publication-inventory-v1.json)
remains unchanged and describes its own older source, not this check.

## Reproduce

```bash
python -I -S scripts/publication_inventory.py
python -m pytest -q tests/test_publication_inventory.py
```

The scanner needs only Python and Git; its three tests need pytest. All three
passed in 0.76 s. They cover deleted credentials remaining in history, selected
patterns without disclosure of matched values, and exclusion of untracked files.
Counts change as history grows; rerun for the actual publication revision.

## Publication decisions

Publishing this history also published its local-path provenance and Git author
metadata; the owner accepted this before publication. Distribution rights for all
included artifacts still need review. Existing MIT source and CC BY4.0 starter notices are not
blanket clearance of the complete research history. Preserve evidence identities;
do not silently sanitize old records or rewrite history to suppress indicators.

No selected credential matches does **not** establish that the repository is
secret-free. This scan excludes ignored/untracked files, unreachable objects,
commit/tag message contents, encoded/compressed payloads and credentials outside
its limited patterns. It does not inspect licensing rights. A reviewed separate
public export would be a different publication scope, not a replacement for the
research history and its freeze tag.

Hosted CI results are recorded in [current verification](../logbook/VALIDATION_LOG.md).
GitHub permissions and branch protection are not verified by this inventory.
Keep ignored raw runs and the native environment outside the Git publication.
