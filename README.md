# Fusion Baselines

Reproducible research on stellarator coil optimization, independent physical
validation and a future SQuID-C baseline. W7-X is the physics/software regression,
StellCoilBench/LPQA the method benchmark, and open Goodman configurations the QI bridge.

## Research overview

Start with [the project overview](docs/README.md), [current assessment](docs/STATUS.md)
and [work plan](docs/PROJECT_PLAN.md). They are written for scientific review.
Detailed protocols, results and the research journal are indexed one level below.

Current assessment, 2026-09-14: **sharpened steps 1 and 2 are complete** for the
bounded local W7-X/Goodman regression and LPQA fixed-surface filament workflow.
The [consolidated acceptance and runbook](docs/validation/FOUNDATION_ACCEPTANCE_RESULTS.md)
record 720 tests, six mandatory scientific regressions without skips, exact two-run
24-bundle iteration, independent audits and all four candidate holdout phases.
This qualifies the workflow, not a better/feasible design or SQuID-C readiness.
All earlier studies are preserved at tag `foundation-pre-scope-2026-09-13`
(`5971fee`). Broader QI, engineering and performance research remains deferred.
After that handoff the user explicitly requested step3. The new
[plasma-boundary optimization protocol](docs/qi/PLASMA_OPTIMIZATION_PROTOCOL.md)
is active. Its first boundary improves training action variance by14.35% but is
independently rejected:15.53% worse on the expanded domain and20 local action
violations. All source/field/refinement checks pass; step3 is not complete.
See the [plasma results and runbook](docs/qi/PLASMA_OPTIMIZATION_RESULTS.md).

- [Latest coil results](docs/optimization/README.md): best fine raw flux about
  8.13e-8 versus the unchanged 1e-8 limit; tested geometry/native constraints pass.
  The completed curvature-informed follow-up improves fine flux by0.754%, with
  exact two-run repetition, separate audit and all four independent holdout phases.
  Both runs exhaust their fixed budgets; no convergence or feasible-design claim.
- [Fresh native integration](docs/validation/FRESH_NATIVE_INTEGRATION_RESULTS.md):
  all 21 local phases and six scientific tests without skips pass. Extended W7-X
  comparison deliberately retains three differences out of 63 quantities.
- [QI evaluation](docs/qi/README.md): independently audited action, coordinate and
  resolution diagnostics give useful partial results. Absolute drift/action/SI
  normalization passes two81-cell analytic controls and independent scalar audits,
  including nonzero radial drift and phase covariance. Finite particle-orbit and
  real QI-field/global qualification remain open. Author data are unchanged.
- [Finite coil geometry](docs/engineering/MESH_FINE_COMPLETION_RESULTS.md):
  all six original meshes pass the scoped non-shared-vertex nonoverlap test,
  with independent witnesses and exact historical prefix. Neighbor pairs, full
  assemblies and valid mechanics remain open.
- Software regression: 720 tests pass with 144 documented fixture warnings;
  Ruff and documentation checks pass. The separate strict netCDF4 import warning
  remains unresolved; this is not an ABI-freedom or hosted-CI claim.

Prior searches, source reconstructions, negative trials and the disk incident
remain preserved in the [research journal](docs/logbook/README.md) and linked
detail reports. Earlier equal-time gains apply to one infeasible start and do
not establish a general method ranking or better power-plant performance.

Persistent working and documentation rules: [AGENTS.md](AGENTS.md).
Documentation must be updated after every completed work step, including checking
both READMEs, the current assessment and the work plan for affected summaries.
Environment details: [validation overview](docs/validation/README.md).
Documentation checks: `python scripts/check_docs.py`.

## Canonical commands

Recheck the bounded foundation in the existing pinned environment, using new
output names (do not sync or install anything for this check):

```bash
PYTHONPATH=src .venv/bin/python scripts/run_foundation_acceptance.py \
  evidence/my-foundation-check artifacts/my-foundation-check
```

`summary.json` separates the two milestone results from physical candidate
acceptance. The demonstrated candidates remain rejected at the unchanged flux
limit. The runbook also documents the standalone iteration/audit/holdout cycle.

Run bootstraps only in the intended environment. Keep the qualified native root
environment intact; run core-only synchronization in a separate clone.

```bash
./scripts/bootstrap_macos.sh
uv run python scripts/run_stellcoilbench_case.py \
  external/stellcoilbench/cases/basic_LandremanPaulQA.yaml \
  artifacts/runs/lpqa-baseline
./scripts/bootstrap_vmecpp.sh
./scripts/bootstrap_qi_data.sh
./scripts/bootstrap_simple.sh
./scripts/bootstrap_neo_jax.sh
uv run fusion-baselines summarize-equilibrium \
  manifests/qi-goodman-2022.json --data-root .
uv run python scripts/audit_squid_c_availability.py \
  evidence/squid-c-availability-$(date +%F).json
```
