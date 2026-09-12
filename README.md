# Fusion Baselines

Reproducible research on stellarator coil optimization, independent physical
validation and a future SQuID-C baseline. W7-X is the physics/software regression,
StellCoilBench/LPQA the method benchmark, and open Goodman configurations the QI bridge.

## Research overview

Start with [the project overview](docs/README.md), [current assessment](docs/STATUS.md)
and [work plan](docs/PROJECT_PLAN.md). They are written for scientific review.
Detailed protocols, results and the research journal are indexed one level below.

Current assessment, 2026-09-12: qualified numerical methods and useful independent
checks, but no newly feasible optimization baseline, no demonstrated SoTA design
advance, and no complete SQuID-C readiness. All four candidates from the latest
equal-wall-time pilot fail independent acceptance. The subsequent direct-constraint
SLSQP pilot passes the tested geometry and additional native checks, but its
selected candidate's independently measured raw flux remains 23.3 times the limit;
the budget-limited run does not establish convergence.

The [quadratic field-model diagnostic](docs/optimization/QUADRATIC_FIELD_MODEL_RESULTS.md)
predicts the correct change sign on all four frozen probes and reduces prediction
error by at least 99.907% versus the linear model. Full native Jacobian comparisons
and a separate core audit pass. Earlier failed checks remain recorded. Next:
execute the [fixed GN trust pilot](docs/optimization/GN_TRUST_PILOT_PROTOCOL.md)
(two repeats, at most 1024 full bundles each), then independently validate its
output. The diagnostic probes are not admitted designs.

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
