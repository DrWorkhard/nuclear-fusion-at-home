# Public quickstart

For people and coding agents. Python 3.11+ and a checkout or source ZIP are enough
for this starter. No package installation, account, API key, GPU, native compiler,
network access during evaluation, or historical local artifacts are needed.
Check `python --version` first. Use `python3.11` or `python3.12` on macOS/Linux
if necessary; the macOS system `python3` may be too old. On Windows substitute
`py -3.12` for `python`. The launcher explains unsupported versions before import.
The separate historical native workflow still requires Python 3.12+.

Current local verification: **44 public tests and eight copied-tree release checks
pass on each of Python 3.11.4, 3.12.13 and 3.14.3**, including the real reference,
changed candidate and tamper rejection. The fresh dev-only core runner also passes.
See the [original verification](PUBLIC_RELEASE_RESULTS.md) and
[current review fixes and tests](PUBLIC_REVIEW_FIXES.md). Hosted CI and independent
hardware reproduction have not yet been verified.

## Reproduce a real reference

Open a terminal in the repository directory:

```bash
python --version
python fusion.py public cases
python fusion.py public demo --output results/my-first-demo
```

The demo computes the actual six-base-coil reference's magnetic field B and vector
potential A on 192 saved points, at 256 and 512 quadrature nodes per filament.
It compares the 256-node result to
previous native calculations and reruns the public computation from the saved
candidate to check its report. The latter uses the same implementation, not a
second mathematical implementation. Expected output: `reference_reproduced: true`
and **`physical_admission: false`**. The second flag is intentional.

The output directory contains `candidate.json`, `report.json`, and `audit.json`.
Existing output paths are refused; use a new name for another run. If interrupted,
keep the partial directory for diagnosis and choose a fresh path, not a silent retry.

## Evaluate your own candidate

```bash
python fusion.py public init --output results/my-candidate.json
```

Edit `base_coefficients` in that JSON file, or use the named helper:

```bash
python fusion.py public set-coefficient --candidate results/my-candidate.json --name 'coil[0]/xc(0)' --value 1.2 --output results/changed-candidate.json
```

This sets an **absolute value in metres**, not an increment. The value above is
an editing example, not an optimized or safe coil change. Evaluate the resulting
`results/changed-candidate.json` to check it. Existing output files are protected.

For direct JSON edits, the exact zero-based mapping is:

```text
parameter_names[33*i + 11*axis + k] labels base_coefficients[i][axis][k]
i = 0..5; axis = 0:x, 1:y, 2:z; k = 0..10
component order = c(0), s(1), c(1), s(2), c(2), ..., s(5), c(5)
example: parameter_names[49] = coil[1]/ys(3) -> base_coefficients[1][1][5]
```

Keep the declared names, metre units,
shape and case ID. The format stores six Cartesian Fourier curves and preserves
the case's fixed symmetry and signed currents. Then:

```bash
python fusion.py public evaluate --candidate results/my-candidate.json --output results/my-report.json
python fusion.py public audit --report results/my-report.json --output results/my-audit.json
```

No result is automatically submitted or merged. For a PR, follow
[CONTRIBUTING](../../CONTRIBUTING.md). Work outside this first candidate format
is also welcome; explain its value and proposed verification separately.

## What the report means

Aim to **lower both** `sampled_normal_rms` (reference **0.3042070281**) and
`sampled_inner_vector_rms` (reference **0.3804347184**). `demo` and `evaluate`
print both reference/candidate values and signed absolute/percentage changes:
negative means lower; report any trade-off rather than hiding a worsened metric.
Reference scores are calculated from the bundled native 256-node fields;
candidate scores use 512 nodes. Roundoff-level differences are not improvements.
Cross-version reproduction can differ at rounding level: Python 3.11's reference
report has two 256-node metrics differing by less than 1.12e-16 from Python 3.12,
with identical B/A arrays. Existing replay tolerances cover this; report hashes
need not be identical across Python versions.

**Lower sampled-score PRs are welcome as exploratory results**, even before full
research acceptance. Provide the candidate, commands, baseline comparison and
limitations. Numerical counterexamples and useful negative results also count.
For a stronger claim, check finer/unseen spatial samples, continuous geometry and
the relevant physical constraints in a separate, agreed evaluation profile.

For context, the research field limits are normal RMS **1e-4** and inner-vector
RMS **0.01**. Those are full-grid, flux-normalized measures, not thresholds for
this sparse fixed-current profile. Historical starts scored about **0.27** and
**0.36–0.37** respectively under that full-grid profile, far from the limits.
Do not compare public scores to those limits as an acceptance ratio or infer
geometry, QI or reactor performance from a public improvement.

| Field | Meaning | Not established |
| --- | --- | --- |
| `levels` | Actual sampled B/A and error metrics at 256/512 coil nodes | Full-surface field fidelity |
| `sampled_normal_rms` | Weighted relative normal field on 64 boundary samples | A physically admitted magnetic surface |
| `sampled_inner_vector_rms` | Vector mismatch on 64 interior samples with fixed target B² | QI quality or confinement |
| `resolution_differences` | Difference between the two filament quadratures | A proof that all numerical errors are small |
| `seed_native_reference` | Match to saved native B/A for the unchanged reference only | A native replay of an arbitrary new candidate |
| `report_replay_pass` | Trusted public evaluator reproduces the submitted report | Independent-implementation or physical acceptance |

Currents are **not renormalized** when candidate geometry changes. Sparse sample
weights are renormalized only within the sample, so these numbers are not the
historical full-grid objectives. Public samples can be overfit. Continuous coil
clearance, curvature, target flux, islands, QI, pressure, finite-build and robustness
are outside this profile. Every report keeps `physical_admission:false` and
`step4_pass:false`; a successful command does not imply otherwise.

## Tests and optional contribution metadata

```bash
python scripts/test_public.py
python fusion.py public check-submission --file examples/contribution.json
```

The public unit/analytic checks are separate from the historical native suite.
They include an analytic circular-coil control, schema/mapping checks, file/hash
protection and rejection of forged scope flags. Cost, budget, hardware and a
related hint are optional in contribution metadata. Plain Markdown PRs also work.

Maintainers can test the full portable path in a copied tree without the research
environment:

```bash
python -I -S scripts/verify_public_release.py --output results/portable-check
```

This retains the copied files, operation logs, actual reports and a qualification
summary. It performs the reference replay, one fixed 1-micrometre input variation
without optimization, its replay, and rejection checks. It is a local portability
check, not a benchmark race or independent-machine validation.

## Troubleshooting and trust boundaries

- `Output already exists`: choose a fresh output file/directory. Do not remove
  old scientific evidence just to make a command run.
- `Evaluator changed`: a report is bound to its recorded evaluator hashes. Use
  its trusted source revision, or create a new report; do not patch old hashes.
- `Case digest mismatch`: restore the distributed case bytes; your design goes
  in a separate candidate. File hashes are not signatures of an unknown fork.
- Native-library or missing historical-artifact errors: check that you used
  **`public`**. The old `evaluate/audit` commands are different, research-local
  workflows with additional requirements.
- For a new research idea not covered by this format, open a proposal/PR anyway.
  Lack of a supported evaluator is a capability gap to discuss, not a reason to
  ignore the contribution.

Do not run foreign PR code in your trusted research workspace. Review against a
trusted project revision. The starter's data parser is not a sandbox for arbitrary
programs. [Review/security policy](REVIEW_POLICY.md) ·
[Dataset conventions and license](../../examples/clear-coil-samples-v1/README.md) ·
[Historical CLI](PROJECT_ENTRYPOINTS.md).
