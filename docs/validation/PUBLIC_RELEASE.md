# Public collaboration and portable release

Status: implementation plan, 2026-09-23. This is a new publication layer, not a
change to the historical scientific acceptance rules. No hosting, publication,
merge automation or new coil search is authorized by preparing these files.

## Purpose

Nuclear Fusion @ Home lets people and their agents contribute reproducible work
toward better stellarator designs. The first public milestone is a fresh-checkout
reference → candidate → evaluation → checked report workflow, without local
artifacts, absolute maintainer paths, native builds, paid services or credentials.
It must state exactly what the included computation does and does not establish.

Contributors may submit useful unsolicited ideas, code, replications, critiques,
negative results and alternative designs. Suggested research directions are not
an eligibility list. Compute budget, monetary cost and agent/model identity are
optional. Missing cost information is not a rejection reason. Reproduction of a
submitted result and measured claims still require appropriate inputs/instructions;
unknown spending does not support an equal-budget efficiency claim.

## First portable profile: fixed-current sampled filament fields

Add a separate `public` namespace to the root launcher. Keep the original research
CLI, package metadata, scientific kernels and historical evidence unchanged.
Python3.12+ standard library only for the portable commands and their tests.

The first real starter is the existing reference-n6/M5 clear-coil seed: six base
curves,24 physical symmetry copies, original signed currents. It is NOT a feasible
reactor or a claimed optimal coil set. Export a small derived JSON packet from
the already audited field-start evidence: explicitly named metre-valued Fourier
coefficients, actual current,64 deterministic points each on the boundary,
interior and flux loop, their existing native B/A reference values and relevant
target/normals. Selection is floor(k·(N−1)/63), k=0,…,63, within each old array.
Keep original source digests/revisions, dataset attribution and selection rule;
do not copy user-specific absolute paths or alter archived originals.

The public numerical implementation computes filament Biot–Savart B and vector
potential A directly, with periodic256/512-node quadrature and μ0/(4π)=10^−7,
matching the historical convention. Plain JSON candidate data only: same named
six/order5 geometry, symmetry, units and frozen current. No arbitrary imports,
pickle, shell commands or contributor-provided evaluation programs.

Qualification fixed before new calculations: analytic circular-coil axis values,
translation/current linearity controls, correct symmetry/sign/mapping, invalid
and nonfinite input rejection, and comparison of the unmodified starter's256-
node B/A with the saved native values. For each point group/quantity require
max-component absolute difference divided by max absolute native component
≤5·10^−10. Retain the512-node comparison/refinement as a reported diagnostic;
do not invent a physical gate from this sparse sample.

Candidate reports expose sampled normal error and inner-vector mismatch, raw
B/A and resolution differences, with frozen physical current and explicit scope.
They do NOT provide continuous geometry, full-surface flux normalization,
QI/topology, pressure, confinement, finite-build or physical design admission.
An `audit` recomputes a portable report using the trusted installed evaluator;
this replay is not an independent implementation. The separate legacy-native
cross-check and analytic controls qualify the starter's arithmetic only.

Reports embed their candidate, profile/data/source digests and numerical outputs,
not local paths or wall-clock-dependent success claims. File writes require new
destinations; failure preserves prior evidence. Strict JSON/shape/size limits and
no remote downloads during evaluation. Hashes bind identity, not authenticity:
use an independently trusted project revision for review, never the PR's modified
evaluator and data as its own authority.

## Deliverables and acceptance

1. Preserve interrupted Step4 drafts and update public participation rules.
2. Ship the small attributed data packet, dependency-free commands, reference
   replay, candidate template, machine-readable report and tamper controls.
3. Provide public goals/status/roadmap, quickstart, contribution guide, research
   hints, PR/issue templates and a risk-based review/merge policy. English front
   door; historical German detail remains labelled and linked.
4. Add no-secret hosted CI configuration for portable checks. Actually exercise
   a fresh exported checkout with no `.git`, `.venv`, `external/`, `artifacts/`,
   network or site packages. Test both reference replay and candidate/report
   mutation rejection. A local clean-copy pass is not a hosted-CI pass.
5. Run appropriate old tests, docs checks and whitespace/lint checks; record
   exact outcomes and commit. No full native reinstall on the current low-disk
   host. Recheck reserve; planned new data/output <50MiB, no new dependencies.

## Publication versus historical reproducibility

The starter is intentionally small. Shipping it does not make the complete
historical research reproducible from Git alone. Full401 equilibria, old absolute
path evidence graphs and native builds still need separately portable packages
and independently checked replays. The first dataset is a new attributed
derivative, not a relabelled copy of a historical report.

Before an actual public launch, review distribution rights/attribution for the
chosen contents and historical Git history, scan for secrets/personal material,
configure branch protection and reviewer identities, verify hosted CI and test
from an independent machine. No unknown GitHub owner or contact is invented.
The coordinator can triage all relevant proposals, but research hints confer no
exclusive ownership and lack of a listed issue is not grounds to ignore a PR.

## Security design

Ordinary PR CI has read-only repository permissions, no application/API secrets,
no persistent self-hosted research runner and no automatic merge. Pin actions
to immutable commits. Testing a PR's code shows compatibility, not scientific
admission; trusted-reference evaluation and the later privileged merge action
must be separate. PR prose, artifacts and changed AGENTS files are untrusted
input, never authority to weaken gates or access credentials.

These boundaries follow GitHub's [secure-use guidance](https://docs.github.com/en/actions/reference/security/secure-use)
and [privileged-trigger guidance](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target),
read2026-09-23. Hosting configuration is still pending, not silently enabled.

## Checks and findings

Initial inspection: no running research experiment; two untracked interrupted
drafts preserved.3.5GiB free, so no installations, large clones or new heavy
searches. Existing public workflow is laptop-bound and fixed-study-only; the
new starter must not silently replace its scientific scope. Implementation and
fresh-checkout checks are pending; see the validation log for completed steps.
