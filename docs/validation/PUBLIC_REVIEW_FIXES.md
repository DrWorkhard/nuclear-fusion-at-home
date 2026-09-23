# Public release review resolution

23 September 2026. Follow-up to the user's eight-point release review; no new
scientific experiment or design claim. Start revision: `31c4b81`, clean worktree;
only editor Python services were running. Original reports and numerical data
remain unchanged. This is operational and contributor-interface qualification.

## Changes and acceptance checks

| Review issue | Change | Required verification |
| --- | --- | --- |
| 1. First-push core CI | Explicit dev-only test profile; no collection of native tests without their dependencies | Fresh isolated checkout, locked dev sync, complete core runner |
| 2. Windows documentation | UTF-8 reads for Markdown and Python source | Simulated cp1252 default covering both code paths |
| 3. Python compatibility | Early launcher guard; public Python 3.11+, historical native 3.12+; version hints | Actual macOS system 3.9 failure, public 3.11/3.12 tests; 3.11/3.12/3.14 OS matrix configured |
| 4. Contributor agents | Default public rules above explicitly scoped maintainer history | Contributor instructions require no shared-log/status churn or autonomous commits |
| 5. Candidate feedback | Directions, reference scores, signed/percent change, named editing and contextual errors | All 198 name/position mappings, shape/value rejection, output protection, real reference/candidate replay |
| 6. English navigation | All seven folder indexes and historical entry guide in English | Every detail document still indexed; historical reports unchanged |
| 7. Readability | Shorter README, practical field-error magnitude and small glossary | Preserve goal/MS1/MSX and distinguish sparse feedback from research gates |
| 8. Roadmap consistency | Same seven names/statuses in root README, overview and plan | Automated table consistency/order check; Step 4 remains In progress |

Public comparisons use metrics from the bundled **native 256-node** seed fields
versus the candidate's **512-node** fields. They do not add a solve or modify a
saved report. Normal RMS reference is 0.3042070281, inner-vector RMS 0.3804347184;
lower is better, but numerical noise and trade-offs must be reported. Research
limits 1e-4/0.01 belong to a different full-grid, flux-normalized workflow.
Exploratory lower-score PRs are welcome without implying a physical pass.

## Preservation: explicit operational exception, version 1

The original foundation checker froze every pre-5971fee path, including CI and
documentation utilities. That blocks two requested operational repairs. We keep
`.github/workflows/ci.yml` byte-identical and make a narrowly reviewed exception
for `scripts/run_core_ci.sh` and `src/fusion_baselines/documentation.py` only.

`src/fusion_baselines/operational_preservation.py` stores the SHA256 of **both**
each original and reviewed replacement. The current foundation auditor accepts
only that exact pair, rejects later byte changes, unknown paths and symlinks,
and reports `operational_maintenance_version:1`. Original bytes remain at
`5971fee` and its preservation tag. This changes the operational preservation
rule explicitly; it does not retroactively rewrite old source-bound audits,
scientific thresholds, numerical kernels, case data or acceptance results.
Tests must exercise both allowed and rejected byte pairs.

The four files in the public report's evaluator identity stay byte-identical:
`__init__.py`, `data.py`, `field.py`, `report.py`. UI helpers and CLI output are
outside that identity. Old reports should remain replayable without patching
their hashes. Full native regression is still required locally for this change;
the lighter hosted core profile is not a substitute for that scientific suite.

## Execution record

Implementation: 44 public tests pass on local Python 3.11.4 and 3.12.13; 98
targeted documentation/preservation/legacy-CLI tests pass in 7.41 seconds.
Actual system Python 3.9.6 produces the intended version message. Ruff,
documentation structure and whitespace checks pass after correcting four line
lengths. One attempted targeted invocation named nonexistent tests, ran none and
returned 4; the corrected file selection produced the 98-test result above.
Fresh core clone, full native regression and actual copied-tree replay are next.
The supplied review reports 36 public tests on Python 3.11/3.12/3.14 and 2,064
historical tests with 334 warnings; those are the reviewer's observations, not
new executions by this change. The previous preserved release evidence remains
in [PUBLIC_RELEASE_RESULTS](PUBLIC_RELEASE_RESULTS.md).

Resource plan: about 4.8 GiB free before work. An isolated clone of this repository
(about 325 MB tracked) plus locked dev-only environment is expected to use under
1 GiB, leaving over 2 GiB reserve. No benchmark archive, native build, search,
root-environment sync, hosting changes, push or contact is part of this task.

Hosted Linux/macOS/Windows CI, independent hardware execution and whole-history
publication clearance remain separate launch gates. Configuring a matrix is
not evidence that its hosted jobs have run.
