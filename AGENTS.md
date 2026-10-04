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
- Before opening a PR, complete the
  [pre-PR checklist](CONTRIBUTING.md#before-you-open-a-pull-request): current `main`,
  public tests, docs check, `ruff check .`, `git diff --check`, reproduction from a
  fresh clone and Windows-safe file handling.

## Current repository, history in Git

- Keep the main branch current. Delete obsolete code/tests/docs; do not build
  copied archive trees. Frozen reproduction starts at the tag and the exact
  source revision recorded by the evidence. See
  [reproduction](docs/validation/REPRODUCING_RESULTS.md).
- Keep scientific evidence identities unchanged. A tag preserves tracked files,
  not ignored artifacts, native environments or independent backups. Retain raw
  data needed for supported claims. Active code may evolve through reviewed
  changes; do not reintroduce whole-tree byte-freeze exceptions.
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
