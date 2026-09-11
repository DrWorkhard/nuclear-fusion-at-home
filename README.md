# Fusion Baselines

Reproducible research on stellarator coil optimization, independent physical
validation and a future SQuID-C baseline. W7-X is the physics/software regression,
StellCoilBench/LPQA the method benchmark, and open Goodman configurations the QI bridge.

## Research overview

Start with [the project overview](docs/README.md), [current assessment](docs/STATUS.md)
and [work plan](docs/PROJECT_PLAN.md). They are written for scientific review.
Detailed protocols, results and the research journal are indexed one level below.

Current assessment, 2026-09-11: qualified numerical methods and useful independent
checks, but no newly feasible optimization baseline, no demonstrated SoTA design
advance, and no complete SQuID-C readiness. All four candidates from the latest
equal-wall-time pilot fail independent acceptance.

Persistent working and documentation rules: [AGENTS.md](AGENTS.md).
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
