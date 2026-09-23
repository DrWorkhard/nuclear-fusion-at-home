# Nuclear Fusion @ Home

Open, reproducible stellarator research — contributed by people and their agents.

We want to find better combinations of **magnetic-field quality, buildable coils
and robustness**, and verify improvements computationally. We start with
stellarators: fusion devices whose external coils create a twisted magnetic field
intended to confine hot plasma. Our work is simulation and software, not a home
reactor construction project.

**Research preview, 23 September 2026.** We have useful tested tools and a bounded
plasma-design result, but **no newly accepted feasible coil design, demonstrated
state-of-the-art advance, or power-plant breakthrough**. We are not affiliated
with Proxima Fusion or the Max Planck Institute; their work and open research
provide important scientific context.

## Start in three commands

From a checkout or source ZIP, with **Python 3.12+**:

```bash
python fusion.py public cases
python fusion.py public demo --output results/my-first-demo
python scripts/test_public.py
```

Use `python3` instead of `python` if that is your system's command.
No package installation, API key, GPU, native compiler or large download is needed
for this portable starter. All starter data is included. Use a fresh output name
for each run; existing evidence is not overwritten.

The demo computes **real filament-coil fields**, compares the unchanged reference
against saved native calculations, and replays its report. It deliberately reports
`physical_admission: false`: sparse field checks are not full design acceptance.
The committed-source reference qualification is being completed; do not infer
hosted CI success from the presence of workflow files.

[Full quickstart and candidate format](docs/validation/PUBLIC_QUICKSTART.md) ·
[Reference data and attribution](examples/clear-coil-samples-v1/README.md)

## Contribute something useful

Bring your own agent, write code yourself, challenge an assumption, reproduce a
result or propose a new approach. **No prior issue, requested task, specified model
or declared compute budget is required.** Negative results and unsolicited ideas
are welcome. Our [research hints](docs/optimization/RESEARCH_HINTS.md) explain what
currently seems promising; they are not an allowlist.

```bash
python fusion.py public init --output results/my-candidate.json
# Edit the named Fourier coefficients in my-candidate.json, then:
python fusion.py public evaluate --candidate results/my-candidate.json --output results/my-report.json
python fusion.py public audit --report results/my-report.json --output results/my-audit.json
```

This first candidate interface has a narrow fixed-current, sampled-field scope.
Work beyond that format is still welcome through ordinary proposals and PRs.
Explain what changed, show evidence, state limitations and credit sources.
Compute/cost information is optional; measured efficiency claims still need evidence.

[Contribution guide](CONTRIBUTING.md) · [Review policy](docs/validation/REVIEW_POLICY.md) ·
[Security](SECURITY.md)

## What is actually established?

| Area | Established result | Important limit |
| --- | --- | --- |
| Research foundation | Reproduced bounded local W7-X/Goodman checks and a repeatable coil-optimization/evaluation workflow | Not the complete W7-X device or a universal physics qualification |
| Own plasma target | 11.17% lower fine-grid relative bounce-action variance in a registered vacuum study | A specific numerical proxy, not demonstrated confinement, global QI or power output |
| Coil realization | Geometrically acceptable starting coils and independently checked field calculations | Their magnetic errors still fail the research acceptance limits |
| Public access | Small self-contained real-coil dataset, plain JSON candidates and dependency-free evaluation/replay | Not the full historical native workflow or physical admission; release checks are tracked separately |

See [the evidence-based status](docs/STATUS.md) for sources and failure modes.
Construction, numerical correctness and physical acceptance are different things.
A merged contribution or green test run does not automatically establish a
scientific improvement.

## Where we are going

The scientific roadmap remains: reliable foundation → reproducible iteration →
own plasma targets → coupled plasma/coil development → independently demonstrated
improvements. **Step 4 remains open**, including realized-field/QI transfer,
finite pressure, finite coil geometry and robustness.

Our immediate priority is letting outside contributors work productively on those
questions. The public starter is an entry point, not a restriction on the research.
The much larger historical research suite remains available with additional
native dependencies and local artifact requirements; it is not installed by the
quickstart.

[Scientific overview](docs/README.md) · [Current status](docs/STATUS.md) ·
[Roadmap](docs/PROJECT_PLAN.md) · [Historical research entry points](docs/validation/PROJECT_ENTRYPOINTS.md)

## Licensing, credit and project operation

Project code: [MIT](LICENSE), with [source/data notices](NOTICE.md).
The bundled derived Goodman reference data has
[separate CC BY 4.0 attribution](examples/clear-coil-samples-v1/README.md); do not
assume the code license covers every upstream dataset. Cite the exact revision
and upstream sources used: [CITATION.cff](CITATION.cff).

The repository is being prepared locally for public hosting. No automatic PR
monitoring, merging, publication or hosted CI success is implied.
[Launch checklist](docs/validation/REVIEW_POLICY.md#launch-checklist--requires-actual-hosting-work).

Historical evidence and failures remain preserved. Maintainer/agent working
instructions: [AGENTS.md](AGENTS.md). Documentation structure check:
`python scripts/check_docs.py`.
