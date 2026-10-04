# Reproducing current and frozen results

The main branch contains the public starter, working penalized fitting, shared
field/geometry checks and their focused tests. Completed experimental pipelines,
their tests and detailed protocols are preserved in Git—not a copied archive.

## Freeze identity

Annotated tag: **`research-freeze-2026-09-27`**

Commit: **`56181dc4250cb24ce3d2bedf5cec3d894d1ac250`**

This is the complete tracked state before the simplicity cleanup. It includes
Steps 1–3, retired LPQA/certified-search/engineering pipelines, old research CLI,
protocols, negative findings and the completed matched coil restart.

Read any removed path without changing the current worktree:

```bash
git show research-freeze-2026-09-27:docs/validation/FOUNDATION_ACCEPTANCE_RESULTS.md
git show research-freeze-2026-09-27:docs/qi/PLASMA_BALANCED_RESULTS.md
git show research-freeze-2026-09-27:scripts/run_foundation_acceptance.py
git ls-tree -r --name-only research-freeze-2026-09-27
```

For a separate historical working tree, choose a new destination:

```bash
git worktree add --detach ../fusion-frozen research-freeze-2026-09-27
```

Both historical tags are available in the
[public repository](https://github.com/DrWorkhard/nuclear-fusion-at-home/tree/research-freeze-2026-09-27).
Use a full clone, or fetch the tag explicitly if your checkout is shallow:

```bash
git fetch origin tag research-freeze-2026-09-27
```

Do not run old workflows blindly: read the protocol and resource requirements
at the tag. When a report records an earlier source revision, use that exact
revision and verify its hashes; the freeze tag is the navigation starting point,
not a substitute for every earlier byte identity.

## Later completed tools

The 4 October simplification removes the completed boundary calibration and coil
start screen drivers/tests, inactive `environments/` manifests, and superseded
review/decision documents. Their last complete pre-cleanup tree is
**`d5d395b`**. For example:

```bash
git show d5d395b:scripts/explore_boundary_controls.py
git show d5d395b:scripts/explore_coil_starts.py
git show d5d395b:environments/vmecpp/pyproject.toml
```

Use the exact producer revision recorded by each experiment for numerical replay;
this newer navigation revision does not replace older source identities. Native
fits retain their imported and hash-bound dependencies. Their data still requires
the recorded local artifacts, including failed runs. No evidence or raw data is
removed by this cleanup.

## Minimal result summaries

The second cleanup keeps completed Step 1–3 conclusions in the
[step index](../steps/README.md) and coil results in [status](../STATUS.md), with
direct evidence links. Full result pages, the old sampled geometry audit and the
completed starter exporter remain at **`8c5753c`**:

```bash
git show 8c5753c:docs/optimization/LENGTH_HEADROOM_EXPLORATION.md
git show 8c5753c:docs/steps/STEP_3_PLASMA_TARGET.md
git show 8c5753c:scripts/audit_coil_geometry.py
git show 8c5753c:scripts/export_public_starter.py
```

These are navigation revisions. Reproduce numerical claims from the original
producer revision and environment in their evidence. The exporter/audit are not
needed to use the public packet or run the active fitter. Shared acceptance code,
original evidence, candidate JSON, raw runs and installed environments are retained.

## Evidence paths and data

Old evidence JSON remains unchanged. A removed repository-relative source or
protocol path resolves in the frozen tree; absolute maintainer-local paths also
require their original raw artifacts or a separately identified portable export.
The source revision is a commit hash, not an assumed current file.

**The tag is not a backup of ignored data.** Raw NPZ files, local experiments,
external checkouts and native environments were not deleted and are not included
in the tag. Historical numerical replay still needs the documented data and
environment. Independent backup/restore and separate-machine reproduction remain
unverified.

## Active checks

```bash
python scripts/test_public.py
python scripts/check_docs.py
git diff --check
```

The remaining `tests/` cover active numerical primitives and fitting; run them
in the documented [native environment](ENVIRONMENT.md). Core CI uses its small
dev-only subset, not the native suite. Old whole-tree preservation auditors and
hash-exception rules are retired; Git preserves their original versions.

[Current evidence](../STATUS.md) · [Active methods](../optimization/README.md)
