# Current verification

Updated 27 September 2026. This page records the latest maintenance check, not
an append-only session history. Git retains previous versions; individual result
reports retain the checks supporting their scientific claims.

## Repository cleanup

Removed superseded progress/planning pages, completed README review paperwork
and the duplicate Step 4 archive. Condensed the shared logs into current decisions,
lessons and this verification record. Updated links, stale next actions and the
current-state documentation policy. No scientific code, protocol, evaluator,
threshold, case, source identity, saved evidence or local run was changed.

Checks actually run for this documentation-only cleanup using the existing `.venv`:

- `python scripts/test_public.py`: **47 passed** (3.742 s).
- Targeted pytest: **52 passed** (final repeat: 27.58 s), covering documentation, release
  maintenance, actual README workflow and foundation acceptance/preservation.
- Isolated stdlib-only `scripts/check_docs.py`, repository Ruff and `git diff --check`: pass.
- Local file-link check across all **214 remaining tracked Markdown files**: no broken targets.
- Git diff confirms no changes to code, protocols, evidence, data or environments;
  all ten removed files are tracked and recoverable from the preceding `1c805af`.
- Independent read-only documentation review finds no blocking issue; a minor
  stale-prerequisite phrase was corrected. This is internal review, not peer review.

The retained three shared-note paths satisfy existing preservation tooling;
their old chronology lives in Git. No archive document was created.

## Scientific and release checks

- [Fixed field comparison](../optimization/FIXED_FIELD_PROBE_RESULTS.md): latest
  completed field study and its source-bound 5,654-test pre-execution regression.
  That regression does not cover all subsequent edits.
- [Public release verification](../validation/PUBLIC_RELEASE_RESULTS.md): dated
  portability/compatibility checks, known failures and unverified hosted coverage.
- [Pending residual analysis](../optimization/FIELD_RESIDUAL_PROGRESS.md): component
  checks exist; final execution qualification and real-array analysis remain open.

No new physics calculation, full native regression, hosted CI, external review or
publication follows from a documentation cleanup.
