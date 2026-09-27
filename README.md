# Nuclear Fusion @ Home

Open stellarator research, contributed by people and their agents.

Our end goal is to **contribute to nuclear fusion for humanity by finding the
best reactor design current technology can achieve**. “Best” balances plasma
performance, buildability, robustness, safety and cost—not one score.
This is computational research, not a home reactor-building project.

We study stellarators: devices whose shaped external coils create a twisted
magnetic field that confines plasma. Our immediate question is whether practical
coil shapes can accurately reproduce a promising plasma target.

**Research preview · 27 September 2026.** A geometry-checked exploratory fit reaches
normal-field RMS **0.002050 versus a 1e-4 pilot limit**, with interior RMS
0.01166 above its 0.01 limit. A longer-coil fit reaches
**0.001948**, with interior-vector RMS **0.009770 below the 0.01 limit**, but
its continuous coil-length bounds remain unresolved. This is useful progress,
not an accepted design or a state-of-the-art advantage. Realized magnetic surfaces and plasma-benefit transfer
remain open. [Scientific evidence](docs/STATUS.md).

We are independent of, and not endorsed by, Proxima Fusion or the Max Planck Institute.

## Project plan and progress

Completed steps passed their defined local scope; they do not imply a complete
reactor. [Detailed roadmap](docs/PROJECT_PLAN.md) · [Scientific overview](docs/README.md)

| Step / milestone | Goal | Status |
| --- | --- | --- |
| 1. Establish a reliable foundation | Reproduce selected open reference calculations. | Complete (local reference tools) |
| 2. Make design iteration reproducible | Change, save, independently check and repeat. | Complete (iteration workflow) |
| 3. Improve our own plasma target | Confirm a better vacuum plasma diagnostic. | Complete (vacuum study) |
| 4. Develop plasma and coils together | Realize and preserve plasma benefits with practical coils. | In progress |
| 5. Demonstrate a meaningful design advantage | Independently verify benefit against leading references. | Not achieved |
| MS0. Publish a useful open coil benchmark | Attributed challenge, calibrated checks and independent reproduction. | Planned |
| MS1. Contact Proxima Fusion with strong evidence | Show our design is better than their relevant design, then contact them. | Not reached |
| MSX. Our end goal | Contribute to fusion for humanity through the best achievable reactor design. | Long-term goal |

MS1 needs a versioned Proxima reference, matched conditions and reproducible,
independently checked benefits. Improving our own seed or public samples is
insufficient. MSX is an ambition, not a claimed global optimum.
MS0 can deliver a useful positive or negative benchmark earlier; we will assess
contributing to existing community tools before building new infrastructure.

## Start in three commands

Obtain a checkout or source ZIP and open its directory. When hosted, use the
actual repository's **Code → HTTPS** clone URL or **Download ZIP**; otherwise
obtain a checkout from the maintainer. No hosted URL is claimed here.

With **Python 3.11+**, run:

```bash
python fusion.py public cases
python fusion.py public demo --output results/my-first-demo
python scripts/test_public.py
```

Check `python --version`. On macOS/Linux, use `python3` only if it is new enough;
the system version may be older. On Windows, try `py -3.12`.
The starter needs **no package installation, API key, GPU or extra download**.

Expected: the demo prints `"reference_reproduced": true` and
`"physical_admission": false`; tests finish with `OK`.
Use a fresh output name for each run.
[Quickstart and troubleshooting](docs/validation/PUBLIC_QUICKSTART.md).

## What should I try?

Try a small coil-coefficient change and lower **both** public errors:

| Metric—lower is better | Reference |
| --- | ---: |
| `sampled_normal_rms`: field leaking across the target boundary | 0.304207 |
| `sampled_inner_vector_rms`: mismatch with the target field inside | 0.380435 |

Start around 0.01–0.1 mm (`1e-5`–`1e-4` metres); this is an exploratory scale,
not a guarantee of improvement or safe geometry. Evaluation prints differences
from the reference. Report both metrics and any trade-off.

```bash
python fusion.py public init --output results/my-reference.json
python fusion.py public set-coefficient --candidate results/my-reference.json --name "coil[0]/xc(0)" --value 0.9609191138350243 --output submissions/my-study/candidate.json
python fusion.py public evaluate --candidate submissions/my-study/candidate.json --output results/my-report.json
python fusion.py public audit --report results/my-report.json --output results/my-audit.json
```

The example changes one coefficient by +0.1 mm; it is not a known improvement.
`--value` is absolute, in metres. Quote coefficient names.
[Named mapping and Python search loop](docs/validation/PUBLIC_QUICKSTART.md#evaluate-your-own-candidate)
· [Lower-score example](submissions/constraint-aware-shape52/README.md).

The public starter uses sparse samples and fixed currents. Research uses dense
grids and flux-normalized currents, with limits **1e-4 normal RMS** and
**0.01 interior-vector RMS**. Those are different checks. Public `audit` is a
same-code replay, not independent physical acceptance.

## Contribute

Useful unsolicited ideas, exploratory improvements, replications, critical
reviews and negative results are welcome. Compute spending is optional to report.
[CONTRIBUTING](CONTRIBUTING.md) explains PRs, evidence and attribution;
[research hints](docs/optimization/RESEARCH_HINTS.md) are invitations, not an allowlist.

The active research path is penalized coil fitting plus shared field/geometry
checks. Completed and retired research code/tests live at Git tag
`research-freeze-2026-09-27`, not in the default working tree.
[Active research](docs/optimization/README.md) ·
[Reproduce frozen results](docs/validation/REPRODUCING_RESULTS.md).

Code is MIT-licensed; data retains its own attribution and licenses.
See [LICENSE](LICENSE), [data credits](examples/clear-coil-samples-v1/README.md)
and [CITATION.cff](CITATION.cff).
