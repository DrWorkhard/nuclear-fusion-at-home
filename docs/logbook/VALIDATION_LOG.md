# Current verification

Updated 2 October 2026. Git retains earlier verification records.

## GitHub publication and hosted CI

On 2 October 2026 the owner authorized publication. The public repository
[DrWorkhard/nuclear-fusion-at-home](https://github.com/DrWorkhard/nuclear-fusion-at-home)
was created and `main` (`e0eb02b`) plus the tags `foundation-pre-scope-2026-09-13`
and `research-freeze-2026-09-27` were pushed over SSH as DrWorkhard; the owner then
pushed `631434c`. The full history was published deliberately, including the
local-path provenance and author metadata described in the
[inventory](../validation/PUBLICATION_INVENTORY.md) (zero matches for its five
limited credential patterns at `a5de268`; local paths in 398 tracked files).

- Hosted GitHub Actions, first runs: `core-ci` passed for both commits (runs
  36971843925 and 36971892980, about 20 s each). `portable-public-ci` passed all six
  jobs (Linux, macOS, Windows × Python 3.11, 3.14) for both commits (runs
  36971843923 and 36971892966).
- Fresh anonymous HTTPS clone of `631434c` on macOS with CPython 3.12.13:
  `public cases` succeeds, `public demo` reports `reference_reproduced: true` and
  `physical_admission: false`, and the public tests pass.
- Publication follow-up builds on the owner's documentation commit `6bda543`.
  Concurrent launch-document edits were preserved and only extended after that
  commit. Rights review of the complete history and reproduction by another
  person remain open.

## Launch protections and follow-up checks

GitHub API read-back confirms private reporting enabled; fork workflow approval
required for all external contributors; full action-SHA pinning required; default
workflow token read-only with review approval disabled. Secret scanning and push
protection are enabled; the alert endpoint returns zero alerts. Auto-merge is off.

- Active rulesets: `24350197` requires the seven observed GitHub Actions checks
  and forbids main force-push/deletion with no bypass; `24350199` requires PR/code-
  owner review, with an explicit review-only exception for sole owner DrWorkhard;
  `24350200` forbids frozen-tag updates/deletion with no bypass.
- An initial classic protection request was rejected (HTTP 422: an organization-
  only user restriction). Read-back showed no partial protection. Separate
  rulesets supply the intended personal-repository configuration without
  broadening the CI exception.
- Fresh anonymous clone of `6bda543`: all eight public qualification operations
  and docs checks pass. Freeze tag identity matches `56181dc`. Outputs remain
  local in `/private/tmp/fusion-launch.tIVtF1/checkout/results/launch-qualification`.
  This local clone is not another person's independent reproduction.
- History inventory repeat: 376 commits, 3,481 blobs, zero selected credential
  matches; details and limits are in the [inventory](../validation/PUBLICATION_INVENTORY.md).
- Active native suite: **429 passed**, 13 known HiGHS-option warnings, **26.58 s**.
  Public suite: **48 passed**, **3.344 s**. Focused documentation/release/inventory
  suite: **43 passed**, **1.06 s**. Ruff, docs and whitespace checks pass after
  correcting an initial import-order lint error in the new release tests.
- Follow-ups have explicit acceptance criteria in issues
  [#1](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/1) (independent
  contributor reproduction) and
  [#2](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/2) (historical
  artifact rights). No independent review or rights clearance is claimed.
- Launch files are to be tested on a separate remote branch before the exact
  passing commit is fast-forwarded to main under the authorized owner session.
  This uses the documented sole-owner review exception, never a CI bypass.
- Local process inspection remains unavailable in the sandbox; no research solve
  or heavy build was started. Disk had about 12 GiB free before the single
  disposable clone. Native dependencies, scientific kernels and evidence are
  unchanged. Monitoring is session-triggered/manual, not a promised scheduler.

## Contributor documentation checks

The human README links to the technical guide and offers a copyable agent task.
Its opening uses an indented blockquote, bold headline and shorter paragraphs;
the motivating text's wording is unchanged, verified by a formatting-stripped
comparison. The rest of the README is byte-for-byte unchanged by that styling edit.
Agent/contributor navigation, roadmap ownership and word-budget checks follow
the split. MSX consistently states the aspirational 2030 goal in the technical
guide and project plan; no scientific acceptance criterion changes.

- Documentation/release tests: **37 passed**, **0.27 s**, including missing-guide,
  misplaced-roadmap, navigation and matching 2030 milestone regressions.
- Public suite: **48 passed**. Repository-wide Ruff, documentation and whitespace
  checks pass. No native experiment or full scientific regression was rerun for
  this documentation/policy change.

## Latest research validation — 27 September 2026

Clean revisions `963793d` and `5a3c1d0` test the same seed with construction
length target 3.44 m, selection limit 3.45 m and unchanged acceptance 3.5 m.

- Both pass scoped geometry. Expanded-box boundary RMS **0.001996268** and
  interior RMS **0.01147939** improve 2.64% / 1.55% over current-box, but still
  fail their limits. Coil-clearance lower bound decreases 6.49 mm.
- Shared geometry gives length upper **3.474220 m**, coil clearance lower
  **0.06831 m**, plasma clearance lower **0.13307 m**, curvature upper **10.04691/m**.
  No directed interval proof or full self-disjointness claim.
- Current/expanded complete **1,575 / 1,462 bundles**, selecting trials
  **1574 / 1459**. All **91 source hashes per run** verify unchanged.
- Separate saved-array arithmetic checks all **3,038 trial records**, both
  selections, four boundary and six interior numerical rows, current/flux
  identities, saved independent B/A samples and composed geometry classifications.
  No independent full geometry rerun or separate-machine reproduction.
- Workers **306.360 / 284.409 s**, supervisors **306.938 / 285.020 s**.
  Retained raw families **36.15 / 34.03 MB**, with complete path/hash inventory
  digests. All declared resource ceilings respected; runs were serial.
- Expanded stops on objective change after 278.205 s of startup/search,
  not its gradient criterion: final max gradient **3.40e-5** versus **1e-9**.
  No active coefficient bounds (selected minimum slack 3.91 mm).
  This does not prove a family optimum or establish the cause of slow convergence.

[Result](../optimization/LENGTH_HEADROOM_EXPLORATION.md) ·
[Current evidence](../../evidence/coil-headroom-v2.json) ·
[Expanded evidence](../../evidence/coil-headroom-v3.json).

The first headroom setup failed before search on unsupported native penalty
subtraction (supervisor 2.563 s). Its prefix remains at `coil-headroom-v1`.
Direct assembly and the real native penalty/derivative test fix that API error.

## Software and portable candidate

- Active native regression: **420 passed**, 13 known HiGHS-option warnings,
  **22.17 s**. Focused headroom/shared-search checks: **31 passed**, **12.53 s**.
- Public suite: **48 passed**, **3.217 s**; repository-wide Ruff, docs and
  whitespace checks pass.
- The [portable candidate](../../submissions/length-headroom-six-coil/README.md)
  exactly preserves all 198 selected names/coefficients. The case and evaluator
  are unchanged. Local Python 3.12 evaluation/replay passes, with sampled normal
  RMS **0.001744032** and interior RMS **0.03610319**.
- Python **3.11 with `-I -S`** also evaluates and replays that candidate without
  site packages. This is a local interpreter check, not a second machine.
- Public current stays 294,966.466322 A, unlike native 308,140.584432 A.
  Public replay is same-code and sparse, not scientific admission.
- The exact-flux identity and one-ULP poison regressions remain passing.
  No native environment sync, hosted CI or external scientific review.

Next: diagnose objective scaling/stopping and penalty conditioning. Physical
acceptance, realized topology, Step 3 transfer, pressure/engineering, independent
backup/reproduction and MS1 remain open. Git does not back up ignored raw data.
