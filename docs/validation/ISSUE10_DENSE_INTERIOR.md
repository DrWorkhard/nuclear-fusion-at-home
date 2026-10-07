# Qualify portable dense interior targets

**Decision:** can contributors evaluate new six-coil candidates against both
frozen #25 targets without native equilibrium libraries? The cheapest test is
an exact target export followed by scalar field recomputation of both frozen
fits. This is numerical portability, not a new fitting or benefit claim.

The [new packet](../../examples/clear-coil-interior-v1/README.md) copies all
12,288 Cartesian target positions and vectors per target from published archive
`05a4511084912fea9bd8d03e81f01018882396b8`, original clean producer/evaluator
`a551289e63e44d7dbae7b5d5a0e5f4b6026db257`. It verifies the full published manifest.
New manifest SHA256: `9f9b32ffb6176b22e149069896500da0ac1aa0c371b5f17be7fa7603ebfb2ccb`.
Native intake contracts and existing public fixed-current reports remain unchanged.

Before running the qualification, freeze code, packets, expected controls and
these rules. From a fresh shallow checkout, use `python -I -S` to run
`scripts/qualify_dense_interior.py` separately for reference401 and selected401.
The exporter requires NumPy; the resulting packet/checker do not. The controls
contain the exact original native fields, original currents and dense metrics.
Bind each control's SHA256 explicitly in the command.
Reference control: `f59bd03f03c126db1820766be831e02da4e64767a15aedcfa0c8b2beedd456f8`;
selected control: `caa78f10048a4c5c920116dbd1c42d34a8ae267084ebdad5cb72844a6018b1f8`.

Each arm gets one attempt, at most 600 s including startup/IO, 32 MiB output,
3 GiB initial / 2 GiB live disk reserve and 5 s wall/monotonic clock agreement.
Checks run between 128-point field batches. Retain failures; no changed threshold
or rerun to convert failure to success. A code defect may justify a new version.
Do not overlap heavy jobs; this is not a throughput comparison.

Acceptance of this **numerical qualification** requires both controls to recover
their original signed current magnitudes within 1e-12 relative, all 12,288 native
field vectors within 1e-10 relative maximum-component error, and aggregate plus
three surface RMS values within 1e-10 absolute. Both original interior failures
must remain failures. Controls are not optimization targets or hidden holdouts.

The scalar public field implementation is independent of native SIMSOPT, but
uses the same frozen target data and quadrature conventions. This does not test
arbitrary-candidate convergence, geometry, realized surfaces, particle confinement,
native Wout regeneration or physical acceptance. No field gate is relaxed. Record
the exact tested revision and evidence archive here after the run; no completed
qualification is claimed by this prospective record.
