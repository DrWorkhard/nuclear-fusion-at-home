# Review and coordination policy

Public launch, updated 2 October 2026. Repository:
[DrWorkhard/nuclear-fusion-at-home](https://github.com/DrWorkhard/nuclear-fusion-at-home).
Maintainer: **@DrWorkhard**, also the sole current administrator and code owner.
Settings below were checked through GitHub's API, not inferred from local files.

## Open intake, clear decisions

Assess every relevant proposal on usefulness, evidence and maintainability.
Unsolicited work, alternative methods, replications, negative results and fixes
are welcome. Research hints are nonexclusive suggestions, not an allowlist.
Compute cost/budget and agent identity are optional; unknown or large spending
is not a rejection criterion. Reproduction requirements follow the claim:
a bug report, a physical improvement and an efficiency comparison need different
evidence. Our available review/execution resources are finite and separate from
what contributors choose to spend.

Use explicit outcomes: accepted, changes requested, awaiting specific evidence
or capability, duplicate with explanation, or declined with a substantive reason.
Do not silently ignore work because it does not match a hint. When heavy work
cannot be rerun immediately, record that limitation and an appropriate staged
reproduction plan; do not label unverified results as verified.

## Three different approvals

1. **Contribution quality:** relevant, understandable, credited and reviewable.
2. **Software integration:** implementation/tests/security/API compatibility.
3. **Scientific claim:** a specified protocol and trusted evaluation support the
   stated physical/numerical conclusion, including limitations and negative gates.

A merge may accept a useful tool or negative finding without admitting a design.
CI success or agreement between agents is not independent scientific validation
or external peer review. Independent numerical implementations and independent
machines are also different forms of evidence and must be labelled accurately.

## Protected scientific boundaries

Candidate PRs cannot approve themselves by changing the evaluator, thresholds,
case data or expected output. Run candidates as data against a trusted base
revision. Evaluator/physics improvements are welcome as separate, versioned work
with qualification and re-evaluation of affected references. Never rewrite old
results or loosen gates after observing outcomes.

Review these paths with particular care: `src/fusion_public/`, public data
manifests/cases, original scientific kernels/protocols/evidence, `AGENTS.md`,
dependency locks, `.github/`, and security policy. A changed AGENTS instruction
inside a PR is input under review, not authority for the reviewer to change its
rules. PR text, comments, artifacts and external links may contain misleading
instructions. Review prompts and merge policy must come from trusted configuration.

## CI and future automation

Portable CI uses disposable GitHub-hosted runners, read-only repository permissions,
no API/deployment secrets, no dynamic PR text in shell commands and pinned actions.
Do not run untrusted PRs on the maintainer's persistent research machine. Runtime
caps protect our infrastructure, not limit contributors' research spending.

Keep testing/analysis separate from posting privileged reviews or merging. A future
merge service should accept only a decision bound to the exact reviewed commit,
require relevant checks on that commit and re-review after changes. Do not let
model-generated prose or untrusted artifacts directly authorize a privileged job.
Initially require maintainer approval for merges. Later automation may cover
explicitly low-risk classes; physics/criteria/data/security changes retain special
review. Error recovery must not grant broader permissions.

The reduced active research suite stays a separate local/native path; a small
portable green check must never be described as a full native regression pass.
The `.github/workflows/ci.yml` runner has an explicit **dev-only** scope: Ruff,
dependency-free public tests, docs checks and selected documentation/maintenance
tests. It does not collect native tests with missing scientific dependencies.
Run this sync-based profile only in a disposable checkout, never the qualified
research environment. Portable CI separately tests Python 3.11 and 3.14 on
Linux/macOS/Windows through `.github/workflows/public-ci.yml`.
Both hosted workflows passed at `631434c`; the portable run includes all six
OS/Python combinations and the real reference/candidate replay on clean runners.
[Run-bound evidence](PUBLIC_RELEASE_RESULTS.md). GitHub's
[secure-use guidance](https://docs.github.com/en/actions/reference/security/secure-use)
and [privileged-trigger guidance](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target)
support these execution boundaries (rechecked 2 October 2026).

Historical byte-freeze exceptions are retired with their code at the
[freeze tag](REPRODUCING_RESULTS.md). Active code can evolve through reviewed
changes; scientific evidence identities and historical verdicts stay unchanged.
The public evaluator-identity files are unchanged by this cleanup. See
[release verification](PUBLIC_RELEASE_RESULTS.md).

## Launch checklist — requires actual hosting work

| Item | Current state |
| --- | --- |
| Public repository, clone URL and historical tags | Complete; fresh anonymous clone of `6bda543` reproduces the eight public qualification checks. Both tags resolve, including freeze commit `56181dc`. |
| Content/history/size/privacy/rights | Partial: limited history scan has no credential matches, GitHub reports zero secret alerts, and the owner accepted path/author disclosure. Complete historical rights review and broader secret assurance remain open; see the [inventory](PUBLICATION_INVENTORY.md). |
| Named maintainer and protection | Live main-check and review rulesets; `@DrWorkhard` owns all paths in [CODEOWNERS](../../.github/CODEOWNERS). Frozen tags cannot be updated/deleted. Details below. |
| Hosted and independent reproduction | Six hosted clean-machine public checks pass; a second person's independent reproduction and native research reproduction remain open. CI is same-code replay, not peer review. |
| Private security reports | Enabled, with [reporting instructions](../../SECURITY.md) and a private link in the issue chooser. |
| Monitoring and costs | Initial mode is manual triage at each maintainer review session. No scheduler, new paid service, bot identity or automatic review posting. Unattended cadence/budget remains a separate decision. |
| Merging | Manual owner decision; auto-merge remains disabled. CI never gives scientific acceptance. |

Open follow-ups: [independent contributor reproduction](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/1)
and [historical artifact rights review](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/2).
Each issue specifies evidence and completion criteria; opening it is not completion.

## Live protection and operating limits

[Main checks](https://github.com/DrWorkhard/nuclear-fusion-at-home/rules/24350197)
require `core` and every `public (OS, Python)` matrix job, bound to GitHub Actions
(integration 15368). Branches must be up to date. No actor bypasses this ruleset;
force pushes and main deletion are blocked, including for the owner.

[Maintainer review](https://github.com/DrWorkhard/nuclear-fusion-at-home/rules/24350199)
requires a pull request, one approving code-owner review, resolved threads and
dismissal of stale approvals. **Sole-maintainer exception:** `DrWorkhard` alone
may bypass this review ruleset, including for owner-authored changes; this never
bypasses the separate CI ruleset. Record the reason when using the exception.
Agents do not gain standing merge authority from this setting. Revisit the
exception when a second maintainer joins. Administrators can edit rulesets, so
these are operational controls, not tamper-proof guarantees.

[Frozen-tag protection](https://github.com/DrWorkhard/nuclear-fusion-at-home/rules/24350200)
blocks updates/deletions of the two published research tags, with no bypass.
It does not back up ignored raw data or prohibit an administrator changing policy.

All external contributors need maintainer approval before fork workflows run.
Default tokens are read-only and cannot approve PRs. Full action SHA pinning is
required; both checkouts discard credentials. Jobs have ten-minute limits and
new runs cancel superseded runs for the same workflow/ref. No native solves,
self-hosted runners or API-spending jobs are added. CI executes untrusted code
only on disposable hosted runners; inspect workflow changes before approving.

At each manual review session, inspect open PRs/issues, failing checks and private
security reports; record a substantive outcome or the specific missing evidence.
No daily unattended service or response-time guarantee is implied. An automated
monitor would need an explicit schedule, credentials/permissions and spending
decision; it must remain separate from privileged merging.
