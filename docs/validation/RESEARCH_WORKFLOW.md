# Research workflow: explore quickly, confirm separately

26 September 2026. Applies prospectively; existing registered studies and their
limits remain unchanged. [Review policy](REVIEW_POLICY.md) · [Roadmap](../PROJECT_PLAN.md)

## Choose the lane before starting

| | Exploration | Confirmation |
| --- | --- | --- |
| Purpose | Find promising methods, test reachability, diagnose failures | Support a specified scientific claim |
| Before work | Short question, input/evaluator identities, a local time/resource ceiling | Preregister hypothesis, selection, metrics, thresholds, budgets and holdouts |
| Adaptation | Allowed; record changes and failed attempts | Only the registered rules; deviations invalidate that confirmatory claim |
| Checks | Relevant unit/sanity checks and a reproducible record | Independent acceptance, appropriate numerical/physics checks and source-bound evidence |
| Output | Labelled exploratory observation or candidate | Only the claim supported by the completed checks |

An exploratory run needs a short record, not a new protocol, generic runner,
full regression or separate qualification commit by default. Reuse existing
tools. Tests follow the risk of changed code; full native regression is warranted
for shared evaluator changes or an explicitly required acceptance/release check,
not every analysis of saved data. Record checks actually performed. Reuse proven
unchanged components without calling that a new qualification.

Exploration may report measured scores and useful negative observations, but
cannot claim physical acceptance, comparative superiority, Step 4 completion or
MS1. Freeze any candidate and comparator **before** independent confirmation;
do not reuse an adaptively consulted dataset as an unseen holdout. Previously
registered work, including the residual diagnosis, keeps its original contract.

## Shared protections

Keep failed results, source identities, current/normalization conventions and
historical thresholds. Vary geometry limits only in separately labelled studies;
an uncertified point is neither accepted nor proven impossible. Do not weaken a
verifier to admit a candidate. Negative positive-control results call first for
a metric/scale/target investigation, not automatic threshold relaxation.

Local execution always needs finite time, storage and disk-reserve limits; this
does not require contributors to disclose their spending. Isolate untrusted PR
code, preserve the native environment, and never imply publishing/contact/merge
authorization. Same-machine separate arithmetic, a second physics code, a second
machine and external expert review are different checks; label them separately.

## Ownership and documentation

The coordinating maintainer is the single editor of root README, status, plan,
overview and shared notes during a work session. Assign each delegated writer
explicit non-overlapping files, or use separate branches with deliberate merges.
Reviewers send findings; they do not edit another writer's files concurrently.
Public-facing changes receive a concise editorial pass before publication.

Keep one home per topic: README for motivation/onboarding, roadmap for priorities,
status for scientific results, step/detail pages for methods and qualification,
and shared notes for current decisions, lessons and latest checks. **History lives
in Git.** Delete superseded plans, completed progress diaries and duplicate archives;
do not move them into a new history document. Repair links and keep any still-useful
conclusion in its canonical page. Retain source-bound protocols, negative results
and evidence needed to reproduce supported claims; inspect dependencies before
deletion. New prose is English; scientific records may retain their original language.
The documentation check enforces word/row budgets and roadmap placement, not
scientific truth, language fluency or every possible semantic duplication.

Current budgets (whitespace-delimited Markdown tokens): root README 1,500;
AGENTS 700; docs overview, status and plan 600 each; current Step 4 page 900.
Status permits at most eight table data rows. Only root README and the plan hold
the roadmap table, with matching names/statuses. `python scripts/check_docs.py`
enforces these limits; historical detail reports are not truncated to fit them.

After a completed work item, update the current result/check/decision record, review
affected summaries and commit under current user authority. Do not write a new
report for every passing test, append a session chronicle or copy test counts into
the roadmap. Earlier records are recoverable with `git log -p -- path/to/file` and
`git show <revision>:path/to/file`. Git does not back up ignored local artifacts;
their retention/backup obligations remain separate. Track elapsed
question-to-answer time and science/tooling effort in the work record when known;
do not invent historical timings or use test/commit volume as scientific progress.
