# Historical research entry points

For a fresh checkout, start with the separate [portable quickstart](PUBLIC_QUICKSTART.md):
`python fusion.py public --help`. This page describes the original, source-bound
local research workflow, which needs Python 3.12+, native dependencies and
historical artifacts. The public sampled-field profile does not replace its
scientific acceptance.

The thin CLI introduced on 20 September 2026 standardizes invocation, discovery
and paths, not physics models. **Version 1 supports one fixed study profile, not
arbitrary new design files.**

## Start without computation

In the research checkout with its existing environment:

```bash
PYTHONPATH=src .venv/bin/python -m fusion_baselines --help
PYTHONPATH=src .venv/bin/python -m fusion_baselines profiles
PYTHONPATH=src .venv/bin/python -m fusion_baselines profiles --json
.venv/bin/python fusion.py profiles --json
```

The root `fusion.py` launcher needs no PYTHONPATH. The historical installed
`.venv/bin/fusion-baselines` command remains unchanged for intake/environment
checks; its code and package configuration are frozen. Nothing installs or syncs
automatically. Help and discovery do not import numerical/native libraries.
Read [status](../STATUS.md), [roadmap](../PROJECT_PLAN.md) and
[agent/maintainer rules](../../AGENTS.md) before running research.

Machine-readable discovery describes schema, profile ID, operations, inputs,
outputs, requirements, resources and exit codes. `supports_candidate_input:false`
is enforced. There is no arbitrary `--design`, executable backend path or silent
choice of another physics model.

## Profile: clear-coil-field-start-v1

The [field-start study](../optimization/CLEAR_COIL_FIELD_START_PROTOCOL.md) evaluates
four fixed cells: reference/own plasma targets, each with six/eight base coils.
It computes actual fields and derivatives but does not optimize a new coil shape.
`audit` independently reconstructs and checks a saved complete run. The existing
backends retain their thresholds, grids, normalization, source and resource checks.

| Operation | Unchanged backend | Output |
| --- | --- | --- |
| evaluate | scripts/run_clear_coil_field_start.py | Fresh directory: run.json, worker logs, raw arrays |
| audit | scripts/audit_clear_coil_field_start.py | Fresh JSON: separate numerical and physical decisions |

Requirements: research checkout including scripts, qualified native environment,
pinned external sources, preceding evidence and all referenced local raw data.
A wheel or Git clone alone lacks ignored historical artifacts. Do not rewrite
old absolute paths/hashes for portability; another machine needs separately
reproduced and checked data. [Environment and limits](ENVIRONMENT.md).

## Inspect the planned invocation

```bash
PYTHONPATH=src .venv/bin/python -m fusion_baselines evaluate \
  --profile clear-coil-field-start-v1 \
  --output artifacts/my-field-start \
  --dry-run
```

This writes nothing and starts no subprocess. JSON shows the exact command,
checkout, normalized paths and subprocess environment changes. It checks paths,
not complete source availability, physics, library compatibility or disk reserve.
Those checks belong to the backend during actual execution.

Relative paths resolve from the invoking working directory. Outside the checkout,
use `--project-root /absolute/path/fusion`. The subprocess uses the invoking
interpreter, checkout working directory and explicit checkout src PYTHONPATH,
without shell evaluation. Three numerical thread limits are set to 1 for that
subprocess only.

## Audit an existing run first

```bash
PYTHONPATH=src .venv/bin/python -m fusion_baselines audit \
  --profile clear-coil-field-start-v1 \
  --run artifacts/clear-coil-field-start-v1/run.json \
  --output artifacts/my-field-start-audit.json
```

All referenced files must exist locally. Audit also supports `--dry-run`.
Use new output paths: existing files, directories and symlinks are protected.
This independently recomputes from saved data; it is neither a fresh native-field
study nor an optimization.

## Repeat the registered study

Run deliberately with sufficient resources and no concurrent heavy job:

```bash
PYTHONPATH=src .venv/bin/python -m fusion_baselines evaluate \
  --profile clear-coil-field-start-v1 \
  --output artifacts/my-field-start

PYTHONPATH=src .venv/bin/python -m fusion_baselines audit \
  --profile clear-coil-field-start-v1 \
  --run artifacts/my-field-start/run.json \
  --output artifacts/my-field-start-audit-after-evaluation.json
```

Four serial workers, each limited to 1,800 seconds including imports/source
checks; at least 3 GiB reserve before each cell and 2 GiB during execution.
Each complete cell uses 262 native requests. There is no automatic audit, retry,
search, equilibrium solve or budget override. Preserve partial/failed output;
restarting needs a fresh path. Do not run this whole study just for a CLI smoke test.

## Interpret results

| Invocation | Exit 0 means | Other outcomes |
| --- | --- | --- |
| profiles / --dry-run | Successful discovery/planning | No numerical/physical decision |
| evaluate | Producer completed; independent acceptance still pending | 1 on failed/incomplete production |
| audit | Numerical startup_pass | 2 on numerical rejection or audit error; inspect JSON status |

Dispatcher/checkout/path errors return 1, argparse usage errors 2, signal N as
128+N, interruption as 130. The existing audit writer uses a fixed sibling
`.tmp` path, which must also be fresh. Backend output remains visible.
**Exit 0, all_pass and startup_pass do not mean physical design acceptance.**
The completed field-start study passes numerically while
`physical_seed_pass:false` and `step4_pass:false`.

## Other profiles and new designs

Construction APIs `evaluate(x)`/`snapshot(x)` remain separate from this fixed
study command. An arbitrary snapshot needs its own versioned input/evaluation
profile, source binding and qualified workflow. The completed
[52-state perturbation study](../geometry/COIL_PERTURBATION_RESULTS.md) uses separate
specialized runners/auditors and is not offered by version 1 of this CLI.

Extend the explicit registry with tests and documented acceptance/exit semantics.
Keep existing backends/protocols unchanged. Never import code or execute commands
provided by a candidate JSON, or relabel LPQA/plasma/engineering checks as
interchangeable profiles.

## Historical verification record

The original 64 dispatch/negative controls passed: lightweight discovery, paths,
environment, exit codes, root launcher and unchanged old CLI/package bytes.
Initial full regression: 1,897 passed, three preservation failures, 334 known
warnings in 195.14 seconds. Extending the frozen old CLI caused the failures;
its exact bytes were restored and the new entry layer made additive.
Preserved failed JUnit: `artifacts/project-entrypoints-v1-qualification/regression.xml`.

Corrected full regression: **1,904 passed**, 334 known warnings, no errors/skips
in 208.42 seconds. JUnit: `artifacts/project-entrypoints-v2-qualification/regression.xml`,
SHA256 `a9b85b88aa95f0141e9632d3652572931d7a92774c10e994b0564e656d1f91d1`.
[Source-bound qualification](../../evidence/project-entrypoints-v1-qualification.json)
records both attempts. Ruff, documentation/whitespace and nine additional document
tests passed. Internal review is not external scientific peer review.

After implementation commit `caa1333`, the root launcher audited the existing run:
exit 0, 2,434 bound references; every result field matched the original except
expected Git metadata `auditor_repository`. All four numerical passes and physical
rejections remain. [Replay evidence](../../evidence/project-entrypoints-v1-replay.json);
output `artifacts/project-entrypoints-v1-replay/audit.json`, SHA256
`8e0af0395d3ddc7e561c786ea99984ac6f79a185894ae2a942f389bb398c7936`.

No new native-field study, search or equilibrium solve was performed by that
audit. Later geometry qualification is separate. The English navigation update
changes none of those historical artifacts or results.
