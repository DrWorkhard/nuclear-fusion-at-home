# Prospective fixed-target recording, version 2

Question: can new fixed-target runs retain the missing settings, costs and solver
iterates needed by [#64](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/64)?
The existing fitter and read-only exporter now do so. No plasma trajectory or
joint-run qualification is implied; those require the joint optimizer in #39.

## Recording and export

`fit_coils.py` writes `inputs.json.recording.format = fusion-coil-recording-v2`
before model construction. `--task-id` names the experiment; its default is
`fixed-target/<target>`. Metadata records objective weights, penalty thresholds,
selection limits, boundary/coil/geometry grids, resource ceilings and the fixed
target/current policy. Named coils, target flux/B² and input/source hashes retain
their existing seed/provenance locations. The objective and selection rules stay
unchanged; fine verification remains separate.

Each terminal trial adds `elapsed_s` and `elapsed_scope`: monotonic wall time in
`model.evaluate` plus its post-evaluation guard, including native progress writes
but excluding the surrounding trial writes. Failed work is timed too. An
interruption retains the attempt without a terminal file or invented cost.
Startup/model preparation and final checking remain outside this per-trial cost;
the existing aggregate times remain available. No equilibrium cost is inferred.

L-BFGS-B's callback writes `iterate-<index>.json` without reevaluation. Exact
coordinates matching the latest returned search evaluation give an evaluation
link; otherwise it records a null link. A callback means solver acceptance only,
even if that evaluation returned a numerical-failure penalty. Other trials remain
`unknown`, not presumed line-search rejections. Solver acceptance, successful
evaluation, final candidate selection and physical acceptance are distinct.

```bash
python scripts/export_coil_trajectory.py --run results/my-fit \
  --output results/my-trajectory.jsonl --max-mib 64
```

The exporter automatically emits `fusion-coil-trajectory-v2` for prospective runs.
It adds recorded settings/costs and `solver_iterate` rows linked to candidate IDs,
validating coordinates, trial roles, indices and callback counts. Unknown links
have null candidate IDs. Historical runs keep the [v1 schema](COIL_TRAJECTORY_V1.md)
and bytes; missing values stay null. Closed-run input and callback hashes bind
the run identity. Source files remain read-only; failures retain partial exports.

## Reproduction and limits

With the preserved [native environment](../validation/ENVIRONMENT.md), set all
four documented native thread variables to `1`, then run from a fresh checkout:

```bash
mkdir -p results
PYTHONPATH=src python -m pytest -q tests/test_coil_fit.py tests/test_coil_trajectory.py \
  --basetemp results/recording-v2-fresh
```

Use a **new** basetemp path: pytest clears an existing one. The controlled v2
example is produced by `test_prospective_control_records_real_interruption_after_callback`:
11 completed evaluations, one failed trial, one interrupted attempt and a linked
callback. A separate real SciPy test checks failed-trial backtracking. The native
fixed-target control permits one optimizer iteration within 60 seconds, exports
its records and exactly replays the selected objective, gradient and metrics
from the saved seed and committed reference input. It requires no ignored Wout.

Recording adds two clock reads per terminal evaluation, timing fields (about
130 bytes per trial in the controls), run metadata and one coordinate-bearing
file per callback (about 2.6–5.4 kB at order 5 in these controls). No extra objective
calls are made. Latency overhead is not benchmarked; extra writes consume the
existing wall-clock budget and can change how many trials finish. The shared
256 MiB output ceiling, disk reserves and failure-preserving stop behavior apply
to callback files too; export retains its separate 64 MiB default ceiling.

These are software and fixed-target replay checks, not physical acceptance.
Joint plasma coefficients, changing equilibrium/target identities and split
equilibrium costs remain unimplemented until that execution path exists. #64
and #38 remain open for that integration and its bounded native replay.
