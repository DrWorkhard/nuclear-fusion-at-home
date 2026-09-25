# Portable public layer: verification record

Latest local follow-up (25 September): [README review resolution](../review/ROOT_README_RESOLUTION.md).
At `0d9abcf`, 47 public tests and eight copied-tree checks pass on local macOS
Python 3.11/3.12/3.14; full research regression: 2,182 pass, 334 warnings. Hosted
verification and a real clone URL remain separate. The original record below
retains its own revisions, counts and failures unchanged.

23 September 2026. The [release specification](PUBLIC_RELEASE.md) fixes the scope
and numerical checks. This report records implementation outcomes separately.
No new optimization or change to historical scientific acceptance is claimed.

## Software qualification

36 standard-library public unit/analytic tests pass, with final pre-commit repeat
in 0.266 s. The initial 35-test run exposed a JSON-depth assumption; explicit
depth/node limits corrected it.
Tests cover analytic circle fields, SI derivatives, current sign/linearity,
translation, physical-copy mapping, candidate/data/report tampering, file
preservation and optional cost/unrequested-topic metadata.

The first full historical regression had 2,061 passes / 3 failures / 334 known
warnings in 210.51 s: frozen CI had been edited. That file was restored byte-for-byte and
the new CI added separately. No preservation exception or physical threshold was
changed. Then 93 focused old controls passed in 7.65 s; the corrected full suite
has 2,064 passes, 334 known warnings, zero failures/errors/skips in 213.23 s. Both runs
and final source/data digests are retained in the
[software qualification](../../evidence/public-layer-v1-software.json).

Ruff, documentation and whitespace checks pass. Static checks verify read-only
public-CI permissions, pinned actions, no privileged trigger, no secrets and
nonpersisted checkout credentials. Hosted Linux/macOS/Windows execution has not
been observed. A limited secret-pattern scan of new files finds no matches;
whole-history rights/privacy/security review remains outstanding.

## Portable data

Three JSON files total 116,178 bytes. Parent audit/run/bundle/snapshot/array/
equilibrium hashes are bound during the read-only derivative export. Original
private paths are not copied into the packet; old files remain unchanged.
Zenodo's official record API confirms the original dataset's creator, version,
CC-BY-4.0 license and the archive checksum already in our manifest. No large
archive was fetched. [Attribution and conventions](../../examples/clear-coil-samples-v1/README.md).

## Real copied-tree qualification

**Passed from clean source `02bc42a25b45cf6df558188b0d8e816a175789ed`.**
All 14 copied file digests match both that Git revision and the unchanged source
tree. All 16 software-qualification source/data records still match after the run.
No numerical source or tolerance changed between source freeze and qualification.

The runner created a fresh `checkout with spaces` containing only the public
launcher, source, tests and bundled examples. There is no copied `.git`, `.venv`,
native dependency, external checkout or historical artifact directory. CPython
3.12.13 on macOS/Darwin 24.6.0 arm64 ran with `-I -S`: site packages and Python
environment customization are disabled. Each CLI worker rejects Python `socket.*`
audit events. This is a local isolation check, **not an OS security sandbox**.

| Check | Observed result |
| --- | --- |
| Public tests | All 36 pass, zero skips; unittest reports 0.299 s |
| Discover available case | Succeeds without research dependencies |
| Unchanged real reference | All six archived native B/A comparisons pass the fixed 5e-10 limit; same-evaluator report replay passes |
| Changed candidate | Fixed +1 micrometre to base coil 0, `xc(0)`; candidate identity and computed fields both change |
| Changed report replay | Passes; no native-reference claim for the changed candidate |
| Forged physical-admission flag | Rejected with exit 2; no success artifact written |
| Contribution without compute/hint fields | Accepted by the metadata checker |
| Existing output directory | Rejected with exit 2; previous evidence is preserved |

Largest relative difference from the archived native values: **9.5879976e-16**.
Largest reported 256/512 resolution difference: **1.8491317e-15**. These are
arithmetic/refinement observations on the saved samples, not whole-surface bounds.
At 512 nodes the seed's sampled normal RMS is 0.3042070281, normal maximum
0.5766173462 and inner-vector RMS 0.3804347184. These are sparse, fixed-current
metrics, **not** the original full-grid normalized objective or a feasible design.
The changed-candidate check performed no optimization or selection for improvement.

All eight operations take a combined 6.775 s in this single local run, including
the 2.548 s reference demo. This is not a performance benchmark or spending limit.
The retained local output contains 37 files / 623,553 bytes, including copied files,
logs, reports and interpreter caches. The committed
[portability evidence](../../evidence/public-layer-v1-portability.json) contains
the full qualification record, operation logs, source/environment identity and
hash-bound references to all raw reports. Raw qualification:
`artifacts/public-portability-v1/qualification.json`, SHA256
`ad7993f68dcd531741113b11771d107a8039faffccede213fa809908413a78fc`.
The source-bound pre-execution software record is preserved without relabelling
its earlier “real reference not yet run” state.

After writing this result, 36 public tests pass again in 0.365 s and 93 historical
foundation/CLI/documentation controls pass in 8.75 s. Ruff, documentation structure
and whitespace checks pass. A read-only consistency check verifies all 27 distinct
bound files (1,122,546 bytes), including raw public reports and both historical
JUnit files, plus the recorded qualification's exact equality with the raw run.
No numerical source changed during this documentation/evidence closure.

The bounded local publication-layer deliverable is complete. Remaining launch
work is the [hosting/security checklist](REVIEW_POLICY.md#launch-checklist--requires-actual-hosting-work),
especially whole-history rights/privacy review, real reviewer/protection settings,
hosted CI and independent-machine reproduction. Full historical physics/data
portability is a separate, valuable research-infrastructure contribution.
The subsequent [publication inventory](PUBLICATION_INVENTORY.md) checks repository
size and selected history/privacy indicators; it does not change this local
starter qualification or establish publication clearance.

This is a portability/arithmetic/interface check, not an optimization study,
independent-hardware reproduction, OS sandbox proof or physical design admission.
No hosted bot, publication or automatic merge is enabled by these changes.
