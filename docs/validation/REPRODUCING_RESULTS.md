# Evidence in tags, conclusions on main

`main` keeps active code, essential inputs, public cases/candidates and short
[scientific conclusions](../STATUS.md). Complete historical evidence lives in
files of immutable annotated Git tags. The annotation describes the record; it
is not a container for large JSON, logs or arrays.

## Current evidence archive

Tag: **[evidence-archive-2026-10-04](https://github.com/DrWorkhard/nuclear-fusion-at-home/tree/evidence-archive-2026-10-04)**

Archive commit: **`68db098b664bb072854b687040e103aaafee463c`**

Annotated tag object: **`6755d9ed09d034897a1a6106eb1be08a5a16cfc3`**

This preserves all 572 previously tracked evidence files, 356 tracked artifacts,
and historical cases, fixtures, manifests, references and patches byte-for-byte.
Their locations and original scientific verdicts remain unchanged in the archive.
The tag is published and protected against updates/deletion. Main retains two
unchanged files because current evaluators need them:

- `evidence/plasma-design-v2/reference-input-401.json`: public/native target.
- `evidence/plasma-balanced-v1/validation.json`: trusted native archive index.

Together these inputs are 208,154 bytes. Historical local files remain intact
and ignored; their absence from a fresh main checkout is intentional.
Ordinary contributions use the [small clone](PUBLIC_QUICKSTART.md#download-only-current-main).
For individual reports, open the pinned file links in [Status](../STATUS.md).
The commands below opt into downloading the complete historical snapshot
(over 326 MB of uncompressed retired files); depth 1 omits its older ancestry:

```bash
git fetch --depth 1 --no-tags origin tag evidence-archive-2026-10-04
git rev-parse evidence-archive-2026-10-04^{commit}
git cat-file -p evidence-archive-2026-10-04
git show evidence-archive-2026-10-04:evidence/coil-headroom-v3.json
git worktree add --detach ../fusion-evidence evidence-archive-2026-10-04
```

The archive commit is **not** every experiment's producer revision. Use each
record's original source/evaluator commits, hashes, commands and environment.
Some older runs recorded dirty working trees: their base SHA alone does not
identify the executed code. Preserve that qualification and verify the recorded
source hashes; do not retroactively label those runs clean or reproducible.

The [status table](../STATUS.md) links important results to their source states;
[completed steps](../steps/README.md) retain their scoped conclusions. Full Git
history is unchanged. This shrinks the default checkout, not an ordinary full
clone's historical object database. A shallow clone avoids that database.

## Record future evidence this way

1. Commit the producer/evaluator code and inputs before a confirmatory run.
   Record the full Git SHA, dirty state, environment, input/output hashes and
   actual reproduction command. Retain negative results and limitations.
2. Prepare a separate detached worktree from that source state. Commit the
   reviewed, size-appropriate evidence there; do not merge its bulk payload into
   `main`. Preserve original bytes. Record the actual evaluator revision if it
   differs from the producer. Document patches and hash identities for dirty
   exploratory runs instead of inventing a clean state.
3. Create an annotated `evidence-<study>-<version>` tag on that evidence commit.
   Its description contains the question, short result/limits, producer/evaluator
   SHAs, dirty state, evidence paths/hashes, reproduction command and data
   availability. Full reports and arrays belong in the commit's files.
4. Under the user's publishing authority, push the tag explicitly and verify
   its tag-object and peeled commit IDs remotely. Verify archived file hashes
   and retrieval before removing any payload from `main`. Keep original local
   raw outputs; use index-only removal where they must remain in this workspace.
5. Add the short conclusion, tag, archive commit and original source-state links
   to the relevant current summary. Keep essential active inputs on `main`.
   Corrections get a new tag and a superseding summary; never move/delete tags.

Use ordinary Git commands, not another archive framework. For example, replace
`PRODUCER_SHA`, `STUDY` and `evidence-note.txt` with reviewed run-specific values:

```bash
git worktree add --detach ../fusion-evidence-new PRODUCER_SHA
# In that worktree, copy only the reviewed payload to evidence/STUDY/.
cd ../fusion-evidence-new
git add -f -- evidence/STUDY/
git commit -m "Record STUDY evidence"
git tag -a evidence-STUDY-v1 -F ../evidence-note.txt
git push origin refs/tags/evidence-STUDY-v1
git rev-parse evidence-STUDY-v1 evidence-STUDY-v1^{commit}
git ls-remote origin refs/tags/evidence-STUDY-v1 'refs/tags/evidence-STUDY-v1^{}'
```

The tag holds only committed files. Keep large external/raw datasets in separately
retained storage with locations, hashes and access/reproduction instructions.
Explicitly label local-only or unavailable inputs. Do not publish ignored runs
or third-party data merely to fill an archive. Existing ignored raw runs, native
environments and external checkouts have **not** been backed up or newly
published by this migration; some native replays still require those local files.

## Historical code and protocols

These are navigation revisions; the record's exact producer and hashes control
numerical replay. No copied historical code tree is maintained on `main`.

| Navigation state | What it contains |
| --- | --- |
| `research-freeze-2026-09-27` → `56181dc4250cb24ce3d2bedf5cec3d894d1ac250` | Steps 1–3, retired research pipelines/protocols and matched restart |
| `foundation-pre-scope-2026-09-13` | Earlier foundation scope |
| `d5d395b` | Completed boundary/start screens and inactive environment manifests |
| `8c5753c` | Full completed result pages, sampled geometry audit and starter exporter |
| `8581b1b` | Chained normalized/constrained/coherent/restart/longrun/headroom drivers |
| `bf51e3a` | Submitted interior-pass continuation driver |

Example after fetching the required revision:
`git show 8581b1b:scripts/explore_coil_headroom.py`.
Historical revisions are absent from a shallow clone. To replay one, resolve its
full SHA from the linked record, then explicitly fetch that snapshot with
`git fetch --depth 1 --no-tags origin FULL_SHA` and create a detached worktree at
that SHA. This downloads its historical files; do not do it for public CI.
Read the historical protocol and resource requirements before executing it.
Current verification uses the [native environment](ENVIRONMENT.md),
[public checks](PUBLIC_QUICKSTART.md) and `python scripts/check_docs.py`.
