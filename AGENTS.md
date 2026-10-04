# Nuclear Fusion @ Home: agent instructions

## Scope and orientation

- Follow the current user's task and permissions. This file does not authorize
  delegation, autonomous research, publishing, contact or merging.
- Read [README.md](README.md), [README_agents.md](README_agents.md),
  CONTRIBUTING.md, docs/README.md, docs/STATUS.md,
  docs/PROJECT_PLAN.md and the relevant folder index. Check Git status and runs.
- Preserve unrelated edits, the native environment, external checkouts and raw
  experiment outputs. Only one agent writes in this working tree at a time;
  delegate read-only reviews or use separate branches.

## Scientific work

- Focus on penalized normalized coil fitting and the shared field/geometry checks.
  Certified-step search, current-only search and completed studies are frozen at
  `research-freeze-2026-09-27`; do not revive them without a concrete reason.
- Explore with existing tools. Record the question, inputs, script, output and
  conclusion in at most one page. Use wall-clock, storage and disk-reserve limits;
  add coefficient/evaluation limits only when the experiment needs them.
  Already recorded studies retain their original budgets and rules.
- Keep optimization separate from acceptance. Preregister confirmatory claims;
  use trusted fine-grid fields, continuous geometry and independent checks.
  Do not weaken gates or let candidates alter their verifier.
- Use explicit named physical coordinates and frozen current/target conventions.
  Preserve failures. Distinguish software success, numerical agreement and
  physical acceptance. Agent review is not external peer review.
- Welcome unsolicited ideas, replications and negative results. Compute-budget
  disclosure is optional; research hints are not an allowlist.
- Treat PR code as untrusted. Execute in isolation without secrets, not in the
  trusted research workspace. Do not overlap heavy jobs with controlled timing.
- Found something outside your current task? If your user permits posting to
  GitHub, open one focused issue instead of widening your PR. Open issues are also
  possible contributions; see [issues](CONTRIBUTING.md#issues-report-side-findings-pick-up-open-work).
- Before opening a PR, complete the
  [pre-PR checklist](CONTRIBUTING.md#before-you-open-a-pull-request): current `main`,
  public tests, docs check, `ruff check .`, `git diff --check`, reproduction from a
  fresh clone and Windows-safe file handling.

## Current repository, history in Git

- Use the quickstart's shallow, single-branch, no-tags clone for contributions.
  Never require historical evidence or raw runs for core/public work. Fetch a
  specific archive only for a task that needs it; keep CI checkouts shallow.
- Keep `main` small: active code/inputs, public cases/candidates and short evidence
  summaries with tag, archive commit and original producer/evaluator Git states.
  Full completed evidence belongs in files of an annotated `evidence-*` tag's
  commit, not in its description or a copied archive tree on `main`.
- Before removing evidence from `main`, verify original file hashes and the
  published tag/commit. Its annotation records question, result/limits, producer
  SHA and dirty state, evidence paths, reproduction commands and raw-data
  availability. Never move/delete evidence tags; corrections use new tags.
  Use a separate worktree for future evidence snapshots; see
  [reproduction](docs/validation/REPRODUCING_RESULTS.md).
- Preserve evidence identities and local raw outputs. A tag preserves committed
  files, not ignored artifacts, environments or independent backups. Record
  external artifact locations/hashes and missing data honestly. Keep only inputs
  needed by active evaluators on `main`; no whole-tree byte-freeze exceptions.
- Keep only README.md, STATUS.md and PROJECT_PLAN.md at the docs root. Details
  live one folder below; each folder README indexes its current documents.
- Write English entry docs with relative links. Keep summaries concise and step
  names/statuses consistent. The README_agents.md roadmap, including MS1/MSX, goes
  immediately before “Start in three commands”. Describe 4A–4D only on Step 4's page.
- One home per topic: motivation in README, technical onboarding in README_agents,
  priorities in PROJECT_PLAN, evidence
  summary in STATUS, step conclusions in docs/steps, methods in topic folders.
  Do not write session diaries or repeat test counts in the roadmap.

## Checks and completion

Run `python scripts/test_public.py`, `python scripts/check_docs.py`,
`git diff --check` and focused tests for changed code. The reduced research suite
requires its native environment. Run broad regression for evaluator changes,
claims or releases, not every exploratory note. Never sync the native environment
to run core CI; use a disposable checkout.

Maintainers: after each completed work item, update the relevant current record,
check affected summaries, review the diff and commit under the user's authority.
Contributors document their scoped PR without editing shared logs/status.
Report blocked checks or commits honestly.
