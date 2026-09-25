# Root README review: implementation and verification

25 September 2026. Response to the [27-point review](ROOT_README_REVIEW.md).
The original review is retained as a historical record, not rewritten as if these
changes had existed when it was performed. This follow-up tracks each recommendation.

## Scope and current conclusion

Implementation addresses the README, contribution route, helper text and displayed
reference comparison. The four source-bound evaluator files, data, saved reports
and scientific thresholds are unchanged. The original README working-copy edits
are in scope because the review explicitly requests revising that wording/layout.
The concurrent overview deduplication at `a1a23ea` is preserved.

**26 recommendations are implemented and locally verified.** Recommendation 2 has a clearly labelled clone template
and ZIP route, but the **real hosted clone URL remains unavailable**: no remote is
configured. Publication/hosting cannot be asserted or enabled by editing prose.

## Recommendation-by-recommendation resolution

| # | Change / disposition |
| --- | --- |
| 1 | Use evergreen project-operation text and link the dated launch checklist; remove the front-page pre-launch inventory/automation narrative. Keep actual outstanding clearance in the status/policy. |
| 2 | Add clone + cd template and Code/ZIP instructions. **Pending hosting:** replace the labelled placeholder with a verified actual URL when supplied; add this to the launch checklist. No URL invented. |
| 3 | Add tracked `submissions/<study>/candidate.json` plus a nearby summary. Keep generated reports/audits in ignored `results/`; document git add. |
| 4 | Say “no additional download” after obtaining the checkout. |
| 5 | Define “best” as a balanced design aim; remove wording suggesting we will build a reactor. |
| 6 | Introduce MSX as the final milestone in the plan, not unexplained in the opening sentence. |
| 7 | Early glossary defines reference/seed, RMS, filament, native tools, full-grid and flux normalization. |
| 8 | Attribute the 0.27 error directly to the current starting coil sets. |
| 9 | Explain the same reference's approximately 0.27 full-research vs 0.304 public-sample score. |
| 10 | Name the preregistered bounce-action metric. |
| 11 | Replace the maintainer synchronization note with the reader-facing route to verified designs. |
| 12 | Keep three consistent columns: named goal, goal explanation and scoped status. Explain that completed local scopes were checked on the maintainer's machine. Canonical names/statuses remain shared only with the detailed plan (D-026). |
| 13 | Expand W7-X and identify Goodman et al.'s open QI dataset. |
| 14 | Tie the starter explicitly to Step 4's coil-field bottleneck. |
| 15 | Show init → set-coefficient → evaluate the newly written candidate → audit. Help explains the name syntax and absolute metre-valued setting. |
| 16 | Use double quotes around coefficient names in both entry guides and help. Actual Windows shell execution remains unverified. |
| 17 | Give a 0.01–0.1 mm exploratory scale, a +0.1 mm editing example, indicative seconds per evaluation and a callable Python loop. This is not a safe-step or improvement guarantee. |
| 18 | Compare both reference and candidate using the unchanged public 512-node calculation. The unchanged reference now has zero displayed change; saved-native 256-node checks stay separate. Do not invent a universal significance threshold. |
| 19 | Show expected reference/admission flags and test-run OK, plus indicative runtime. |
| 20 | Explain python3/py -3 with a version check and optional explicit version selection; distinguish macOS local checks from unverified Windows/Linux/hosted runs. |
| 21 | Explain optional/recommended audit as same-code numerical replay, with tolerances; request its outcome in the PR. |
| 22 | Use 1e-4 consistently for the normal-RMS research limit. |
| 23 | Add “not endorsed by” to the affiliation statement. |
| 24 | Explain that reports call physical acceptance “admission”. |
| 25 | Link the stable release-results page and current status, with exact tested Python versions rather than implying untested 3.13 or other OS coverage. |
| 26 | Fix Python/version and sample-count spacing in launcher/discovery output. |
| 27 | Add a five-line repository map, including the candidate contribution folder. |

## Checks and limits

Initial checks: **47 public tests pass** on Python 3.11.4 (3.992 s). The broader
36-test selection has **34 passes and two disk-guard failures**, retained in
`artifacts/readme-review-v1/workflow-tests.xml`. Both new end-to-end tests pass:
the seven exact README Python commands, same-resolution zero comparison, candidate
git add in a temporary repository (report still ignored), and the three-point
Python example. The two failures are old foundation runners requiring 3 GiB;
the observed free space was approximately 2.83 GiB at those calls. Do not mock or
lower that guard to relabel this selection as green.

One CLI help line initially failed Ruff's length check; corrected. Repository Ruff,
documentation structure and whitespace pass. The narrower documentation/workflow
suite passes all 16 tests in 14.95 s. Original review, examples and all four hashed
evaluator sources match `a1a23ea`. Committed-source qualification follows below.

### Committed-source closure

Implementation `0d9abcf`: **47 public tests and all eight real copied-tree checks
pass on each of Python 3.11.4, 3.12.13 and 3.14.3**, on macOS. All 16 files in each
copy match that commit. The unchanged reference displays exactly zero change for
both scores. Demo timings were 3.84–4.08 s and evaluations 2.58–2.75 s; these are
indicative local observations, not controlled performance comparisons.

After disk space rose to approximately 55 GiB without any cleanup by this session,
the **full research regression passed: 2,182 tests, 334 existing warnings, zero
failures/errors/skips, 244.42 s**. The original disk guards and earlier two failures
remain intact. No package installation or environment sync was needed.

The [qualification record](../../evidence/readme-review-v1.json) binds 12 code/test
sources and 30 retained result/log artifacts, including all three copied-tree
operation histories and both the failed and successful test selections.
Unrelated new README edits appeared during validation; code/data stayed bound to
the implementation commit and those user edits are left out of the closure commit.
Final checks: all 42 source/artifact hashes and sizes match; all 12 source files
match the implementation commit. After documentation updates, 14 documentation/
release tests pass in 0.59 s; docs, Ruff and whitespace pass.

Disk reserve at start was only about 1.1 GiB, later about 2.8 GiB without any cleanup
by this session; it subsequently rose to approximately 55 GiB, clearing the resource
blocker before the successful full regression. Step 4 native work still needs the
unchanged 3 GiB starting / 2 GiB running reserve. This UI/documentation work does not complete Step 4 or qualify
a new physical design. No hosting, external contact, PR automation or merge enabled.
