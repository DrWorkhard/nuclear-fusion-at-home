# Inconclusive bounded local eleven-period search

The single attempt stopped at its frozen neighborhood guard. After five completed
return-map evaluations, the sixth root trial moved about 53.17 mm from the seed,
outside the 10 mm neighborhood. It was rejected before field evaluation at that
point. No periodic point, refined result, matrix or linear classification was
obtained. This establishes neither presence nor absence of an island or resonance.
The original continuation qualification remains 19/20.

Clean producer/evaluator: `50e6243685af6e504cd48aab03501a0c709016f0`.
One unsuccessful attempt took 6.683277 s supervised total, below its 300 s driver
after imports / 330 s outer ceilings. Other limits: one thread, 256 MiB, 3/2 GiB
disk reserves and 5 s clock discrepancy. The unsuccessful receipt confirms process
cleanup. It does not claim successful completion or post-run identity checks.
A separate read-only post-failure check verified all 55 direct source/input
bindings and 1,662 recorded native package files; its receipt is in metadata.
No numerical retry, changed neighborhood or alternative seed was attempted.

Code/protocol/tests remain at their original paths. All original raw files remain
untouched at `/private/tmp/issue48-periodic-return-v1` and are copied under `raw/`.
`inputs/` contains exact consumed subsets of archive
`d12b01bedbb3d4e89ab891d03a9e6048f0690918`: manifest, snapshot, refined trace and
report. Its manifest includes other entries not copied here. The data-informed
seed averages the first eleven-residue sequence of the failed refined phi=0
crossings. No confirmatory holdout claim is made. Input/source maps, pre-run tests
and adversarial review, configuration, command and environment identity are saved.

## Verification and reproduction

With NumPy, from a fresh shallow archive checkout:

```bash
python evidence/issue48-periodic-return-v1/replay.py --manifest-sha RECORDED_MANIFEST_SHA256
```

The replay verifies payload/source identities, exactly recomputes the saved seed,
and checks all six trial statuses and the guard distance. Replay success means
that the failed record is consistent, not that the scientific search succeeded.
It does not repeat field maps, root solving, derivatives, environment or timing.

For numerical reproduction, use a clean checkout of producer `50e6243`, the
recorded native Python and one-thread settings. The actual command/environment
is in `raw/start.json`: `scripts/run_periodic_return.py --config CONFIG
--config-sha SHA256 --output FRESH_PATH --revision
50e6243685af6e504cd48aab03501a0c709016f0`.
The original config is in metadata. Relocation requires setting its `archive`
to this payload's `inputs`, and `supervisor`/`environment` to the recorded metadata
files; hash and retain the new config. Native installation identities remain
external and are checked. No Wout is needed. Do not confuse archive and producer
revisions; retain any new reproduction attempt separately.

Everything remains local-only, unpublished and remotely unverified. No claim of
periodic-orbit absence, topology, nonlinear stability, contour qualification,
confinement or benefit transfer follows. Agent review is not external peer review.
