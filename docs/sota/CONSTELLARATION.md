# ConStellaration and CoilStellaration: lessons for this project

Desk review with one data comparison, 11 October 2026. [Folder index](README.md) ·
[Related projects](RELATED_PROJECTS.md)

**Main finding:** in Proxima Fusion's public coil benchmark, no quasi-isodynamic
(QI) case reaches our boundary limit of 1e-4, and our best coil fits are already
better than about 91–95% of its coil sets. The fixed-target "stall" is therefore
close to what a professional pipeline achieves, and our 1e-4 pilot limit appears
far beyond practical filament coils for such plasmas. This does not relax any
limit; see [calibration](#calibration-of-our-boundary-limit) for caveats.

## What they are

- **[ConStellaration](https://github.com/proximafusion/constellaration)** (Proxima
  Fusion and Hugging Face, July 2025; [paper](https://arxiv.org/abs/2506.19583)):
  about 182,000 QI-like plasma boundaries (158,000 evaluated without errors) with
  VMEC++ equilibria and three
  benchmarks (geometric; "simple-to-build" QI; multi-objective MHD-stable QI). A
  design that violates any constraint by more than a 1% relative tolerance scores
  zero; feasible designs get a normalized score, and the multi-objective problem
  is scored by hypervolume. The simple-to-build problem maximizes a coil-simplicity
  proxy, the normalized magnetic gradient scale length L∇B, under QI, mirror-ratio,
  elongation and aspect-ratio limits.
- **[CoilStellaration](https://github.com/proximafusion/coilstellaration)** (May 2026,
  MIT; [dataset](https://huggingface.co/datasets/proxima-fusion/coilstellaration)):
  a coil benchmark built on ConStellaration. A submission maps a plasma boundary
  plus four requirements (coil–coil distance, coil–plasma distance, curvature,
  field error) to a coil set. Reference coil sets come from REGCOIL warm starts
  refined with DESC; cases are split into "loose", "medium" and "tight" tiers by
  the field error that pipeline achieved, and scoring uses soft feasibility
  (exponential penalties per requirement, geometric mean across requirements).

## How the community responded

Public results on Hugging Face, read 11 October 2026:

| Problem | Submissions | Distinct users | Score above zero | Best score | Paper baseline |
| --- | ---: | ---: | ---: | ---: | ---: |
| Geometric | 69 | 39 | 47 | 0.9805 | 0.969 |
| Simple-to-build QI | 44 | 20 | 30 | 0.6577 | 0.431 |
| MHD-stable QI (hypervolume) | 51 | 6 | 51 | 239.4 | 130.0 |

An open benchmark with a frozen evaluator drew a few dozen participants over 15
months, steady rather than viral, and they clearly beat the paper's baselines on
the two harder problems.

## Calibration of our boundary limit

We downloaded only the 16 MB evaluation split of CoilStellaration (13,299 cases,
8,058 with DESC results; coils of Fourier order 7, 4–8 coils per half-period, one
to five field periods). Its DESC metric is |B·n|/|B| with the local field strength,
the same quantity as ours; it reports a mean, we report an area-weighted RMS. From
the saved fine-grid arrays of the [construction-margin probe](../optimization/ISSUE70_CONSTRUCTION_MARGINS.md)
we computed our plain mean (the recorded RMS was reproduced exactly):

| Statistic | Our control C | Our halved-margin M |
| --- | ---: | ---: |
| Area-weighted RMS (our metric) | 0.0018339 | 0.0017283 |
| Plain mean (their statistic) | 0.0015283 | 0.0014337 |
| Maximum | 0.008488 | 0.008063 |

| CoilStellaration cases | n | Mean better than C / M | Maximum better than ours |
| --- | ---: | ---: | ---: |
| All with DESC results | 8,058 | 8.9% / 7.5% | 4.4% |
| Two field periods | 1,345 | 6.4% / 5.4% | 2.2% |
| Two field periods, six coils per half-period | 282 | 5.3% / 3.2% | 1.8% |
| "Tight" tier | 2,701 | 26.7% / 22.3% | 13.3% |

No case reaches a mean of 1e-4 (best 2.6e-4); 2.5% reach 1e-3 and the median is
5.4e-3.

**Caveats:** different plasma boundaries (ConStellaration QI shapes versus the
Goodman reference401), different requirement values and normalizations, coil
order 7 versus our 5, pipeline budgets we do not know, and a plain mean over
their grid whose weighting we did not verify. The comparison is order of
magnitude, not a matched benchmark. Acceptance limits stay unchanged: changing
them after seeing outcomes is not allowed, and any revision needs a separately
reviewed, versioned acceptance definition.

## Lessons

1. **Freeze and version the evaluator.** The leaderboard is pinned to release
   v0.2.6; the README lists every score-changing difference, and submissions
   accidentally scored with v0.3.0 were re-evaluated. Our hash-bound public
   evaluator follows the same idea; a leaderboard would need an explicit version.
2. **One feasibility-gated score** is easier for outsiders than our two separate
   metrics; soft feasibility (CoilStellaration) gives partial credit near limits.
3. **Low-friction submission:** a small JSON file, a Docker or Gradio evaluator and
   a public results dataset with user, time and score.
4. **A cheap coil-difficulty proxy on the plasma side.** L∇B lets plasma
   optimization account for coils before any coil is fitted, a lightweight step
   toward the joint route ([#36](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/36)).
5. **Calibrate tiers against a reference pipeline.** CoilStellaration defines
   difficulty by what a strong pipeline achieved; our limits were set without such
   a reference.

## Possible next steps

- Rerun the comparison with our own checker on a small CoilStellaration sample
  (two field periods, six coils per half-period) to remove the statistic and
  normalization caveats, then propose a versioned acceptance definition for
  separate review.
- Done: [both targets scored with `constellaration==0.2.6`](../qi/CONSTELLARATION_METRICS.md).
  The Step 3 gain shows no measurable L∇B cost (−0.026%, rule band ±5%), which
  informs the joint pilot ([#59](https://github.com/DrWorkhard/nuclear-fusion-at-home/pull/59)).
- For MS0, consider aligning with CoilStellaration instead of building a new
  coil benchmark.
