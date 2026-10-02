# Security and responsible handling

Do not put secrets, personal data or exploit details that expose credentials in
public issues or PRs. For a sensitive finding,
[submit a private vulnerability report](https://github.com/DrWorkhard/nuclear-fusion-at-home/security/advisories/new).
Private reporting is enabled; reports go to the maintainer, **@DrWorkhard**.
Include the affected commit, impact and a minimal reproduction without live
credentials or unnecessary personal data. If the form is unavailable, do not
publish the sensitive details in an issue. There is no guaranteed response time
or bug-bounty programme.

Security maintenance targets the current `main` branch. Historical tags preserve
research evidence, not supported software releases. Report historical findings
privately too; do not rewrite frozen evidence or tags to conceal them.

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
