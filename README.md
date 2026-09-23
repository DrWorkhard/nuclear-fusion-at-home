# Nuclear Fusion @ Home

Open stellarator research — contributed by people and their agents.

Our end goal (**MSX**) is to **contribute to nuclear fusion for humanity by finding
the best reactor design current technology can achieve**. We work on stellarators:
fusion devices whose shaped external coils create a twisted magnetic field to
confine hot plasma. This is computational research, not a home reactor-building project.

“Best” means balancing performance, buildability, robustness, safety and practical
cost. We want improvements that others can reproduce and challenge.

**Research preview · 24 September 2026.** Our tools reproduce selected open
references, and one plasma-target study improved its chosen metric by **11.17%**.
The current challenge is turning targets into good coils: their full-grid normal
field error is **about 0.27 against a 0.0001 limit**. A feasible new coil design and
a state-of-the-art advance remain ahead of us. We are independent of Proxima Fusion
and the Max Planck Institute.

## Project plan and progress

These names and statuses are shared with the [scientific overview](docs/README.md)
and [detailed roadmap](docs/PROJECT_PLAN.md). “Complete” applies to the stated study,
not to an entire reactor.

| Step / milestone | Purpose and progress | Status |
| --- | --- | --- |
| **1. Establish a reliable foundation** | Reproduce selected W7-X/Goodman checks and reference coil calculations. | **Complete (local reference tools)** |
| **2. Make design iteration reproducible** | Change or optimize a design, save it, evaluate it separately and repeat. | **Complete (iteration workflow)** |
| **3. Improve our own plasma target** | One vacuum study achieved 11.17% lower relative bounce-action variance, a particle-motion diagnostic. | **Complete (vacuum study)** |
| **4. Develop plasma and coils together** | Starting coils pass geometry checks; their magnetic errors still exceed limits. Next: improve fields, preserve plasma benefits, test pressure and robustness. | **In progress** |
| **5. Demonstrate a meaningful design advantage** | Compare feasible designs fairly with leading references and independently verify the benefit. | **Not achieved** |
| **MS1. Contact Proxima Fusion with strong evidence** | Contact Proxima as soon as strong, reproducible, independently checked evidence shows our design is better than the design they are pursuing. | **Not reached** |
| **MSX. Our end goal** | Contribute to nuclear fusion for humanity by finding the best reactor design current technology can achieve. | **Long-term goal** |

MS1 requires a relevant, versioned Proxima reference, matched conditions and
explicit uncertainty and trade-offs. Improving our own seed or a sparse score
alone cannot establish that advantage. [MS1 evidence framework](docs/squid_c/MS1_PROXIMA_COMPARISON.md).
MSX extends beyond MS1 through expert scrutiny and practical follow-on work;
“best” is an ambition, not a proven global optimum.

## Start in three commands

From a checkout or source ZIP, with **Python 3.11+**:

```bash
python fusion.py public cases
python fusion.py public demo --output results/my-first-demo
python scripts/test_public.py
```

Check `python --version`. On macOS/Linux use `python3.11` or `python3.12` if
`python` is missing or too old; the macOS system `python3` may be 3.9.
On Windows use `py -3.12` instead of `python`. The historical native workflow
requires Python 3.12+ and additional dependencies; the public starter needs
**no installation, API key, GPU, compiler or download**.

The demo calculates real filament-coil fields, compares the seed with saved native
calculations and replays its report. Use a fresh output name on each run.
[Full quickstart](docs/validation/PUBLIC_QUICKSTART.md) ·
[Data and attribution](examples/clear-coil-samples-v1/README.md)

## What should I try?

Try a small coil-shape change that lowers the two sampled errors:

| Public metric (dimensionless; lower is better) | Reference score |
| --- | --- |
| `sampled_normal_rms` — field leaking across the target boundary | **0.304207** |
| `sampled_inner_vector_rms` — mismatch with the target field inside | **0.380435** |

`demo` and `evaluate` print reference and candidate scores, absolute change and
percentage change. Negative change is improvement; report both metrics and any
trade-off. Very small changes can be numerical noise.

**Exploratory PRs with lower sampled scores are welcome.** Include the candidate,
reference/reproduction commands and limitations. Counterexamples, negative results,
better tests and alternative approaches are equally useful.

The research limits are **1e-4 normal RMS and 0.01 inner-vector RMS**, measured by
a *different full-grid, flux-normalized workflow*. The sparse public scores above
are search feedback, not that acceptance test. Good samples can hide poor geometry
or field quality elsewhere; a promising candidate needs wider checks before any
physical-design claim. [Score interpretation](docs/validation/PUBLIC_QUICKSTART.md#what-the-report-means).

```bash
python fusion.py public init --output results/my-candidate.json
# Change coefficients, then:
python fusion.py public evaluate --candidate results/my-candidate.json --output results/my-report.json
python fusion.py public audit --report results/my-report.json --output results/my-audit.json
```

Use `public set-coefficient --help` to edit by name without indexing arrays.
For direct edits, `parameter_names[33*i + 11*axis + k]` labels
`base_coefficients[i][axis][k]`: coil `i=0..5`, axis `0=x,1=y,2=z`,
component `k=0..10`, in metres.
[Named-edit example and Fourier ordering](docs/validation/PUBLIC_QUICKSTART.md#evaluate-your-own-candidate).

## Contribute something useful

Bring an agent, write code yourself, reproduce a result or challenge an assumption.
**No listed issue, prior permission, particular model or compute-budget disclosure
is required.** [Research hints](docs/optimization/RESEARCH_HINTS.md) are invitations,
not an allowlist. Work beyond the starter's fixed-current format is welcome.

[Contribution guide](CONTRIBUTING.md) · [Review policy](docs/validation/REVIEW_POLICY.md) ·
[Agent guide](AGENTS.md) · [Security](SECURITY.md)

## How to read our evidence

- **Reference / baseline:** the saved starting case used for comparison.
- **RMS:** root-mean-square error; a measure of typical mismatch.
- **Bounce-action variance:** variation in a trapped-particle motion diagnostic;
  the 11.17% improvement concerns this metric, not measured confinement or power.
- **Physical acceptance (`physical_admission`):** all specified physics and
  engineering checks pass. Public reports keep this false: they test only samples.
- **Replay / audit:** recompute a saved report. Public replay uses the same
  implementation; independent implementations and external peer review are
  stronger, separate checks.

The starter and historical research have [documented local tests](docs/validation/PUBLIC_REVIEW_FIXES.md).
Hosted CI and independent-machine verification are still outstanding.
See [current scientific status](docs/STATUS.md) for the evidence and retained
failures; [historical research entry points](docs/validation/PROJECT_ENTRYPOINTS.md)
explain the larger native workflow.

## Licensing and project operation

Project code: [MIT](LICENSE), with [source/data notices](NOTICE.md).
Bundled derived Goodman data has [CC BY 4.0 attribution](examples/clear-coil-samples-v1/README.md).
Credit exact revisions and upstream sources: [CITATION.cff](CITATION.cff).

Public hosting is being prepared locally. PR monitoring and automatic merging are
not active. The [publication inventory](docs/validation/PUBLICATION_INVENTORY.md)
identifies historical machine paths requiring review.
[Launch checklist](docs/validation/REVIEW_POLICY.md#launch-checklist--requires-actual-hosting-work).
