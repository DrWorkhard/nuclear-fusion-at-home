# Simplicity review: what to keep, freeze and drop

27 September 2026. A second, independent review with one lens: **the smallest set
of things that gives the project a real chance to reach its next milestone.**
Reviewer: Claude (an AI coding agent); internal, not domain-expert review.
Reviewed state: commit `c1d2260`. Read-only; nothing was changed or run except
counting. [Review index](README.md) · [Roadmap](../PROJECT_PLAN.md) · [Status](../STATUS.md)

## Summary

**One method moves the key number, and most of the machinery belongs to another
method that did not.**

- **Plain penalized coil fitting works best so far.** The exploration sessions of
  27 September lowered the normal-field error from about 0.27 to **0.152 with
  continuously checked geometry** (0.137 with sampled geometry only), within a
  few minutes of compute.
- **Certified local search barely moved.** The same error went from 0.27 to 0.268
  over the preceding ten days of that approach. The registered residual
  diagnosis explains why: its steps follow the raw objective (88–90%), not the
  acceptance error (12–20%).
- **The stalled approach carries most of the weight.** Its certified-step search
  family accounts for **62% of all tests** (3,783 of 6,056) and **39% of library
  code**. The exploration that worked accounts for about 2% of tests.
- **Closed history is still live code.** Studies closed before 13 September still
  make up a third of the scripts (71 files, 14,700 lines). The full suite takes
  about eight minutes.
- **Even the "light" exploration lane is heavy.** One day of exploration produced
  13 commits, about 76,000 added lines (mostly evidence records) and 9,200 words
  of reports, each with hashes and separate checks. A derivative-guard hiccup
  alone took three commits and a 30-bundle diagnosis.
- **The front door is at its limit.** The README sits at 1,497 of 1,500 allowed
  words and introduces three milestone tiers: Steps 1–5, packages 4A–4D, and
  MS0/MS1/MSX.

**Five moves:**

1. Freeze the certified-search family and pre-September studies with a Git tag.
2. Run the working fitting method properly: longer, with wider limits, as a
   trade-off map.
3. Keep one trusted acceptance checker.
4. Make exploration records genuinely short.
5. Let one agent write at a time.

## The test applied

Keep something only if it passes at least one of three questions:

1. **Does it move Step 4's key number**, field error at acceptable geometry?
2. **Is it needed to make a claim credible**, as an acceptance evaluator or frozen
   evidence?
3. **Is it needed for someone else** to reproduce a result or contribute?

Everything else is frozen (kept reachable in Git, no longer maintained) or dropped.
Freezing is reversible; deleting from Git history is never recommended.

## Keep

| Item | Why it passes the test |
| --- | --- |
| Penalized stage-2 coil fitting from the exploration sessions | The only method that has moved the key number (0.27 → 0.152 checked) |
| One trusted fine-grid field evaluator plus the continuous geometry checker | Required before anything can be called accepted |
| Steps 1–3 results as tagged, frozen baselines, with their English step pages | Complete and credible; they need no further maintenance |
| Public starter (574 lines), contribution rules and the 47 public tests | Small, working entry point for others |
| "What this does not show", retained failures, no silent threshold changes | Cheap habits that make every claim credible |
| One page each: README, roadmap, status, step results; the docs size check | Short, enforced and sufficient |

## Freeze with a Git tag

Freeze these as a tagged archive (for example `archive-2026-09-27`) and remove them
from the default test run and from maintenance:

| Item | Size today | Why freeze |
| --- | --- | --- |
| Certified-step search family: controller, runner, journal, cell, plumbing, launcher, fine pipeline, fixed probes, residual tools | 3,783 tests; 8,900 library lines; 7,800 script lines | Its question is answered for now. Reuse only the pieces the acceptance checker needs, such as the continuous curvature and clearance bounds |
| LPQA optimization history before 13 September (Gauss–Newton, SLSQP, augmented Lagrangian, spatial/batched Jacobians and similar) | 71 scripts, 14,700 lines; about 400 tests | Closed studies; results are recorded |
| Coupled-coil pilot and the perturbation-matrix study code | About 580 tests (216 + 360) | Closed; their lessons are on the Step 4 page. Keep the clear-coil geometry checker (465 tests), which acceptance needs |
| Engineering mesh/FEM, SQuID-C intake schemas and CLI, the one-profile research CLI | About 150 tests plus optional dependencies | Not on the path to MS0; revisit once a coil set is within 10× of the limit |
| 149 historical protocol/results reports, mostly German | About 88,000 words | Keep the files in place, because 167 evidence files cite their paths. Collapse each folder index to one "frozen archive" pointer and stop maintaining them |

Two mechanics are possible:

- **Simplest:** tag, then remove the frozen code and tests from the main branch.
  Evidence paths resolve at the tag.
- **Safer:** keep the files, but mark them archived and exclude them from default
  test collection and indexing rules.

Either way, the default test run shrinks to active code and should take seconds,
not minutes.

## Drop

### Methods unlikely to pay off

1. **Certified small steps as the main search method.** They gained about 0.5% per
   round against a gap of about 2,700× the limit, and the residual diagnosis shows
   why. Keep certification for checking results, not for steering every step.
2. **Current-only freedom at fixed geometry.** Raw current fits worsened the
   normalized error; normalized current fits gained little and weakened the field.
   This is not a route to a tenfold improvement.
3. **Self-imposed limits inside exploration.** A ±0.02 m coefficient box blocked
   descent (up to 131 of 198 coefficients sat at the bound), and 240-bundle caps
   ended the full searches early. Standard stage-2 fits run far longer, and a
   longer run costs minutes. Keep only a wall-clock cap.
4. **Reopening settled questions.** Raw versus normalized objective is answered:
   use the normalized objective with geometry penalties.

### Ways of working with poor return

5. **A separately written checker for every tool.** Independent checking pays off
   for the acceptance evaluator, not for journals, launchers or runners.
6. **Full regression after every step.** Run the active subset per step, and the
   full suite before a claim or a release.
7. **Provenance prose in exploration notes.** An exploration record should be the
   script, its inputs, its JSON output and a note of at most one page. Hashes and
   independent audits are for claims.
8. **The byte-freeze of the historical tree.** Today it needs hash-pair exceptions
   (`operational_preservation`) before an old file may change. Once an archive tag
   exists, Git already guarantees immutability.
9. **Several AI agents writing to one branch at once.** This caused real
   collisions during the last reviews. Use one writer at a time, or one branch per
   agent.
10. **Building bespoke benchmark infrastructure first.** For MS0, first check
    whether the Goodman QI case and our coil sets can be contributed to an existing
    benchmark (for example StellCoilBench) and evaluated with community tools.
    Build only what is missing.
11. **Detailed planning for distant work.** Park Step 4C/4D, SQuID-C and the MS1
    evidence framework details until Step 4A has a coil set within 10× of the limit;
    keep one line each on the roadmap.
12. **Minor:** the public CI matrix runs nine jobs (three systems × three Python
    versions). Three systems with the oldest and newest Python would do.

## A simpler front door

- **The README tries to do too much.** At its word limit it explains goal, glossary,
  plan, quickstart, exercise, contribution, evidence reading, map and licensing.
  Keep: what and why, the current best number, the three commands, how to
  contribute. Move the glossary and "how to read our evidence" to the docs overview.
- **Too many milestone tiers.** Keep the roadmap table, but shorten its goal column
  to one line per row. Describe 4A–4D only on the Step 4 page.

## A lean plan for the next four weeks

1. **Freeze** the items above with one tag and one commit. About a day.
2. **Map the trade-off with the working method**, in the remaining exploration
   sessions:
   - penalized normalized-objective fits for both coil classes;
   - longer runs and wider coefficient ranges;
   - more coils per period as a separately labelled family.

   Report field error against clearance and curvature as one table.
3. **Check** the best two or three candidates once with the trusted fine evaluator
   and continuous geometry.
4. **Decide on 24 October:** below 1e-2 means continue locally; otherwise change the
   coil family or target.
5. **Launch** with the starter plus the best checked coil set as the first public
   challenge seed.

## What this review does not claim

Family sizes come from grouping files by name and are approximate. Freezing does not
mean the frozen work was wasted; it produced the answers that make this
simplification possible. Whether more coils, other targets or other clearance rules
are sensible is a physics judgment that a domain expert should confirm. This review
does not argue against rigor; it argues for **spending rigor on claims, and speed on
exploration**. It complements the [strategic review](STRATEGIC_REVIEW.md), whose
calibration and exploration priorities still stand.
