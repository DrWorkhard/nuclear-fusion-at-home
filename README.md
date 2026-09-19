# Fusion Baselines

Reproducible research on stellarator coil optimization, independent physical
validation and a future SQuID-C baseline. W7-X is the physics/software regression,
StellCoilBench/LPQA the method benchmark, and open Goodman configurations the QI bridge.

## Research overview

Start with [the project overview](docs/README.md), [current assessment](docs/STATUS.md)
and [work plan](docs/PROJECT_PLAN.md). They are written for scientific review.
Detailed protocols, results and the research journal are indexed one level below.

Current assessment, 2026-09-19: **steps 1, 2 and the registered vacuum scope of
step 3 are complete.** Steps 1/2 qualify the bounded local W7-X/Goodman regression
and LPQA fixed-surface filament workflow.
The [consolidated acceptance and runbook](docs/validation/FOUNDATION_ACCEPTANCE_RESULTS.md)
record 720 tests, six mandatory scientific regressions without skips, exact two-run
24-bundle iteration, independent audits and all four candidate holdout phases.
This qualifies the workflow, not a better/feasible design or SQuID-C readiness.
All earlier studies are preserved at tag `foundation-pre-scope-2026-09-13`
(`5971fee`). Broader QI, engineering and performance research remains deferred.
The subsequently authorized [plasma-boundary optimization](docs/qi/PLASMA_BALANCED_RESULTS.md)
now delivers a changed Goodman-nfp2 vacuum boundary: **11.1700% lower relative
bounce-action variance on the finest registered domain**, plus4.8506% narrow
training gain. All ten final gates pass, including local action guards, exact cold
repeat, source/action audit, field/contour/tracer checks and all20 refinements.
The first design remains [rejected and preserved](docs/qi/PLASMA_OPTIMIZATION_RESULTS.md).
This is a bounded numerical design improvement, not measured confinement, global
QI, a feasible coil design, SoTA or power-plant performance. Both domains informed
the follow-up construction; finer independent admission is not blind generalization.
After handoff, the user explicitly authorized step4. Its
[options and three independent agent reviews](docs/optimization/COUPLED_DESIGN_OPTIONS.md)
prioritize paired actual-coil realization before coupled plasma/coil iterations.
The [completed first coil pilot](docs/optimization/COUPLED_COIL_PILOT_RESULTS.md)
remains negative: all six admitted128-call searches fail fine physical admission,
with1.8–6.7mm plasma clearance against80mm required and only17/30 refinements passing.
The subsequent [clear-initialization study](docs/geometry/CLEAR_COIL_INITIALIZATION_RESULTS.md)
now passes independent geometry admission for **all twelve actual coil sets**:
168 LP calls,84 exact repeats,72 direct clearance checks. The selected shaped
starts for both six/eight-base-coil classes retain at least98.2mm certified plasma
clearance, with length/curvature/pair-distance limits unchanged. This is a
geometry-only result; no magnetic fields were evaluated. Next is a separately
registered, better-resolved field fit from the accepted starts.
No field-qualified coil design or completed step4; pressure, realized-field physics, finite geometry and
robustness remain required subpackages. No automatic step5 or SoTA claim.

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
- Latest complete software regression: 1,172 tests pass with 334 documented warnings
  (144 fixture warnings and 190 explicitly retained solver-option forwarding notices);
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
