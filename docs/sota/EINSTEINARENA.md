# EinsteinArena: lessons for this project

Desk review, 11 October 2026, of
[Bianchi, Kwon, Pappu and Zou, "Harnessing the Collective Intelligence of AI Agents in the Wild"](https://arxiv.org/abs/2606.10402).
[Folder index](README.md) · [Related projects](RELATED_PROJECTS.md)

**Summary:** EinsteinArena shows that anyone's AI agents can jointly produce new
research results when every problem has a public, exact verifier. Its design
choices transfer to us, but only after our decisive checks are portable; a
leaderboard on our current public metric would reward the wrong thing.

## How it works

- **Problems:** a natural-language description, a JSON solution schema, a scoring
  direction and a verifier. Fifteen problems as of May 2026, chosen for cheap,
  objective evaluation and established research interest (kissing numbers,
  packings, autocorrelation inequalities).
- **Agents:** register through an API after a small proof-of-work; the humans
  operating them stay anonymous. Agents list problems, download specifications and
  verifiers, submit and poll results. Submissions run in isolated sandboxes.
- **Verifiers:** public and runnable locally, manually audited and hardened when
  agents expose edge cases. The kissing-number verifier had to move to 80-digit
  arithmetic because double precision was not enough.
- **Leaderboard:** one entry per agent (its best); a new top score must beat the
  record by a problem-specific minimum improvement, so floating-point noise cannot
  take first place; all personal bests are kept as history.
- **Discussion:** one board per problem, automatically moderated. The authors
  stress that the board stores "the path to the frontier", which a leaderboard
  cannot.
- **Results:** launched 19 March 2026; by May 2026, 11 to 12 new state-of-the-art
  results, including the kissing number in dimension 11 from 593 to 604. That
  record came from a chain of submissions, public discussion, a verifier fix and
  agents reusing each other's ideas, not from one agent.

## Lessons

1. **The verifier comes first.** Agent contributions add up when anyone can check
   a claim cheaply and identically. Our public starter already has a schema and a
   hash-bound evaluator, but the decisive research checks (dense fields, geometry,
   realized-field benefit) still need the native environment. Making them portable
   (MS0) is the precondition for any open competition.
2. **Agents optimize against the scorer.** EinsteinArena keeps hardening its
   verifiers. We have seen the same: a sparse public score can improve while the
   dense boundary worsens ([#8](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/8),
   [ranking counterexample](../../submissions/millimetre-ranking-counterexample/README.md)).
   A leaderboard must use the dense, feasibility-gated metric, not the sparse one.
3. **Require a minimum improvement for a new record** and show one best entry per
   contributor; keep every attempt as history. This matches our "retain failures"
   rule and avoids noise-level record chasing.
4. **Record the path, not only the frontier.** Ask contributors to post methods
   and failed attempts with explanations (issues or a discussion per task); a
   thread of unexplained failures is noise.
5. **Leaderboards create short-horizon incentives.** The authors note that agents
   chase scores instead of slower, promising directions. Our preregistered
   decisions and the Step 4 programme are the counterweight; any leaderboard
   should serve a stated research question, not replace it.
6. **Low-cost openness:** anonymous operators, proof-of-work against spam, sandboxed
   evaluation. We rely on GitHub accounts, hosted CI and maintainer review, which
   serve the same purpose.

## What does not transfer directly

Their verifiers are exact and take seconds. Ours are physics checks that take
minutes to hours, depend on numerical resolution and, for the questions that
matter (realized-field benefit), are not yet a single scalar. The
[CoilStellaration calibration](CONSTELLARATION.md#calibration-of-our-boundary-limit)
also shows that our boundary limit is not a reachable target in its current form.

## Possible next step (not started)

Design the MS0 challenge from both models: a frozen, versioned evaluator; a JSON
candidate schema; one feasibility-gated score on the dense boundary, interior and
geometry checks; a minimum improvement for records; public results with history;
and one discussion thread per task.
