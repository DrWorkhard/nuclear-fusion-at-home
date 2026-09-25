# Nuclear Fusion @ Home

Open stellarator research — contributed by people and their agents.

Our end goal is to **contribute to nuclear fusion by finding the
best reactor design current technology can achieve**. We work on stellarators:
fusion devices whose shaped external coils create a twisted magnetic field to
confine hot plasma. This is computational research, not a home reactor-building project.

By “best” we mean a design that balances performance, buildability, robustness,
safety and practical cost — not just the top score on one metric. We want
improvements that others can reproduce and challenge.

**Research preview · 25 September 2026.** Our tools reproduce selected open
references. One plasma-target study improved its preregistered metric
(bounce-action variance, a particle-motion diagnostic) by **11.17%**.
Our current starting coil sets have a full-grid normal field error of
**about 0.27; the acceptance limit is 1e-4**. A feasible new coil design and
a state-of-the-art advance remain ahead of us. We are independent of, and not
endorsed by, Proxima Fusion or the Max Planck Institute.

## A few terms

- **Reference (seed):** the saved starting design used for comparison.
- **RMS:** root-mean-square error; a measure of typical mismatch.
- **Filament:** a coil model represented by a thin current-carrying curve.
- **Native research tools:** the larger workflow with compiled scientific libraries;
  the public starter below uses only Python's standard library.
- **Full-grid / flux-normalized:** the research calculation uses dense spatial
  grids and adjusts current to match a specified magnetic flux. The starter uses
  sparse samples and holds current fixed; these are different checks.

## Project plan and progress

We move from reproducible calculations to improved plasma and coil designs, then
to fair comparisons and expert scrutiny. “Complete” means the stated scope passed
on the maintainer's machine, not that a reactor or universal toolchain is complete.
[Scientific overview](docs/README.md) · [Detailed roadmap](docs/PROJECT_PLAN.md)

| Step / milestone                                     | Goal                                                                                                                                                       | Status                               |
| ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| **1. Establish a reliable foundation**               | Reproduce selected checks for W7-X (the Wendelstein 7-X experiment), Goodman et al.'s open quasi-isodynamic (QI) dataset, and reference coil calculations. | **Complete (local reference tools)** |
| **2. Make design iteration reproducible**            | Change a design, save it, evaluate it separately and repeat.                                                                                               | **Complete (iteration workflow)**    |
| **3. Improve our own plasma target**                 | Reduce the preregistered particle-motion diagnostic by changing the vacuum plasma target.                                                                  | **Complete (vacuum study)**          |
| **4. Develop plasma and coils together**             | Find coils that realize the plasma benefit, then demonstrate coupled improvement, pressure/confinement validity and finite-coil robustness.                | **In progress**                      |
| **5. Demonstrate a meaningful design advantage**     | Compare feasible designs fairly with leading references and independently verify the benefit.                                                              | **Not achieved**                     |
| **MS1. Contact Proxima Fusion with strong evidence** | Contact Proxima as soon as strong, reproducible, independently checked evidence shows our design is better than the design they are pursuing.              | **Not reached**                      |
| **MSX. Our end goal**                                | Contribute to nuclear fusion for humanity by finding the best reactor design current technology can achieve.                                               | **Long-term goal**                   |

MS1 requires a relevant, versioned Proxima reference, matched conditions and
explicit uncertainty and trade-offs. Improving our reference or a sparse score
alone cannot establish that advantage. [MS1 evidence framework](docs/squid_c/MS1_PROXIMA_COMPARISON.md).
MSX names our final milestone: expert scrutiny and practical follow-on work extend
beyond MS1; “best” is an ambition, not a proven global optimum.

## Start in three commands

First get a checkout or source ZIP and open its directory. On a hosted repository,
use its **Code → HTTPS** clone URL or **Download ZIP**. Replace the placeholder
below with that actual URL before running it; if hosting is unavailable, obtain
a checkout/source ZIP from the maintainer:

```bash
git clone <repository-url> fusion
cd fusion
```

With **Python 3.11+**, run:

```bash
python fusion.py public cases
python fusion.py public demo --output results/my-first-demo
python scripts/test_public.py
```

Check `python --version`. On macOS/Linux, `python3` is also fine **if it is 3.11
or newer**; some system Pythons are older. On Windows, try `py -3` and check its
version, or select an installed supported version, such as `py -3.12`.
The public starter needs **no package installation, API key, GPU, compiler or
additional download** after obtaining the repository. The native research workflow
requires Python 3.12+ and additional dependencies.

Expected: the demo prints `"reference_reproduced": true` and
`"physical_admission": false`; the test run ends in `OK`. A demo/evaluation
takes a few seconds on the review Mac; timing varies by machine. The demo
compares the unchanged reference with saved native fields and replays its report.
Use a fresh output name on each run.
[Full quickstart](docs/validation/PUBLIC_QUICKSTART.md) ·
[Data and attribution](examples/clear-coil-samples-v1/README.md)

## What should I try?

The starter lets you explore **Step 4's current bottleneck: coil shapes whose
field matches the target**. Try a small coefficient change, initially around
0.01–0.1 mm (`1e-5`–`1e-4` metres), and compare both errors. That is a starting
scale for exploration, not a guarantee of improvement or safe geometry.

| Public metric (dimensionless; lower is better)                     | Reference score |
| ------------------------------------------------------------------ | --------------- |
| `sampled_normal_rms` — field leaking across the target boundary    | **0.304207**    |
| `sampled_inner_vector_rms` — mismatch with the target field inside | **0.380435**    |

`demo` and `evaluate` compare reference and candidate at the same 512-node coil
resolution and print signed/percentage changes. An unchanged reference gives zero
change; negative is better. Report both metrics and any trade-off. Tiny changes
still need resolution and wider-sample checks, not just more printed digits.

The same reference coils score about **0.27 in the full research check** and
**0.304 on the public samples**. The research limits, **1e-4 normal RMS and
0.01 inner-vector RMS**, apply to the different full-grid, flux-normalized workflow.
The sparse scores are feedback, not that acceptance test.
[Score interpretation](docs/validation/PUBLIC_QUICKSTART.md#what-the-report-means).

This example changes `coil[0]/xc(0)` from about 0.960819 m by +0.1 mm.
It demonstrates editing, not a known improvement:

```bash
python fusion.py public init --output results/my-reference.json
python fusion.py public set-coefficient --candidate results/my-reference.json --name "coil[0]/xc(0)" --value 0.9609191138350243 --output submissions/my-coil-study/candidate.json
python fusion.py public evaluate --candidate submissions/my-coil-study/candidate.json --output results/my-report.json
python fusion.py public audit --report results/my-report.json --output results/my-audit.json
```

`--value` is **absolute, in metres**, not a delta. Double-quote the name for
bash, zsh, Windows cmd.exe and PowerShell. See
`python fusion.py public set-coefficient --help`. The last command is optional
but recommended: `audit` recomputes the report with the same evaluator and checks
agreement within its numerical tolerance. Include that outcome in your PR;
it is not independent physical validation.

For direct array edits, the name-to-index mapping and a callable Python search-loop
example are in the [quickstart](docs/validation/PUBLIC_QUICKSTART.md#evaluate-your-own-candidate).
An evaluation takes a few seconds; budget longer loops accordingly.

## Contribute something useful

**Exploratory PRs with lower sampled scores are welcome.** Commit the small
`submissions/my-coil-study/candidate.json` (about 10 KB) and a brief
`README.md` beside it with the reference revision, commands, both scores,
checks and limitations. Keep generated reports/audits in ignored `results/`;
do not force-add the much larger report. [Submission layout](submissions/README.md).

Counterexamples, negative results, better tests and alternative approaches are
equally useful. Bring an agent or write code yourself. **No listed issue, prior
permission, particular model or compute-budget disclosure is required.**
[Research hints](docs/optimization/RESEARCH_HINTS.md) are invitations, not an allowlist;
work beyond the starter's fixed-current format is welcome.

[Contribution guide](CONTRIBUTING.md) · [Review policy](docs/validation/REVIEW_POLICY.md) ·
[Agent guide](AGENTS.md) · [Security](SECURITY.md)

## How to read our evidence

Reports call physical acceptance **admission** (`physical_admission`): all checks
specified by that evaluation profile must pass. Public reports keep this false
because they test only sparse fields, not the full physics and engineering.
The plasma study's bounce-action improvement is not measured confinement or power.

Recorded public checks pass locally on macOS with Python **3.11, 3.12 and 3.14**.
These are not Windows/Linux or hosted-CI results; see the
[verification record](docs/validation/PUBLIC_RELEASE_RESULTS.md) and
[current status](docs/STATUS.md) for dated coverage and retained failures.
[Historical research entry points](docs/validation/PROJECT_ENTRYPOINTS.md) describe
the larger native workflow.

## Repository map

- `src/fusion_public/`: dependency-free starter and candidate helpers.
- `src/fusion_baselines/`: historical and ongoing research code.
- `examples/`: attributed reference data; `submissions/`: small contributed candidates.
- `docs/`: project status, methods, results and reviews.
- `evidence/`: recorded research evidence; large local runs stay outside Git.

## Licensing and project operation

Project code: [MIT](LICENSE), with [source/data notices](NOTICE.md).
Bundled derived Goodman data has [CC BY 4.0 attribution](examples/clear-coil-samples-v1/README.md).
Credit exact revisions and upstream sources: [CITATION.cff](CITATION.cff).

Publication and any PR automation require the
[launch and operating checklist](docs/validation/REVIEW_POLICY.md#launch-checklist--requires-actual-hosting-work).
The [review policy](docs/validation/REVIEW_POLICY.md) separates accepting a useful
contribution from accepting its scientific claims.
