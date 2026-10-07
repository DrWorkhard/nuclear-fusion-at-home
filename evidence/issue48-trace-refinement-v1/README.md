# Independent-integrator check of two continuation traces

Both frozen comparisons pass. Maximum paired crossing differences are
7.850939 micrometres for failed launch 10 and 8.217908 micrometres for control 8,
below the prospective 10-micrometre ceiling. All 22 failed-case residue sequences
retain one reversal; all control sequences retain zero. The failed pooled gap
changes from 1.240256 to 1.240183 rad. This supports reproducibility of two finite
traces, not topology, contour qualification, confinement or benefit transfer.
The original continuation grid remains unqualified at 19/20.

Clean producer/evaluator: `6323ba683698ab55ab00b8f3d8778b5b6e6fb348`.
The code, tests and prospective protocol remain at their original paths. One
attempt completed in 161.562568 s supervised total. Limits: 600 s inside the
driver after imports / 630 s including startup/finalization, one thread, 256 MiB,
3/2 GiB disk reserves, 5 s clock discrepancy. Source/input and 1,662 native package
file identities matched before/after; owned-process cleanup passed.
Original raw output (138,701 bytes) remains untouched at
`/private/tmp/issue48-trace-refinement-v1` and is copied exactly under `raw/`.
Pre-run analytic controls/checks and adversarial review are retained in metadata.

The comparison changes integrator/parameterization, coil quadrature and numerical
settings together: original native compute_fieldlines used 512 nodes/tol=1e-10;
new SciPy DOP853 R,Z maps use 1024 nodes, rtol=1e-11, atol=1e-13, max step pi/100.
Both use native Biot–Savart fields. Existing independent filament fields agree at
five predetermined new crossings per launch to less than 1.99e-16 on scale
max(1,|B|). No full independent-field trajectory or continuum error bound is claimed.

`inputs/` contains exact consumed subsets from archive
`191875d231b396e5960cbd9460a37a6c462b6381`: manifest, report, snapshot and two NPZs.
Its original manifest still lists files outside this subset. Every direct source
binding resolves through `metadata/source-bindings.json`. The recorded native
environment is external; no Wout is required. Everything remains local-only,
unpublished and remotely unverified.

## Replay and numerical reproduction

From a fresh shallow archive checkout with NumPy/SciPy:

```bash
python evidence/issue48-trace-refinement-v1/replay.py --manifest-sha RECORDED_MANIFEST_SHA256
```

This verifies all identities and exactly replays paired crossing errors, 88 residue
sequences, gaps and both decisions using the same NumPy kernels and saved arrays.
It does not rerun either integrator, native fields, environment or historical timing.

For a new numerical reproduction, use a clean source checkout at `6323ba6`, the
preserved native Python and one-thread settings. The full command/environment is
in `raw/start.json`; run `scripts/run_trace_refinement.py --config CONFIG
--config-sha SHA256 --output FRESH_PATH --revision
6323ba683698ab55ab00b8f3d8778b5b6e6fb348`.
The original config is retained in metadata. For relocated inputs, set `archive`
to this payload's `inputs` and `supervisor`/`environment` to their recorded metadata
files, then hash and retain the new config. The supervisor requires the recorded
native installation identities. Do not pass the archive revision off as producer.
Retain every reproduction attempt, including incomplete or differing outcomes.
Agent review is not external physics review.
