# Contributing to Nuclear Fusion @ Home

People and their agents are welcome. You do **not** need a listed issue, prior
permission, a particular model, a new best score, or a compute-spending report.
We welcome relevant unsolicited work, replications, bug reports, critical reviews,
negative results, documentation, new methods and proposals outside our current
[research hints](docs/optimization/RESEARCH_HINTS.md). Hints are invitations,
not an allowlist. Code without an AI agent is equally welcome.

## Start here

1. Read the [project introduction](README.md), [technical contributor guide](README_agents.md)
   and [scientific status](docs/STATUS.md). Agents also follow [AGENTS.md](AGENTS.md).
2. Run the [portable quickstart](docs/validation/PUBLIC_QUICKSTART.md). It needs
   only Python 3.11+, not our private workspace, large datasets or an API key.
3. Make a small, coherent change on your branch. Run `python scripts/test_public.py`
   for the public layer, and relevant additional tests for the changed subsystem.
4. Open a pull request explaining the contribution, evidence and limitations.
   An issue is optional, including for work not on the hints list. Large changes
   often benefit from discussion, but unrequested work will still be assessed.

## What to include

- **Contribution:** what changed or what we learned, and why it matters.
- **Evidence:** tests actually run, reproduction instructions and result files
  when applicable. Identify the reference/evaluator version for numerical claims.
- **Limitations:** what has not been tested; failed checks and negative results
  are useful evidence, not something to hide.
- **Attribution:** credit people, source code and datasets; include applicable
  license notices. Never submit secrets, credentials or personal data.

Compute time, money spent, hardware, model/provider and relationship to a research
hint are **optional**. Their absence or the amount spent does not disqualify a
contribution. Claims specifically about speed, resource efficiency or equal-budget
comparisons do need measurements supporting that claim. We assess the contribution,
not the contributor's spending. Maintainer/CI execution limits only bound the
resources we can run; expensive external work can be reviewed from evidence and
independent reproduction plans without automatic rejection.

For structured metadata, copy [examples/contribution.json](examples/contribution.json)
and run `python fusion.py public check-submission --file path/to/contribution.json`.
This format is optional, and the checker validates structure, not scientific merit.
It never executes commands or follows URLs in your description.

## Designs and research results

The first public candidate interface accepts the fixed six-coil Fourier schema
in [the starter](examples/clear-coil-samples-v1/README.md). Edit only the candidate
in your experiment; do not alter the case or evaluator to improve its reported
score. Other designs, novel physics or different methods remain welcome through
ordinary PRs/proposals; the initial file format is not the project's scientific
boundary. Explain what a suitable independent check would require.

Exploratory PRs that lower the starter's sampled errors are explicitly welcome.
Aim below reference normal RMS 0.304207 and inner-vector RMS 0.380435; report both
and disclose trade-offs. See [score interpretation](docs/validation/PUBLIC_QUICKSTART.md#what-the-report-means).
The starter has public sparse samples and frozen currents. A lower score is
not a full-surface/geometry/QI pass. Label exploratory work honestly. Before a
confirmatory project study, agree a versioned evaluation protocol; we do not
retroactively reject useful exploratory work for lacking preregistration.
Changes to evaluators/criteria are welcome but need separate review from the
candidate they would admit. Preserve old benchmarks and failures.

The [two-lane workflow](docs/validation/RESEARCH_WORKFLOW.md) keeps exploration
lightweight and confirmation separate. The [Step 4 programme](docs/optimization/STEP4_RESEARCH_PROGRAMME.md)
sets priorities toward a full-grid coil challenge; that expanded
challenge is planned, not yet supplied by the sparse starter.

Keep large raw runs outside Git; provide a reproducible recipe and content hashes
for necessary artifacts. A tiny derived fixture can be committed with clear
provenance/license and a size justification. Do not reformat historical evidence
or rewrite its old absolute paths. New portable exports have their own identity.

For a public candidate PR, use `submissions/<unique-study-name>/candidate.json`
and a short `README.md` beside it. Commit the candidate (about 10 KB), your exact
reference/evaluator revision, reproduction commands, both scores and limitations.
Keep generated reports/audits in ignored `results/`; put the audit outcome in the
summary rather than force-adding the larger report. See the
[submission layout and git add example](submissions/README.md). Other kinds of
contribution need not use the candidate folder or this format.

## Review, credit and conduct

Keep PR documentation local to your change: usage text, a focused report, or the
PR description with actual checks and limitations. Keep documentation current;
remove superseded plans and duplicate history rather than creating archives.
Git retains earlier versions. Frozen protocols and code resolve at the
[research tag](docs/validation/REPRODUCING_RESULTS.md); scientific evidence and
necessary raw data retain their identities, including negative findings.
Maintainers integrate current
verification, decisions, status and roadmap; contributors do not need to edit
those files or commit after every small step. The general instructions in
[AGENTS.md](AGENTS.md) apply to outside agents; its maintainer completion duties
apply only to repository-owner sessions.

Review checks usefulness, correctness, reproducibility, scope, security and
maintainability. Being unsolicited is not a negative criterion. Where evaluation
is not yet possible, reviewers should record the specific missing evidence or
capability, not ignore the proposal. Passing CI is not a scientific endorsement.
See the [review policy](docs/validation/REVIEW_POLICY.md).

Keep discussion constructive and evidence-based. Credit contributions and
reproductions by their actual role; agent assistance does not remove the submitter's
responsibility for the PR. Criticize claims and methods, not people. Participation
does not imply authorship on every later publication; attribution should follow
the actual contribution. See [CITATION.cff](CITATION.cff) and retain upstream credit.
