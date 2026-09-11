# Batched qualification output failure — 2026-09-11

The first attempt at 44e3435 completed the first state's computations and saved
`artifacts/spatial-flux-batched-v1/original.npz`, then failed while serializing the
report: a NumPy boolean from the new flux check is not accepted by json.dumps.
The exception-path report failed for the same reason. No completed qualification
JSON was produced and the second physical state was not reached. Do not call
this attempt a passing qualification or invent its unretained timing data.

Correct the report boundary by explicitly converting every check value to a
Python bool. No numerical formula, tolerance or input is changed. Preserve the
first attempt's raw files and use new `spatial-flux-batched-v1-retry1` output paths
for a complete rerun of both physical states and all three timing repetitions.
