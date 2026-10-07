# Contributing to Nuclear Fusion @ Home

Relevant unsolicited ideas, designs, replications, fixes, critical reviews and
negative results are welcome. No listed issue, prior permission, AI agent, model,
new best score or compute-spending report is required. The
[research hints](docs/optimization/RESEARCH_HINTS.md) are invitations, not an allowlist.

## Start here

1. Read the [vision](README.md), [technical guide](README_agents.md) and
   [scientific status](docs/STATUS.md). Agents also follow [AGENTS.md](AGENTS.md).
2. Run the [portable quickstart](docs/validation/PUBLIC_QUICKSTART.md): Python
   3.11+, no installation, API key or native research artifacts. Use its shallow
   clone command; neither full Git history nor evidence archives are required.
3. Make a coherent change, complete the checks below and open a PR explaining
   what changed or was learned, evidence, limitations and attribution.

## Before you open a pull request

1. Update your branch with current `main` and resolve conflicts.
2. Run from the repository root:

   ```bash
   python scripts/test_public.py
   python scripts/check_docs.py
   uvx ruff@0.16.5 check .
   git diff --check
   ```

   Run focused tests for changed code. If changing `scripts/verify_public_release.py`
   or anything it copies, also run
   `python -I -S scripts/verify_public_release.py --output results/<fresh-name>`.
   `./scripts/run_core_ci.sh` repeats core CI with uv; use a disposable checkout
   so its sync cannot replace the native research environment.
3. Reproduce your commands from a fresh clone. Required inputs must be committed
   or explicitly obtainable; never depend silently on ignored `results/` files.
   Label local-only evidence as not distributed.
4. Keep Windows compatibility: use `encoding="utf-8"` for text I/O. Pin line endings
   in `.gitattributes` for files whose bytes you hash or compare. `examples/`,
   `src/fusion_public/` and `public_tests/` are already covered. Ruff checks import
   order, `zip(..., strict=True)` and the 100-character line limit.
5. List actual checks and untested parts in the PR. Hosted Linux/macOS/Windows CI
   must pass on the current branch before merging.

## Issues: report side findings, pick up open work

Search [open issues](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues)
for useful work and duplicates. For a finding outside your PR, open one focused
issue when authorized to post: observation, revision, reproduction, impact and
uncertainty. Use the bug/research templates; report security issues privately via
[SECURITY.md](SECURITY.md). When you start work on an issue, comment there that
you are working on it (agents: if authorized to post), so others avoid duplicate
work; if you stop, say so.
`Fixes #N` closes an issue on merge; `Related to #N` does not. Neither an issue nor
a research hint is required for a contribution.

## Evidence and designs

Explain the contribution, exact reference/evaluator version, reproducible inputs,
checks actually run, failures and limits. Credit people, upstream code and data;
retain their licenses and exclude secrets/private data. Hardware, AI model and
spending are optional, except that speed or equal-budget claims need measurements.
Review capacity limits what maintainers can rerun, not what others may contribute.

Public candidate PRs use `submissions/<study>/candidate.json` and a short adjacent
`README.md` with both sampled errors and a replay outcome. Keep generated reports
in ignored `results/`; see the [submission layout](submissions/README.md).
Sparse and dense boundary scores are diagnostics, not full physical acceptance.
Other designs/methods are welcome outside the six-coil schema; explain the checks
they need. Optional metadata uses [contribution.json](examples/contribution.json)
and `python fusion.py public check-submission --file <path>`; that validates
structure only and never executes submitted commands or URLs.

Keep exploration lightweight and confirmation separate under the
[research workflow](docs/validation/RESEARCH_WORKFLOW.md). Freeze candidates and
comparators before independent confirmation. Never improve a candidate by changing
its case, evaluator or acceptance rules; evaluator changes require separate review.
Do not retroactively demand preregistration of exploratory contributions.

Retain failures and original scientific evidence identities. Keep short conclusions
and tag/commit pointers on `main`; complete evidence files belong in an annotated
`evidence-*` snapshot with the producer/evaluator revision, dirty state, hashes,
reproduction command and data availability. Maintain archive tags without updates
or deletion; corrections receive a new tag. Verify the published archive before
removing tracked payloads. Maintainers publish tags under the user's authority;
contributors propose a summary and evidence snapshot in their scoped PR.
Large raw outputs stay outside Git with hashes and an obtainable reproduction
recipe where possible; a tag does not back them up. Preserve local raw runs and
keep small inputs required by current evaluators. See the
[archive workflow](docs/validation/REPRODUCING_RESULTS.md).

## Review and credit

Keep PR documentation local to its change. Maintainers integrate shared status,
priorities and verification; contributors need not edit those records. Delete
superseded plans and duplicate prose: history lives in Git.

Review assesses usefulness, correctness, reproducibility and maintainability;
missing evaluation capability should be stated explicitly. CI success is not
scientific endorsement. See the [review policy](docs/validation/REVIEW_POLICY.md).
Criticize methods and claims, not people. AI assistance does not remove submitter
responsibility; credit contributions by their actual role, following
[CITATION.cff](CITATION.cff) and upstream attribution.
