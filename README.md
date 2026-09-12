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
advance, and no complete SQuID-C readiness. Long-term steps 1 and 2 remain open.

- [Fresh native integration](docs/validation/FRESH_NATIVE_INTEGRATION_RESULTS.md)
  now passes: locked new environments, newly built VMEC8.52, fresh W7-X outputs
  from both solvers, and all six scientific tests with zero skips. The extended
  W7-X comparison deliberately retains three failures out of 63 quantities.
- [SLSQP-1024](docs/optimization/DIRECT_SLSQP_1024_RESULTS.md) passes tested
  geometry/native metrics but its refined flux is 12.7 times the limit; its new
  repeats agree internally but fail the historical-prefix requirement.
  [GN-1024](docs/optimization/GN_NATIVE_COVECTOR_RESULTS.md) passes repeat/audit
  checks but remains 24.7 times over the same flux limit. Neither is feasible.
- [Natural-flux AL](docs/optimization/NATURAL_AUGLAG_RESULTS.md): the original
  interrupted study's full first arm and saved 700-bundle second prefix are
  independently verified. The [unchanged recovery](docs/optimization/NATURAL_AUGLAG_RECOVERY_RESULTS.md)
  now passes both full repeats and independent historical-prefix audits;
  all fine holdouts are complete: geometry/native checks pass, flux fails by
  26.99 times. The separate Jacobian-scaling test is fully audited/validated:
  fine flux is11.4% lower but still23.91 times the limit, curvature higher.
  Five separately selected upstream fields now pass independent reconstruction
  but all fail raw flux by about100 times, despite reported clipped zeros.
  A separately qualified first-source start now completes both repeated searches
  and all fine holdouts: geometry/native checks pass, flux still8.955 times too high.
  Subsequent [SLSQP polishing](docs/optimization/SLSQP_POLISH_RESULTS.md) stops
  before optimization at its derivative gate; the independent postmortem confirms
  all nine startup bundles, not a qualified new construction.
  The [disk incident](docs/validation/RESOURCE_INTERRUPTION.md) remains preserved.
- [QI gauge tests](docs/qi/QI_RADIAL_GAUGE_RESULTS.md) reproduce all84 old traces
  but find25 nfp3 families with sign changes under field-line relabeling alone.
  [The full drift/phase transformation](docs/qi/QI_DRIFT_COORDINATES.md) explains
  the interpretation limit; absolute physical drift validation remains open.
  A separate signed-flux check confirms the field orientation, but five poloidal
  identities exceed the fixed tolerance:19/24 grids pass the full screen.
  The [fresh16-cell resolution matrix](docs/qi/QI_FRESH_RESOLUTION_RESULTS.md)
  is now independently audited: doubled solver angular resolution passes all
  sampled identities, but evaluation-refinement and historical-fidelity failures
  prevent overall qualification. No historical data replaced.

Earlier equal-time spatial-residual improvements remain limited to one start and
infeasible fields. A [field-strength audit](docs/optimization/FIELD_STRENGTH_AUDIT.md)
rules out simple mean-field weakening as their explanation; it does not establish SoTA.

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
