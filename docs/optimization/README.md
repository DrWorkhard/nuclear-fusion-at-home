# Active coil research

The working method is **penalized normalized coil fitting**, followed by separate
fine-grid field and continuous-geometry checks. Best checked exploratory normal
RMS is **0.004889**, against a 1e-4 pilot limit. No accepted reactor design or
Step 4 completion follows.

## Current documents

- [Coherent-shape results](COHERENT_COIL_EXPLORATION.md): matched comparisons,
  best candidates, geometry limits and retained failures.
- [Interior-field screen](INTERIOR_FIELD_EXPLORATION.md): five fixed snapshots;
  best interior RMS 0.04029, 73.66% below its matched control but above 0.01.
- [Boundary calibration](REFERENCE_CALIBRATION.md): QUASR/LPQA component controls
  and why metric conventions matter.
- [Research programme](STEP4_RESEARCH_PROGRAMME.md): next decisions, trade-off
  map and open-benchmark route.
- [Research hints](RESEARCH_HINTS.md): useful contributions, not an allowlist.

## Executable path

The latest completed fit is `scripts/explore_coherent_restart.py`; its explicit
source-bound inputs and settings reproduce the recorded comparison in the native
environment. It reuses the normalized model, construction penalties and fine
checker in `explore_normalized_coils.py` / `explore_constrained_coils.py`.
The completed `screen_coherent_interior.py` is a fixed-snapshot field diagnostic,
not another optimizer.

The acceptance mathematics live in `coupled_coil_audit.py`,
`clear_coil_geometry_audit.py`, `curvature_bounds.py` and
`boundary_control_metrics.py`. Use these shared checks; do not create a new
checker for every optimizer. Historical filenames do not imply retired physics:
these retained routines are active dependencies.

The latest reproduction command is:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 MKL_NUM_THREADS=1 \
  python scripts/explore_coherent_restart.py --output artifacts/my-restart
```

It requires the recorded local snapshots and the [native environment](../validation/ENVIRONMENT.md).
It is not the portable public starter. Existing studies retain their exact
budgets. Future exploration uses a declared wall-clock/resource ceiling and
adds search bounds only for a stated scientific comparison.

## Frozen methods

Certified-step search, current-only fitting and completed LPQA/plasma/engineering
pipelines are removed from the main branch. Their full code, tests and reports
resolve at the [freeze tag](../validation/REPRODUCING_RESULTS.md).
Their failures remain scientific evidence; they are not active maintenance work.
