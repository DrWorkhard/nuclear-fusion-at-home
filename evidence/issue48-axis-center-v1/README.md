# Axis-center sensitivity of the saved continuation failure

The local periodic center shifts by 0.256506 mm for the continuation and
0.076997 mm for the original reference401 fit. At both refined centers, every
failed-case residue sequence still reverses once on both planes; four controls
have no reversals. Its pooled gap changes from 1.240256 to 1.247492 rad.
This specific center correction does not remove the reconstruction problem.
No label was recomputed or requalified; no dynamical classification follows.

Clean successful producer/evaluator: `5a0d06303a2d0405f52e0f179176bc2ada532536`.
Its one numerical attempt finished in 6.776873 s supervised total. Native package
identities (1,662 files), source/input identities and owned-process cleanup passed.
The 240 s driver allowance starts after imports; the 270 s outer allowance
includes startup/finalization. One thread, 256 MiB, 3/2 GiB reserve, 5 s clock
discrepancy limit. All numerical settings were frozen before calculation.

`raw/v1` preserves the 1.700 s import failure at producer
`daff62fbce104b7d48b0210be1f899a69f49bc33`: no field/root calculation began.
Version 2 only fixes native import availability and plotting-cache configuration.
`raw/v2` holds its complete original output. External original directories remain
`/private/tmp/issue48-axis-center-v1` and `...-v2`; neither was altered.
Analytic controls are pre-run test evidence in `metadata/`, not driver controls.

The snapshot keeps original code/protocol/tests at their normal paths. `inputs/`
holds exact consumed subsets of archives `191875d231b396e5960cbd9460a37a6c462b6381`
and `2ee186bb347245072c98d983a42b06f8e02a16a9`, including coil snapshots and five
saved point sets. Their original manifests retain entries outside these subsets.
Each attempt has a source-binding map; the two changed v1 files are retained in
`metadata/failed-producer/`. The native environment is recorded, not distributed.
No Wout is needed. Everything remains local-only, unpublished and remotely unverified.

## Replay and reproduction

With NumPy/SciPy, from a fresh shallow archive checkout:

```bash
python evidence/issue48-axis-center-v1/replay.py --manifest-sha RECORDED_MANIFEST_SHA256
```

This checks all payload/source identities and exactly replays the five cases,
two centers and 220 residue sequences using stored centers and the same kernels.
It does not repeat periodic-root solves, native fields, long trajectories or timing.

For the numerical run, use a clean checkout of successful producer `5a0d063`,
the preserved native Python and one-thread environment. Run
`scripts/run_axis_center.py --config CONFIG --config-sha SHA256 --output FRESH_PATH
--revision 5a0d06303a2d0405f52e0f179176bc2ada532536`. The original config and exact
command/environment are preserved in `metadata/` and `raw/v2/start.json`.
For relocated inputs, set config `archive` and `reference_archive` to this payload's
`inputs/continuation` and `inputs/reference401`, and `supervisor`/`environment` to
the corresponding recorded metadata files; hash and retain that new config.
Environment verification requires the recorded native installation identities.
Do not pass the archive commit off as the clean producer. A repeated run is a new
reproduction attempt and must retain its own outputs and limitations.

Resolved fixed points do not establish axis uniqueness/stability, contour
qualification, islands, nestedness or confinement. Agent review is not external
physics review.
