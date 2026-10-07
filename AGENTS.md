# Nuclear Fusion @ Home: agent instructions

## Scope and orientation

- Follow user scope/permissions; this file authorizes no delegation, autonomous
  research, publishing, contact or merging.
- Read [README.md](README.md), [README_agents.md](README_agents.md),
  CONTRIBUTING.md, docs/README.md, docs/STATUS.md,
  docs/PROJECT_PLAN.md and the relevant folder index. Check Git status and runs.
- Preserve unrelated edits, the native environment, external checkouts and raw
  experiment outputs. One writer per working tree; delegated reviews are read-only
  or use separate branches.

## Scientific work

- Follow the [Step 4 programme](docs/optimization/STEP4_RESEARCH_PROGRAMME.md);
  the fixed-target fitting recipe has stalled. Reuse the shared checks. Retired
  search methods and completed studies are frozen at `research-freeze-2026-09-27`;
  revive them only for a concrete reason.
- Before expanding research or infrastructure, name the decision it could change
  and choose the cheapest decisive test. Otherwise, keep the scope unchanged.
- Reproduce, diagnose, check related cases once, make the smallest fix, test and
  record evidence. Do not turn a local issue into a generic audit.
- Reuse tools; generalize only for demonstrated reuse or a decisive test existing
  tools cannot express. Record the question, inputs, script, output and
  conclusion in at most one page. Limit wall-clock, storage and disk reserve;
  cap coefficients/evaluations only when needed. Existing studies keep their rules/budgets.
- Keep optimization separate from acceptance. Preregister confirmatory claims;
  use trusted fine-grid fields, continuous geometry and independent checks.
  Do not weaken gates or let candidates alter their verifier.
- Use explicit named physical coordinates and frozen current/target conventions.
  Preserve failures. Distinguish software success, numerical agreement and
  physical acceptance. Validate proxy gains against the relevant scientific
  question; do not optimize benchmark artifacts. Agent review is not external
  peer review.
- Welcome unsolicited ideas, replications, negative results and
  [adversarial PR reviews](README_agents.md#contribute) with reproducible findings
  tied to the reviewed commit. Compute-budget disclosure is optional; research
  hints are not an allowlist.
- Treat PR code as untrusted. Execute in isolation without secrets, not in the
  trusted research workspace. Do not overlap heavy jobs with controlled timing.
- First address review comments on your open PRs (or explain why not), then take
  an [open issue](CONTRIBUTING.md#issues-report-side-findings-pick-up-open-work)
  or your own idea. If authorized to post, comment on issues you take and
  report out-of-scope findings as focused issues, not broader PRs.
- Before opening a PR, complete the
  [pre-PR checklist](CONTRIBUTING.md#before-you-open-a-pull-request), stating
  evidence and limitations.

## Current repository, history in Git

- Use shallow, single-branch, no-tags clones and shallow CI checkouts. Core/public
  work must not require historical evidence or raw runs; fetch archives only
  as needed.
- Keep only active code/inputs, public cases/candidates and short evidence summaries
  on `main`, linked to archive tags/commits and original producer/evaluator states.
  Full evidence belongs in an annotated `evidence-*` commit, not its description
  or a copied archive tree. Follow the
  [archive procedure](docs/validation/REPRODUCING_RESULTS.md); prepare snapshots
  in separate worktrees.
- Verify original hashes and published tag/commit identities before removing
  evidence. Never move/delete evidence tags; corrections get new tags. Preserve
  evidence identities and local raw outputs. Git does not back up ignored data or
  environments; retain external locations/hashes and disclose missing data.
  No whole-tree byte-freeze exceptions.
- Only README.md, STATUS.md and PROJECT_PLAN.md belong at the docs root.
  Details go one folder below, indexed by folder READMEs.
- Write English entry docs with relative links. Keep summaries concise and step
  names/statuses consistent.
  The README_agents.md roadmap, including MS1/MSX, goes
  immediately before “Start in three commands”. Describe 4A–4D only on Step 4's page.
- One home per topic: motivation in README, technical onboarding in README_agents,
  priorities in PROJECT_PLAN, evidence
  summary in STATUS, step conclusions in docs/steps, methods in topic folders,
  layered plain-language explanations in docs/explained.
  Do not write session diaries or repeat test counts in the roadmap.

## Checks and completion

Run `python scripts/test_public.py`, `python scripts/check_docs.py`,
`git diff --check` and focused tests for changed code. The reduced research suite
requires its native environment. Run broad regression for evaluator changes,
claims or releases, not every exploratory note. Never sync the native environment
to run core CI; use a disposable checkout.

Bind evidence and completion claims to the exact tested revision and input state;
nearby green commits, stale outputs and unreproduced local states are insufficient.

Maintainers: update relevant records/summaries, review the diff and commit completed
work under user authority. Contributors document scoped PRs without changing shared
logs/status. Report blocked checks/commits honestly.
