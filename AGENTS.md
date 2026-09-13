# Fusion research: persistent working instructions

## Start each session

Read `docs/README.md`, `docs/STATUS.md`, `docs/PROJECT_PLAN.md`, then the relevant
detail directory's `README.md` and latest entries in `docs/logbook/VALIDATION_LOG.md`.
Check Git status and running experiments before changing anything. Preserve user
changes, pinned external checkouts, failed runs and immutable evidence.

## Documentation architecture (user requirement, 2026-09-11)

- `docs/` root contains only `README.md`, `STATUS.md`, `PROJECT_PLAN.md`: a concise
  scientific overview suitable for a professor evaluating the project and progress.
- Put detailed protocols/results in exactly one purpose-specific child directory:
  `optimization`, `geometry`, `qi`, `engineering`, `validation`, `squid_c`, `logbook`.
- No directories below these children. No root-level experiment reports.
- Every child has a `README.md` explaining its purpose, current conclusion/limits
  and the contents of every document it contains. Update it when adding a document.
- A new purpose requires a justified documentation change and a root overview link;
  do not create miscellaneous dumping grounds or date-based folder hierarchies.
- Keep top-level status/plan concise and current when a material finding changes
  the project's assessment. Detailed evidence and chronology belong below.
- Replace outdated overview summaries instead of appending successive experiment
  histories. Keep each top-level overview readable in a few minutes; link to the
  detail reports/journal for the complete chronology and preserved failures.
- Use relative Markdown links for navigation. Run `python scripts/check_docs.py`
  and tests before committing structural changes. Update live script paths when
  moving protocols; do not rewrite archived evidence paths/hashes to look current.
- The migration manifest maps original paths to destinations and records original
  hashes/revision. Historical experiment code/protocols remain retrievable in Git.

## After every completed work step (user requirement, 2026-09-12)

Documentation is part of completing each bounded work step, not an end-of-session
cleanup. Before starting the next step or handing off:

1. Update the relevant detail document and `docs/logbook/VALIDATION_LOG.md` with
   what changed or was learned, checks actually run and their outcomes, remaining
   limits and the next step. Record negative results and blockers as well as
   successes. Do not claim checks that were not performed.
2. Add material findings to `docs/logbook/FINDINGS.md` and durable decisions to
   `docs/logbook/DECISIONS.md` when applicable; keep the relevant folder overview
   accurate and index every new document.
3. Check `README.md`, `docs/README.md`, `docs/STATUS.md` and `docs/PROJECT_PLAN.md`
   against the completed step. Update affected summaries, next actions and dates
   before proceeding; do not duplicate detailed experiment logs at the top level.
   A step that does not change the overall assessment still needs its detail/log
   entry, but does not need a cosmetic rewrite of every overview.
4. Run `python scripts/check_docs.py`, `git diff --check` and proportionate tests.
   Record the results, review the intended diff and commit the scoped changes.
   If a permission or other blocker prevents a commit, explicitly record and
   report what is saved versus committed; never bypass the restriction or call
   the step fully closed. Keep historical evidence and failed runs immutable.

## Research discipline and autonomy

### Sharpened foundation milestone (explicit user correction, 2026-09-13)

Steps1/2 now mean a bounded reliable local reference/LPQA-filament toolchain and
the ability to run reproducible design iterations, not a new feasible optimum,
five-start comparison, SoTA advance or SQuID-C readiness. Follow the active
`docs/validation/FOUNDATION_ACCEPTANCE_PROTOCOL.md` and `docs/PROJECT_PLAN.md`.
Keep process qualification distinct from physical candidate acceptance. Never
relax historical physical thresholds or rewrite failures. Preserve all earlier
research at5971fee and its artifacts; QI-global/orbit/mechanics extensions remain
separate, unqualified future work. Do not start another long search or physics
branch unless it closes a specific active foundation gate. Once both sharpened
steps pass, document/commit and hand off rather than continuing into later research.
The canonical foundation runner normalizes paths. Its standalone overall auditor
currently requires an absolute run.json path for strict recorded-command matching;
use a fresh output path and retain any failed invocation as evidence.

Preregister new numerical studies before running them. Keep construction and
independent acceptance separate; retain negative results and all predeclared
resolution levels. Never relax limits after looking at outcomes. A test-suite
pass, solver success, low penalty, or data-intake schema is not physical admission.
Do not claim SoTA or readiness while scientific gates remain open. Record input,
code, environment, budget, derivative work, failures and validation provenance.
Use explicit named physical-DOF mapping when replaying serialized coil arrays.

The user requests autonomous continuation with intermediate documentation and
local commits, without routine confirmation questions. This does not authorize
publishing/pushing, contacting authors or modifying external repositories. Do not
run heavy jobs concurrently with controlled wall-time experiments. Keep the root
native benchmark environment intact; use a separate clone for core-only sync.

Before large clones, installations or builds, estimate the selected checkout and
build size and verify a disk reserve. Never materialize a benchmark's historical
submission archive merely to obtain source code. Recheck space between phases;
do not run heavy searches concurrently with resource-intensive installs/builds.
On IO failure retain last successful checkpoints unchanged, record terminal
failure separately, and distinguish console progress from persisted state.
