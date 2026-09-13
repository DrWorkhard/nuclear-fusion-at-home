# Fusion Baselines

Reproducible research on stellarator coil optimization, independent physical
validation and a future SQuID-C baseline. W7-X is the physics/software regression,
StellCoilBench/LPQA the method benchmark, and open Goodman configurations the QI bridge.

## Research overview

Start with [the project overview](docs/README.md), [current assessment](docs/STATUS.md)
and [work plan](docs/PROJECT_PLAN.md). They are written for scientific review.
Detailed protocols, results and the research journal are indexed one level below.

Current assessment, 2026-09-13: no newly feasible optimization baseline,
no demonstrated SoTA design advance, and no complete SQuID-C readiness.
Long-term steps 1 and 2 remain open.

- [Latest coil results](docs/optimization/README.md): best fine raw flux about
  8.19e-8 versus the unchanged 1e-8 limit; tested geometry/native constraints pass.
  Exact current redistribution offers negligible gain. Six subsequent geometric
  trials all worsen flux despite verified derivatives and linearly descending
  models. Curvature/conditioning diagnosis is next; no new feasible design.
- [Fresh native integration](docs/validation/FRESH_NATIVE_INTEGRATION_RESULTS.md):
  all 21 local phases and six scientific tests without skips pass. Extended W7-X
  comparison deliberately retains three differences out of 63 quantities.
- [QI evaluation](docs/qi/README.md): independently audited action, coordinate and
  resolution diagnostics give useful partial results, not an absolute/global
  drift or maximum-J qualification. Historical author data are unchanged.
- [Finite coil geometry](docs/engineering/MESH_FINE_COMPLETION_RESULTS.md):
  all six original meshes pass the scoped non-shared-vertex nonoverlap test,
  with independent witnesses and exact historical prefix. Neighbor pairs, full
  assemblies and valid mechanics remain open.
- Software regression: 663 tests pass with 144 documented fixture warnings;
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
