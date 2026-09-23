# Public quickstart

For people and coding agents. Python3.12+ and a checkout or source ZIP are enough
for this starter. No package installation, account, API key, GPU, native compiler,
network access during evaluation, or historical local artifacts are needed.
On systems where the command is `python3`, substitute it for `python` below.

Implementation status: unit/analytic tests pass; the committed-source real-reference
qualification is the next release check. Do not interpret the instructions as a
claim that hosted CI or independent hardware reproduction has already passed.

## Reproduce a real reference

Open a terminal in the repository directory:

```bash
python --version
python fusion.py public cases
python fusion.py public demo --output results/my-first-demo
```

The demo computes the actual six-base-coil reference's B and A on192 saved points,
at256 and512 quadrature nodes per filament. It compares the256-node result to
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

Edit `base_coefficients` in that JSON file. Keep the declared names, metre units,
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

| Field | Meaning | Not established |
| --- | --- | --- |
| `levels` | Actual sampled B/A and error metrics at256/512 coil nodes | Full-surface field fidelity |
| `sampled_normal_rms` | Weighted relative normal field on64 boundary samples | A physically admitted magnetic surface |
| `sampled_inner_vector_rms` | Vector mismatch on64 interior samples with fixed target B² | QI quality or confinement |
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

The36 public unit/analytic checks are separate from the historical native suite.
They include an analytic circular-coil control, schema/mapping checks, file/hash
protection and rejection of forged scope flags. Cost, budget, hardware and a
related hint are optional in contribution metadata. Plain Markdown PRs also work.

Maintainers can test the full portable path in a copied tree without the research
environment:

```bash
python -I -S scripts/verify_public_release.py --output results/portable-check
```

This retains the copied files, operation logs, actual reports and a qualification
summary. It performs the reference replay, one fixed1micrometre input variation
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
