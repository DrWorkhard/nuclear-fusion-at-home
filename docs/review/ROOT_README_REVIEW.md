# Root README review

24 September 2026. Requested by the maintainer after the first release review had
been addressed. Reviewer: Claude (an AI coding agent), not an external expert.
This review changed no code, data, evidence or other documents. **All 27
recommendations below are open.**

[Review index](README.md) · [Overview](../README.md) · [Status](../STATUS.md) · [Roadmap](../PROJECT_PLAN.md)

## Reviewed version and questions

- `README.md` working copy, Git blob `bae5c814cfbc0704bd1af4bb6947965c1c580642`
  (136 lines, about 1,000 words). This is commit `7a0b2ed` plus the maintainer's
  uncommitted edits: aligned tables, `_…_` emphasis and the new sentence
  “The end reactor shall balance…” on line 10. **Line numbers below refer to
  this version.**
- Program behaviour was checked with the code at commit `7a0b2ed`.

Questions: Is the README now more understandable? Is it consistent with the other
entry documents and with what the commands actually do?

## Verdict

**Much more understandable than at the first release review, and consistent where
it matters most.** Every README command works as described. The printed numbers
match the README. All links resolve. Step and milestone names and statuses are
identical across the four overview documents.

Remaining issues are mainly: statements that become false on launch day, terms
used before they are explained, and gaps in the candidate workflow. A newcomer can
run the starter, but may not know which file to change, what a sensible change
is, or where to put the result in a pull request.

Since the first review, these points were resolved: English folder indexes,
an early Python-version check, reference scores with “lower is better”, editing
coefficients by name, a short glossary, a contributor-safe `AGENTS.md`, a
lightweight core CI and one consistent roadmap.

## Checks actually performed

All on macOS 15 (Darwin 24.6.0, arm64), 24 September 2026.

| Check | Observed result |
| --- | --- |
| README commands, verbatim, in a fresh clone of `7a0b2ed` with the reviewed README, CPython 3.12.13 | `public cases`, `public demo`, `scripts/test_public.py`, `public init`, `public evaluate`, `public audit` and `public set-coefficient --help` all succeed; demo reports `reference_reproduced: true` in 2.3 s; 44 public tests pass in 0.50 s |
| Printed scores vs README table | Reference 0.3042070281 and 0.3804347184, matching the README's 0.304207 and 0.380435 |
| Candidate loop | Unknown coefficient name gives a clear error (exit 2); `coil[0]/xc(0)` 0.9608 → 0.97 m makes the two scores 0.44% and 0.26% worse; one evaluation takes 1.2 s; audit replay passes |
| Unchanged reference in `demo` | `sampled_inner_vector_rms` change is +5.6e-17, because the reference is scored at 256 nodes and the candidate at 512 |
| Older/other Python | macOS system Python 3.9.6: clear “requires Python 3.11+” message, exit 2. Python 3.11.4: demo reproduces the reference |
| Numbers in text | 11.17% and “about 0.27 against a 0.0001 limit” agree with [status](../STATUS.md) (0.269–0.276 vs 1e-4) |
| Links | All 21 local links and 3 section anchors resolve; `scripts/check_docs.py` passes |
| Cross-document consistency | Step/MS1/MSX names and statuses identical in README, [overview](../README.md), [roadmap](../PROJECT_PLAN.md) and [status](../STATUS.md); “Python 3.11+” consistent in README, CONTRIBUTING, quickstart and launcher |
| Committing a result | `git add results/…` is refused because `results/` is ignored |

Not checked: Windows or Linux execution, hosted CI, how GitHub renders the page,
or comprehension tests with real outside readers.

## Recommendations

### A. Fix before launch

1. **Pre-launch statements become false on launch day.** “Public hosting is being
   prepared locally”, “Hosted CI … still outstanding” and “The publication
   inventory identifies historical machine paths requiring review” (lines 122,
   133–135) describe the private state. The last one tells public readers that
   unreviewed content is in the repository. Replace them at launch.
2. **No way to get the code.** “From a checkout or source ZIP” (line 44) needs a
   `git clone <url>` and `cd` line once the URL exists.
3. **No place for contributed files.** Line 76 asks PRs to “include the
   candidate”, but `results/` is ignored by Git. Say which file to commit (the
   ~10 KB candidate, not the 117 KB report) and in which folder.
4. **“No … download” (line 56) is inaccurate.** The clone itself is about 65 MB
   (about 380 MB unpacked). Say “no additional download”.

### B. Clarity

5. **Line 10, “The end reactor shall balance…”,** reads like a specification and
   suggests that the project will build a reactor, which conflicts with line 8.
   The edit also removed the only early explanation of “best”. Suggested wording:
   “By ‘best’ we mean a design that balances performance, buildability,
   robustness, safety and cost — not just the top score on one metric.”
6. **“MSX” in the first sentence (line 5) is not explained.** Readers will look
   for MS2, MS3 and so on. Drop it there, or say “MSX, our final milestone”.
7. **Terms are used before the glossary (line 109) explains them.** “Seed”
   (lines 37, 58) is never defined, while the glossary defines “baseline”, which
   the README does not use. “Native”, “filament”, “full-grid” and
   “flux-normalized” are also unexplained. Move the glossary up, or rename the
   entry to “Reference (seed)” and add the four missing terms.
8. **Unclear subject at lines 15–16.** “Turning targets into good coils: their
   full-grid normal field error…” Suggested: “Our current starting coil sets have
   a full-grid normal field error of about 0.27; the acceptance limit is 0.0001.”
9. **0.27 and 0.304 look contradictory.** The introduction gives 0.27 and the
   table gives 0.304 for a similar quantity. Add: “The same reference coils score
   about 0.27 in the full research check and 0.304 on the public samples.”
10. **“Improved its chosen metric” (line 14) sounds like cherry-picking.** The
    metric was fixed in advance; say “its preregistered metric (bounce-action
    variance)”.
11. **Lines 22–24 are a maintainer note.** “These names and statuses are shared
    with…” could become one sentence telling readers what the steps lead to.
12. **The plan table mixes content types.** The middle column holds a purpose
    (rows 1, 2, 5), a result (row 3) or progress plus next steps (row 4). Consider
    two columns, “Goal” and “Where we are”. The status qualifiers are also mixed:
    “(local reference tools)” vs “(vacuum study)”, and “local” will not mean “on
    the maintainer's machine” to outsiders.
13. **W7-X and Goodman (line 28) need a short explanation,** for example
    “the Wendelstein 7-X experiment” and “Goodman et al.'s open QI dataset”.
14. **The starter is not tied to the roadmap.** Suggested: “The starter lets you
    work on Step 4's current bottleneck: coil shapes whose field matches the target.”

### C. Ease of use

15. **The command block (lines 86–91) has no editing step.** It says “# Change
    coefficients” and then evaluates the same file name. Put `set-coefficient` in
    the block and evaluate the *new* file it writes. Line 93 shows only a partial
    command (`public set-coefficient --help`), and that help text neither shows the
    name format nor says the value is absolute, in metres.
16. **Quote names with double quotes.** The quickstart's `'coil[0]/xc(0)'` fails
    in Windows `cmd.exe`, and without quotes it fails in zsh. Double quotes work
    in bash, zsh, `cmd.exe` and PowerShell (known shell behaviour; Windows was
    not tested in this review).
17. **“Small change” has no scale (line 65).** The quickstart example moves a
    coefficient from 0.96 to 1.2 m; the reviewer's +9 mm change worsened the
    scores by 0.26–0.44%. Give a typical step size, the cost of one evaluation
    (about 1.2 s) and a pointer for running a search. Only the CLI is documented,
    not a Python function that can be called in a loop.
18. **“Very small changes can be numerical noise” (line 74) needs a number.** The
    unchanged demo itself shows +5.6e-17 because it compares 256-node reference
    scores with 512-node candidate scores. State a threshold, or compare both at
    512 nodes so the unchanged reference shows exactly zero.
19. **Show the expected output**, for example `reference_reproduced: true`, the
    test run ending in `OK`, and that the demo takes about 2 seconds.
20. **Python hints are narrower than the support (lines 52–54).** They name only
    `python3.11`/`python3.12` and `py -3.12`, although 3.11–3.14 work. Say
    “`python3` (3.11 or newer)” and `py -3`, and state that only macOS has been
    tested so far.
21. **Say what `audit` is for (line 90)**, for example “optional: confirms the
    report recomputes identically; include it in your PR”.

### D. Consistency and small fixes

22. The limit is written “0.0001” (line 16) and “1e-4” (line 80). Use one form.
23. “We are independent of Proxima Fusion…” (line 17) omits “not endorsed by”,
    which the other documents include.
24. “Physical acceptance (`physical_admission`)” (line 115) should note that the
    reports use the word “admission”.
25. The “documented local tests” link (line 121) points to a review-change record.
    Link a stable test/results page, or state “all public tests pass locally on
    Python 3.11–3.14”.
26. Outside the README, the command output still lacks spaces: “Python3.11+” in
    the `fusion.py` help and in `public cases`, and “64 boundary,64 inner”.
27. Optional: a five-line repository map (`src/fusion_public` = starter,
    `src/fusion_baselines` = research code, `examples/`, `docs/`, `evidence/`)
    would help people and agents find their way.

## Limits of this review

One AI reviewer on one macOS machine. Program behaviour was checked only for the
commands the README shows. Scientific claims were compared with the status page
and one final audit, not re-derived. Line numbers apply only to the reviewed blob.
