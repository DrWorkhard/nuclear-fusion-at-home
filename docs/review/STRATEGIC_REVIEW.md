# Strategic review: work, results and structure

26 September 2026. Requested by the maintainer as a high-level, consultant-style
assessment. Reviewer: Claude (an AI coding agent); an internal review, not
external or domain-expert peer review. Reviewed state: commit `0da6a35`. No code,
data or evidence was changed and no calculation was run for this review.
[Review index](README.md) · [Status](../STATUS.md) · [Roadmap](../PROJECT_PLAN.md) · [Step results](../steps/README.md)

## Executive summary

**In four weeks, the project has built an unusually rigorous research machine,
but it is tuned for proving things rather than finding things.** The science is
stuck at the step that matters most, and the process is growing much faster than
the results. To move towards its goals, the project needs to learn quickly whether
its coil targets are reachable at all, and to make its bottleneck open to others.

1. **Rigor is the standout asset.** Every study is preregistered, construction is
   kept separate from acceptance, evidence is hash-bound and immutable, and
   failures stay on record. Few early-stage projects could withstand expert
   scrutiny this well.
2. **The key result is stalled.** After 12 days on Step 4, the best coil field
   error is about 0.27 against a limit of 0.0001, a factor of about 2,700. The
   latest searches improved it by 0.45–0.49% (coarse) and 0.06% (fine). At that
   rate, local search cannot plausibly close the gap.
3. **Nobody knows whether the targets are reachable.** Every coil design evaluated
   so far fails, including five archived StellCoilBench benchmark solutions tested
   against our own flux gate. The Step 4 limits were set as "new pilot conditions, not
   universal standards", and no known-good design has been run through them.
4. **Process volume outpaces results.** The full test suite grew from 720 to 5,654
   tests (about 8×) in 13 days, while the key Step 4 metric moved by less than 1%.
   Half of the 16 Step 4 result entries are software qualifications.
5. **Outsiders cannot reach the problem.** The public starter works well, but it
   cannot evaluate the thing that blocks progress (full-grid field quality within
   certified coil geometry). The ambition (MS1, MSX) is far ahead of the current
   means and has no intermediate milestone that creates value for others.

**Top three recommendations:** (1) calibrate the Step 4 gates with a known-good
design and run a time-boxed exploratory study of what field error is achievable
within the geometry limits; (2) introduce a fast exploratory lane next to the
confirmatory one; (3) launch publicly with a contributable "Step 4 coil challenge"
and a concrete six-month objective.

## Scorecard

Ratings are qualitative (1 = weak, 5 = excellent) and meant to direct attention.

| Axis | Rating | Verdict |
| --- | :---: | --- |
| Strategy and ambition fit | 2 | A compelling north star, but no credible path or intermediate milestones matching one maintainer, AI agents and a laptop |
| Scientific results | 2 | Solid capability steps and one modest proxy gain; the decisive coil step is stalled at about 2,700× its limit |
| Rigor and credibility | 5 | Exceptional discipline and honesty; "independent" still means the same machine and the same maintainer |
| Execution: speed, focus and cost of rigor | 2 | Very high output, low scientific throughput; confirmatory rigor applied even to exploration and infrastructure |
| Structure: repository and documentation | 3 | Entry layer much improved; detail layer heavy, mostly German, and overview pages drift back into changelogs |
| Collaboration readiness | 3 | Working starter and fair rules, but not hosted yet, and the starter cannot reach the bottleneck |
| Reproducibility and evidence portability | 3 | Hash-bound and honest; full reproduction needs one laptop's native environment and 4.8 GB of local artifacts |
| Operating model and risk | 2 | AI agents give throughput but add concurrency, volume and independence risks; single key person |

## The work in numbers

| Measure | Value |
| --- | --- |
| Duration and commits | 28 days (30 Aug – 26 Sep), 337 commits; 34 on 26 September alone |
| Code | About 105,000 lines of Python: 22,000 library, 42,000 scripts, 41,000 tests; public starter 574 lines |
| Full test suite | 720 tests (13 Sep) → 2,064 (23 Sep) → 5,654 (26 Sep) |
| Documentation | 207 Markdown files, about 180,000 words; 78 protocols and 70 results reports |
| Research log | 105 findings, 27 decisions, 287 validation-log entries (about 39,000 words) |
| Evidence | 274 MB in Git; 4.8 GB of local, untracked artifacts |
| Step timeline | Steps 1–2 accepted 13 Sep; Step 3 14 Sep; Step 4 open since 14 Sep; public layer 23–26 Sep |

## Findings by axis

### 1. Strategy and ambition fit — 2/5

- **The goal is inspiring but distant.** MSX ("the best reactor design current
  technology can achieve") and MS1 ("better than the design Proxima Fusion is
  pursuing") require finite-pressure equilibria, stability, transport and
  engineering models. None of these is qualified here yet. Proxima and academic
  groups pursue this with full physics toolchains and expert teams.
- **The middle of the ladder is missing.** Between "our tools work" (Steps 1–2)
  and "we beat Proxima" (MS1) there is no milestone that would be useful to anyone
  outside the project within three to six months.
- **So what:** keep MSX and MS1 as the north star, but define a six-month objective
  that is both reachable and valuable to others. Candidates: an openly verified
  quasi-isodynamic coil benchmark with certified geometry; independent,
  reproducible verification of published designs; or one open coil set that
  passes calibrated gates.

### 2. Scientific results — 2/5

- **Steps 1–2 are table stakes.** They show that the tools work and that iteration
  is reproducible. That is necessary, but not a result anyone outside would cite.
- **Step 3 is real but modest.** An 11.17% reduction of a proxy metric
  (bounce-action variance) comes from boundary changes of at most 0.1 mm on a
  configuration with about 1 m major and about 0.2 m minor radius. It was not a
  blind test, and all checks ran on the same machine.
- **Step 4 is stalled, and the stall is informative.**
  - The coil sets have certified geometry, but their field is about 2,700× off.
  - The eight native protected searches stopped at the curvature certificate after
    0.45–0.49% improvement. Fine validation keeps all eight rejected (normal-field
    RMS 0.268–0.275 against 0.0001).
  - Two newly certified proposals gain 0.057% and 0.065%.
  - Illustration only: at about 0.5% per round, a 2,700-fold reduction would take
    around 1,600–1,800 rounds. Local continuation is not a path to the target.
- **The coil mismatch dwarfs the plasma improvement.** With the same starting
  coils, the Step 3 plasma and the reference differ only in the fourth digit of the
  field error (0.27611 vs 0.27605 with six base coils; 0.26921 vs 0.26915 with
  eight), about 0.02%. Checking whether the Step 3 benefit survives in a
  coil-produced field needs far more accurate coils first.
- **The gates have no positive control.** Every design evaluated so far fails:
  - our own coil candidates, at every step;
  - five archived StellCoilBench benchmark solutions, rejected by our flux gate
    (about 1e-6 against 1e-8).

  The Step 4 protocol itself calls its limits "newly set pilot conditions, not
  universal standards". Without a known-good design passing them, "very hard"
  cannot be told apart from "unreachable with this setup".
- **The negative results are genuine learning.** Examples: fine sampling revealed
  only 1.8–6.7 mm plasma clearance where coarse sampling showed 35–52 mm; and
  curvature certification is now identified as the binding constraint. They are
  documented honestly.
- **So what:** calibrate the gates and map what is achievable before investing
  further in certified local search. The saved-field residual diagnosis registered
  on 26 September asks the right question; give it priority.

### 3. Rigor and credibility — 5/5

- **Strength.** Preregistered protocols, separate construction and acceptance,
  immutable hash-bound evidence, retained failures and an explicit "what this does
  not show" in every result. This will be a genuine asset in front of experts,
  and for MS1.
- **Caveat.** "Independent" checks are separate implementations on the same
  machine, written by the same maintainer's AI agents. There has been no external
  expert review and no second family of physics codes. The same heavy rigor is also
  applied to infrastructure, for example a crash-safe event journal with 47 tests.
- **So what:** keep full rigor for claims, and spend it deliberately. Add one
  external expert touchpoint for the Step 3 metric and the Step 4 gates.

### 4. Execution: speed, focus and cost of rigor — 2/5

- **Output is very high; scientific throughput is low.** The test suite grew about
  8× in 13 days while the key metric moved by less than 1%. Each question runs the
  full chain: protocol, implementation, synthetic tests, review, full regression,
  checkpoint, run, audit, documentation. A single 168-request field comparison
  took one protocol and about five commits.
- **The factory is being built before the product is known.** Every step of the
  search is certified (radii of 0.01–1 mm) before anyone knows whether any coil set
  within the geometry limits can approach the field target.
- **So what:** run two lanes.
  - An *exploratory lane*: fast, clearly labelled, no preregistration, and no
    claims. Its purpose is to learn what is achievable.
  - A *confirmatory lane*: today's full rigor, used only when something is claimed.

  Add time-boxes and decision rules, for example "if the exploratory field error is
  not below 1e-2 by a set date, change the coil topology or targets".

### 5. Structure: repository and documentation — 3/5

- **The entry layer is much improved.** There is one home per topic, English step
  pages, a lean roadmap and a review folder.
- **Entropy returns quickly under agent-speed writing.**
  - The status table grew from 6 to 16 rows since 25 September, mostly tool
    qualifications.
  - The roadmap grew from 451 to 613 words, and its next actions again list test
    counts and commit hashes.
  - The Step 4 page reached about 1,900 words and 16 entries.
  - The one-home rule exists only as text, so nothing enforces it.
- **The detail layer is hard to use.** It holds about 180,000 words, mostly German,
  with dense jargon, and a validation log of 287 entries. The public starter (574
  lines) sits next to 100,000 lines of research code and 190 scripts, so newcomers
  cannot tell what matters.
- **So what:**
  - Give editorial ownership of the overview pages to one role.
  - Keep scientific results only in the status page; tool qualifications belong on
    the step page or in the detail folders.
  - Set word or row budgets that a docs check enforces.
  - Write new documents in English only.
  - Add a short repository map.

### 6. Collaboration readiness — 3/5

- **Strengths:**
  - a portable starter verified on three Python versions;
  - fair rules that accept unsolicited work without requiring a compute-cost
    disclosure;
  - safe handling of untrusted contributions;
  - clear onboarding.
- **Gaps:**
  - The project is not hosted yet: no URL, no verified CI, no discussion channel.
  - There are no external contributors so far.
  - The starter works with fixed currents and sparse samples and has no geometry
    or full-grid checks, so contributors cannot work on the problem that blocks
    Step 4.
  - The name "@ Home" suggests volunteer computing, which this is not.
  - Nothing explains why someone should contribute here rather than to SIMSOPT or
    StellCoilBench.
- **So what:**
  - Launch soon; done beats perfect.
  - Build a portable "Step 4 coil challenge": a full-grid field check plus
    continuous geometry checks for the reference coil set, with a public
    leaderboard.
  - Seed three to five well-scoped starter issues.
  - State the contributor value proposition in one paragraph.

### 7. Reproducibility and evidence portability — 3/5

- **Strength.** Evidence is hash-bound, and the public starter reproduces anywhere.
- **Gap.** Reproducing Steps 1–4 needs the maintainer's native environment and
  4.8 GB of untracked local artifacts; much of the committed evidence points to
  files outsiders cannot obtain. It is not documented whether these artifacts are
  backed up. About 365 tracked files contain the maintainer's home-directory paths.
- **So what:** archive each major result's artifacts with a DOI (for example on
  Zenodo), build portable packages for the Step 3 and Step 4 reference data, and
  set up a backup routine.

### 8. Operating model and risk — 2/5

- **AI agents bring throughput and new risks.**
  - This week, two agents (Claude Code and Codex) edited the same overview and log
    files at the same time; commits had to be split by hand.
  - Agents write a lot and densely, which drives documentation volume and jargon.
  - Agents reviewing agents weakens the meaning of "independent".
- **Key-person risk.** Decisions, compute and the only full artifact copy sit with
  one person.
- **Resources.** Free disk has improved (about 49 GB now, versus about 4 GB earlier
  this week). Native runs are single-threaded with 30-minute caps, which limits
  exploration.
- **Reputation.** Naming Proxima Fusion publicly as the MS1 comparison is honest
  and well caveated, but it invites scrutiny. Outreach should wait for strong
  evidence, as the MS1 framework already requires.
- **So what:** give each agent one area to write, or its own branch that is merged
  deliberately; add an editorial pass for anything public; and set up an artifact
  backup.

## Recommendations

| # | Recommendation | Why | When |
| --- | --- | --- | --- |
| 1 | **Calibrate the Step 4 gates with positive controls**: run published or benchmark coil sets for a comparable configuration through the same gates, in a preregistered study. If none pass, version the gates with a documented rationale, never retroactively. | Tells "hard" apart from "unreachable" | Now (1–2 weeks) |
| 2 | **Map what is achievable, time-boxed**: an exploratory stage-2 coil optimization that traces the trade-off between field error and clearance/curvature, with a decision rule for continuing the protected search. | Avoids investing in certified search of a region that cannot reach the target | Now |
| 3 | **Finish the registered residual diagnosis** and let it, together with 1 and 2, choose the next Step 4 method. | Already the right question | Now |
| 4 | **Launch**: decide on history and privacy, host the repository, verify CI, open a discussion channel. | External value starts at launch | Now |
| 5 | **Two-lane governance** (exploratory and confirmatory) with time-boxes and decision rules. | Restores learning speed without losing credibility | Next 30 days |
| 6 | **Documentation guardrails**: scientific results only on the status page, word/row budgets enforced by the docs check, English-only new documents, a repository map. | Stops overview pages from drifting back into changelogs | Next 30 days |
| 7 | **A contributable bottleneck**: a portable Step 4 coil challenge with full-grid field and geometry checks and a leaderboard. | Lets outsiders work on what blocks progress | Next 30 days |
| 8 | **Agent operating rules**: one writer per area or one branch per agent; an editorial pass before publishing. | Prevents collisions and volume creep | Next 30 days |
| 9 | **External expert review** of the Step 3 metric and the Step 4 gates; cross-check with a second physics code where feasible. | Makes "independent" mean independent | This quarter |
| 10 | **Archive and back up the evidence**: DOIs for major results, portable data packages. | Reproducibility beyond one laptop | This quarter |
| 11 | **A six-month objective and milestone ladder towards MS1**, with dates and KPIs. | Connects the north star to near-term work | This quarter |

## Indicators to track

- Best fine normal-field RMS for a geometry-certified coil set (now about 0.27;
  limit 0.0001), and the achievable trade-off with clearance and curvature.
- Number of known-good reference designs that pass our gates (now none tested
  for Step 4).
- Cycle time from question to answer, and the share of effort spent on science
  versus infrastructure.
- Size of the overview pages (words, status-table rows).
- External contributors, external reproductions and expert reviews (all zero today).

## Basis and limits of this review

A read-only reading of the repository at `0da6a35`: the overview and step pages,
the key protocols and results (most of them German), Git history and file counts.
All numbers come from those sources; the 1,600–1,800 rounds figure is an
illustrative extrapolation, not a forecast. The scientific judgments are an AI
reviewer's, and a domain expert should check them, especially on gate calibration
and on the significance of the Step 3 metric. The ratings are qualitative.
