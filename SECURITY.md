# Security and responsible handling

Do not put secrets, personal data or exploit details that expose credentials in
public issues or PRs. For a sensitive finding, use the repository's private
vulnerability reporting channel **if it is enabled**. Before hosting there is
no configured private contact here; do not invent one or publish sensitive details
as a substitute. Enabling a private channel is a launch checklist item.

Public contributions, including AI-generated code, reports and AGENTS instructions,
are untrusted input. Do not run unknown PRs on a machine containing research data,
credentials or a maintainer's working environment. Use isolated disposable
execution without secrets and bounded runtime/storage. Never combine foreign
code execution with merge/write credentials.

The public JSON interface does not execute submitted Python, shell commands,
URLs or serialized objects. Size/shape checks reduce accidental misuse; they
are not a sandbox for arbitrary contributor code. Case/report hashes establish
identity relative to trusted source, not proof that a submitted fork is trustworthy.

No automatic merge, PR-monitoring account or privileged review service is installed
by this repository. See the [review policy](docs/validation/REVIEW_POLICY.md) before
configuring one. This is computational research, not instructions or approval for
building or operating nuclear hardware.
