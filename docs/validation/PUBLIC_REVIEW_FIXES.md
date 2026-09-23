# Public release review resolution

23–24 September 2026. Follow-up to the user's eight-point release review; no new
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

## Execution record — local qualification complete

Implementation: 44 public tests pass on local Python 3.11.4 and 3.12.13; 98
targeted documentation/preservation/legacy-CLI tests pass in 7.41 seconds.
Actual system Python 3.9.6 produces the intended version message. Ruff,
documentation structure and whitespace checks pass after correcting four line
lengths. One attempted targeted invocation named nonexistent tests, ran none and
returned 4; the corrected file selection produced the 98-test result above.
Implementation is committed at `be916fb`. Subsequent clean-source verification:

- **Fresh dev-only core CI:** exact `scripts/run_core_ci.sh` passes in an isolated
  local clone using uv 0.11.2: Ruff, 44 public tests, docs checker and 14 selected pytest tests.
  SciPy, meshio and JAX are confirmed absent. The root native environment was
  never synchronized; workflow disablement is unnecessary for this dependency issue.
- **Public compatibility:** all 44 tests and all eight real copied-tree operations
  pass on Python **3.11.4, 3.12.13 and 3.14.3**, on this macOS machine. Every copied
  source matches the implementation commit. This is not a nine-job hosted-matrix pass.
- **Full native regression:** **2,072 passed, 334 warnings**, zero failures/errors/
  skips, 222.70 seconds. JUnit is retained at
  `artifacts/public-review-v2/regression.xml`; SHA256
  `f967910c6ec9aa6875b3673e1e61274d3d4e6722b92e90005df72bedc42e1995`.
- **Preservation:** all 1,266 historical paths accounted for, exactly two approved
  operational replacements, no blocked changes. Old committed evidence, bundled
  numerical data, four public evaluator sources and historical workflow unchanged.
- **Windows encoding:** both regression fixtures and the whole documentation tree
  pass with a simulated cp1252 default. Actual Python 3.9.6 returns 2 with the
  version and macOS/Linux/Windows upgrade hints before numerical imports.
- **Navigation:** all documents remain indexed, local links pass, four public
  navigation anchors checked, canonical roadmap names/statuses and heading order
  pass automated tests. All seven indexes and historical entry guide are English;
  original detailed German reports stay preserved. README shortened from 1,186
  to 1,005 whitespace-delimited words while adding goals, scores and a glossary.

An **additional**, nonprotocol byte-equality assertion initially failed for the
Python 3.11 reference report and its digest-bearing replay. Diagnosis: only
`levels[0].metrics.sampled_normal_max` differs by -1.1102230246251565e-16 and
`sampled_normal_rms` by +5.551115123125783e-17. All B/A arrays match exactly on all
three Pythons; changed-candidate reports match byte-for-byte too. Python 3.12 and
3.14 reference reports/replays are also byte-identical to the original release.
The **unchanged existing** replay tolerance passes; no threshold was relaxed.
Direct replay of the old report on 3.11 and 3.12 succeeds with identical audit
output. The failed stronger assertion is retained separately, not erased.

The one-micrometre smoke variation slightly **worsens** both displayed scores;
the signed comparisons correctly show that. It is a test input, not a new optimized
  candidate or physical improvement. Source-bound records and raw artifact hashes:
[public-review-v2 evidence](../../evidence/public-review-v2.json).
Final documentation/preservation/legacy-CLI rerun: 98 tests pass in 7.33 seconds.
Ruff, docs and whitespace checks pass; all 32 recorded artifact/source hashes and
sizes verify. Software remains identical to the full-regression revision.

Environment/setup limitations encountered: default uv cache access was sandbox-
denied, so an isolated task cache was used. A local hardlink clone was denied;
a fresh `--no-hardlinks` clone succeeded. The isolated checkout/cache used about
604 MiB; about 4.1 GiB remained after regression. No data or old runs were deleted.
The disposable clone/cache remains under `/private/tmp/fusion-public-review-czVuOx`;
it is not part of the repository or public dataset. The earlier denied process
inspection was repeated with read-only permission and confirmed editor services
only before native regression. No research experiment was interrupted.

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
