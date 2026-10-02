# Current verification

Updated 2 October 2026. Git retains earlier verification records.

## GitHub publication preflight

Publication was requested, but there is no configured remote or connected GitHub
integration yet; the owning account/repository name is still needed. No push,
public repository, hosted CI run or repository-settings change has occurred.

- Read-only [inventory](../validation/PUBLICATION_INVENTORY.md) at `a5de268`:
  1,081 tracked files, 373 reachable commits, zero matches for five limited
  credential patterns. Local paths remain in 398 tracked files; author metadata
  and complete-history distribution rights still need intentional review.
- Inventory tests: **3 passed**, **0.76 s**. Public tests: **48 passed**,
  **3.358 s**. Documentation/release tests: **37 passed**, **0.22 s**.
  Documentation and whitespace checks pass.
- Local copied-tree public qualification: **8 checks passed** using Python with
  isolated imports, no site packages and a socket audit guard. Raw outputs are
  retained locally in `results/github-preflight-2026-10-02`; they are ignored by
  Git. This is neither hosted CI nor separate-machine reproduction.
- The user's README date edit is preserved, not included in the committed-object
  scan. No scientific evidence, evaluator, native environment or research result
  was changed. Process-list inspection was denied by the local sandbox; no
  research or other heavy job was started.

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
