# Protected cell: synthetic integration qualification

Registered 26 September 2026 after [component qualification](PROTECTED_RUNNER_RESULTS.md)
at `d130fff`, before the integrated cell implementation. The original search and
resource limits remain unchanged. [Method clarifications](PROTECTED_METHOD_REVIEW.md)
apply; this is a software integration study, not a native field experiment.

## Fixed sequence

Use one source-described cell, an original geometry seed and its admitted geometry
report, exact named coordinates, historical seed bundle and immutable source
references. A dependency-injected adapter supplies model initialization,
certification and field-bundle calculation; this stage has no native default,
process launcher, network or equilibrium solver.

1. Persist the context's source/identity metadata. Initialize the main model at
   the original seed through the qualified ledger.
2. Compute ten registered low-mode startup bundles, each following a positive
   original-seed certificate and explicit cache invalidation. Compare the first
   complete numerical bundle exactly with the historical seed, and the last with
   the first. Run the recorded-value derivative screen; this is not yet independent
   physical reconstruction.
3. Certify and freshly evaluate the search seed on the same model, then compare
   it exactly with the initial seed bundle.
4. Run the unchanged controller. Its journal retains exactly the controller's
   event schema. Native/ledger events use a separate journal. Trial certificate
   and bundle IDs use the proposal index, preserving gaps after geometric rejection.
5. Resolve selection only to the fresh search seed or an accepted trial. Construct
   the one replay model at the original seed, certify/evaluate selected coordinates
   and compare the full numerical bundle exactly. This is not a second search path.
6. Publish immutable checkpoints/result references with both externally bound
   journal receipts and all operation manifests. No physical/Step 4 flag turns true.

## Data contract

Coordinate identity is SHA-256 of canonical JSON `{schema_version:1,names,x}`;
phase, filenames and operation IDs are excluded. Coefficients have exact canonical
ordering and preserve inactive original-seed bits. Bundle state has exactly the
controller's `x/value/gradient/metrics` keys; its snapshot must retain original seed,
target, normalization and physical-copy mapping. Finite overcurrent trial values
are valid evaluation results for the controller to reject, not malformed data.

Each certificate manifest identifies case, phase, operation, coordinates/hash,
original seed reference, geometry audit reference/index and complete certificate.
Each bundle manifest identifies case, phase, operation, complete state, snapshot
reference, array reference and certificate reference. Arrays/snapshot are persisted
before their manifest, which precedes ledger completion acknowledgement. Historical
arrays keep their original checked loader; do not rewrite or force them into the
new canonical archive encoding.

Before any replay equality comparison, require all sixteen exact finite real arrays:
boundary points/normals/B/A `(4096,3)`, weights `(4096,)`; inner points/target/B/A
`(3072,3)`; loop points/tangents/A/B `(256,3)`; physical coil positions/tangents
`(4*nbase,256,3)` and currents `(4*nbase,)`. Require consistent snapshot/state
coordinates, names, method, source identities, signed physical currents and metrics.
This schema check cannot replace independent physical field/geometry calculations.

### Controller certificate representation (pre-execution clarification)

During implementation, read-only inspection found that representative saved
n6/n8 full certificates occupy about 82/135 KB each. Copying 116 of these into
the controller's final event could exceed the qualified 8 MiB record limit.
Keep that limit and the controller unchanged: persist each complete certificate
in its manifest, then return a controller view containing exactly `status`,
`calculation_complete`, `certified` and `certificate_reference`. The three flags
must equal the referenced full result. Independently check this linkage, including
case, original seed, state and proposal identity. This uses the controller's
existing extensible certificate contract; no proof data is discarded. Exercise
the full 116-proposal budget with this representation before qualification.

## Failure and qualification controls

Test both coil classes and methods, completed synthetic paths, selection/replay
routing, coordinate/name/source mutations, every missing/wrong-shaped raw array,
wrong snapshot/current identities and false completeness assertions. Retain
certificate rejection, overcurrent/Armijo rejection and budget-stop semantics.

Inject guard, certificate, native, array/snapshot/manifest, journal and checkpoint
failures, including swallowed callback errors. Any such failure poisons the whole
cell; no later callback dispatch. Successful prefixes and partial failed tails
remain. A frozen completed-trajectory audit must accept real synthetic histories
and reject mutations, while keeping all physical-verification flags false.

Run focused tests, independent internal review, public/docs/Ruff checks and full
regression; commit and bind sources/results. Native source revalidation, wall-time/
disk/process enforcement, independent physical reconstruction and fine-grid
acceptance are subsequent prerequisites. A synthetic cell pass is not a native
runner qualification or evidence of improved coils.
