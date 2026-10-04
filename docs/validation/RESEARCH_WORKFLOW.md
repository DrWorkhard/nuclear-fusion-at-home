# Explore quickly, confirm separately

Updated 4 October 2026. Existing registered studies retain their original rules.
[Review policy](REVIEW_POLICY.md) · [Roadmap](../PROJECT_PLAN.md)

| | Exploration | Confirmation |
| --- | --- | --- |
| Purpose | Answer a question, find candidates, diagnose failures | Support a specified scientific claim |
| Before work | Question, input/evaluator identities, time and storage ceilings | Preregister hypothesis, selection, metrics, thresholds, budgets and holdouts |
| Adaptation | Allowed; record changes and failures | Registered rules only; deviations invalidate that confirmatory claim |
| Checks | Relevant unit/sanity checks and reproducible outputs | Independent acceptance with appropriate numerical and physics checks |
| Output | Labelled observation or candidate | Only the claim supported by completed checks |

Use existing tools and at most one page per exploration: question, inputs, script,
output and conclusion. No new protocol, generic runner, per-script checker or
full historical regression by default. Test changed code; broaden regression for
shared evaluators, claims and releases. Freeze candidates/comparators before
confirmation; adaptively consulted data is not an unseen holdout.

Preserve failures, source identities, named physical coordinates, current/target
conventions and acceptance limits. A sampled penalty pass is not continuous
geometry acceptance; an unresolved bound is not proof of infeasibility. Investigate
metric/scale/target mismatches before proposing separately reviewed gate changes.
Exploration cannot establish physical acceptance, superiority, Step 4 or MS1.

Declare wall-clock, storage and disk-reserve limits. Add coefficient/evaluation
caps only for a scientific reason; old studies keep theirs. Spending disclosure
is optional for contributors. Isolate untrusted PR execution and preserve the
native environment. Same-machine independent arithmetic, another physics code,
another machine and external expert review are different checks.

Follow [AGENTS.md](../../AGENTS.md) for ownership, evidence retention, documentation
homes and maintainer completion. Keep decisions in the roadmap, lessons beside
their results and only latest checks in the verification record. Git preserves
committed history, not ignored raw data. Store full completed records in immutable
annotated `evidence-*` snapshots and short tag/commit-linked conclusions on `main`;
follow [the archive procedure](REPRODUCING_RESULTS.md). Backup/restore of local raw
data remains a separate obligation.
Record question-to-answer time when measured, never test/commit volume as science.

`python scripts/check_docs.py` enforces local links, folder indexes and whitespace-
word budgets: README/README_agents 1,500 each; AGENTS 700; docs overview/status/plan
600 each; Step 4 900. Status has at most eight table rows. Only README_agents and
the plan carry the matching roadmap; these editorial checks do not validate physics.
