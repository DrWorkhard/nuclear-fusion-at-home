# Nuclear Fusion @ Home

Open, reproducible stellarator research — contributed by people and their agents.

Our end goal is to **contribute to nuclear fusion for humanity by finding the best
reactor design current technology can achieve**. We pursue that goal through open,
reproducible research that others can test, challenge and build on.

We want to find better combinations of **magnetic-field quality, buildable coils
and robustness**, and verify improvements computationally. We work on
stellarators: fusion devices whose external coils create a twisted magnetic field
intended to confine hot plasma. Our work is simulation and software, not a home
reactor construction project.

“Best” means a defensible balance of performance, buildability, robustness, safety
and practical cost under explicit technological constraints—not just the lowest
simulation score. This is a research ambition, not a claim of proven global optimality.

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
The committed-source starter passes its [local copied-tree qualification](docs/validation/PUBLIC_RELEASE_RESULTS.md),
including a changed candidate and tamper rejection. Hosted CI and independent-
machine reproduction have not yet been verified.

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

| Area                | Established result                                                                                  | Important limit                                                                           |
| ------------------- | --------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Research foundation | Reproduced bounded local W7-X/Goodman checks and a repeatable coil-optimization/evaluation workflow | Not the complete W7-X device or a universal physics qualification                         |
| Own plasma target   | 11.17% lower fine-grid relative bounce-action variance in a registered vacuum study                 | A specific numerical proxy, not demonstrated confinement, global QI or power output       |
| Coil realization    | Geometrically acceptable starting coils and independently checked field calculations                | Their magnetic errors still fail the research acceptance limits                           |
| Public access       | Dependency-free real-coil starter; 36 public tests and all eight copied-tree checks pass            | Locally verified, not yet hosted or independently reproduced; not full physics acceptance |

See [the evidence-based status](docs/STATUS.md) for sources and failure modes.
Construction, numerical correctness and physical acceptance are different things.
A merged contribution or green test run does not automatically establish a
scientific improvement.

## Project plan and progress

These are the numbered steps referenced throughout the research documents.
“Complete” always means complete within the stated scope, not a finished reactor.

| Step | Purpose | What is done / current status |
| --- | --- | --- |
| **1. Establish a reliable foundation** | Reproduce open references and qualify the calculations we will use. | **Complete in the bounded local scope:** specified W7-X/Goodman checks and reference coil tools pass. |
| **2. Make design iteration reproducible** | Load a reference, change or optimize it, save the result, independently evaluate it and repeat. | **Complete in the registered scope:** real optimization paths replay and candidate checks run; rejected candidates remain rejected. |
| **3. Improve our own plasma target** | Find and verify a better quasi-isodynamic-like target magnetic configuration. | **Complete for one vacuum study:** the 11.17% diagnostic improvement above, not full QI or demonstrated confinement. |
| **4. Develop plasma and coils together** | Turn target fields into realizable coils, preserve their physics, and address pressure, finite coil geometry and robustness. | **In progress:** acceptable starting geometry and checked field calculations exist; magnetic errors still fail acceptance. No new physically accepted coil design yet. |
| **5. Demonstrate a meaningful design advantage** | Compare accepted designs fairly with relevant leading references and independently verify the advantage; work toward MS1 below. | **Not achieved:** no demonstrated advantage over Proxima Fusion's design and no state-of-the-art or power-plant claim. |

Our immediate priority is letting outside contributors work productively on those
questions. The public starter is an entry point, not a restriction on the research.
The much larger historical research suite remains available with additional
native dependencies and local artifact requirements; it is not installed by the
quickstart.

[Scientific overview](docs/README.md) · [Current status](docs/STATUS.md) ·
[Roadmap](docs/PROJECT_PLAN.md) · [Historical research entry points](docs/validation/PROJECT_ENTRYPOINTS.md)

## MS1 — Evidence strong enough to contact Proxima Fusion

**As soon as we have strong, reproducible and independently checked evidence that
a design we found is better than the design Proxima Fusion is pursuing, we will
contact Proxima Fusion to share the evidence and invite technical scrutiny.**
This is **MS1**, our first external-impact milestone. **MS1 has not been reached.**

The comparison must identify the actual reference design and its version, use
like-for-like operating assumptions and realistic technology constraints, and
show a meaningful design-level advantage with uncertainties and trade-offs made
explicit. A lower sparse-field score, improvement over our own starting point,
or an outdated/mismatched reference is not sufficient. The
[MS1 evidence framework](docs/squid_c/MS1_PROXIMA_COMPARISON.md) explains the bar.

MS1 is a targeted outcome of Step 5, not the end goal and not proof that we have
found the globally best reactor. After reaching it, the aim is to subject the
design to expert review, improve it further and help turn useful findings into
practical fusion progress. No outreach or affiliation is implied by this plan.

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
