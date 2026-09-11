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
- Use relative Markdown links for navigation. Run `python scripts/check_docs.py`
  and tests before committing structural changes. Update live script paths when
  moving protocols; do not rewrite archived evidence paths/hashes to look current.
- The migration manifest maps original paths to destinations and records original
  hashes/revision. Historical experiment code/protocols remain retrievable in Git.

## Research discipline and autonomy

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
