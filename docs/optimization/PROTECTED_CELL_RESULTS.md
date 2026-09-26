# Protected cell: integrated synthetic workflow

26 September 2026. [Registration](PROTECTED_CELL_PROTOCOL.md) ·
[Component qualification](PROTECTED_RUNNER_RESULTS.md) · [Index](README.md)

## Assessment

The complete injected startup → search → selected-design replay workflow is
implemented and **299 focused synthetic checks pass** (179 contract, 54 cell,
66 saved-graph audit). Independent internal review
has exposed and helped correct integration defects. **Synthetic integration
qualification is complete:** committed implementation `c17123a` passes the full
2,918-test regression, and source/artifact identities are bound below.

No native field search was performed. Existing source files, numerical limits,
controller policy and qualified storage/ledger implementations remain unchanged.
Synthetic fields are deliberately nonphysical: software completion is not
physical acceptance, a better coil design, Step 4 completion or MS1 evidence.

## Interfaces and evidence boundaries

- `protected_cell_contract`: exact eight-case context, original seed/named
  coordinates, complete 17-field snapshot, 19 metrics and all 16 raw arrays.
  Seven fixed grid/target arrays must be byte-identical to the supplied historical
  reference. Active coefficients may change; inactive seed bits may not. Finite
  overcurrent trials are valid records for the controller to reject.
- `protected_run_cell.run_cell`: injected adapter, guard, snapshot store and two
  distinct journals. Ten startup bundles, fresh search seed, unchanged controller
  and one fresh-model selected replay. Every certificate and numerical bundle has
  an immutable manifest; checkpoint receipts bind the acknowledged prefixes.
- `protected_cell_audit.audit_cell`: read-only file/hash/schema, cross-manifest,
  checkpoint-prefix and native-accounting checks, plus the separately authored
  scalar controller audit. It imports neither the cell producer nor the ledger.
   Structural and exact-replay primitives are shared, including transitive imports
   of controller primitives; this is not an independent
  physical reconstruction or new source authentication.

The historical context must be admitted by the separate source binder before any
native use. The synthetic geometry-report fixture and zero field arrays cannot
serve as physical evidence. The auditor retains explicit false flags for fields,
gradients, certificate truth, source admission and physical/Step 4 acceptance.

Final result publication is the terminal commit boundary; no fallible guard runs
after it. A supervisor must bind the **returned** result reference externally.
An I/O failure can leave files on disk, including a result-shaped tail: discovering
such a file or recomputing its hash is not proof that execution returned successfully.
Graph-integrity checking cannot supply missing execution acknowledgement.

## Tests and independent review

The contract's 179 checks pass. A separately preserved read-only compatibility
probe accepts all eight real historical seed contexts, rejects 72 identity
mutations and retains eight finite-overcurrent synthetic trial schemas. It hashes
28 individual input references. It does not rerun the complete source admission
graph or perform native field, geometry-certificate or equilibrium calculations.

Integrated controls exercise both coil classes and methods, null direction,
geometry rejection, current rejection, Armijo rejection, gaps in proposal IDs,
the 20-field and 116-certificate limits, exact startup/seed/replay gates and failure
at adapter, guard, journal, raw-data and checkpoint boundaries. The graph auditor
checks accepted and negative completed histories and rejects inconsistent links,
missing/extra/reordered manifests, wrong receipts and false scope/completeness flags.

Three agents supplied bounded contributions/reviews: `protected_budget_impl`
implemented the cell; `protected_runner_map` reviewed the contract against saved
native data; `cell_integration_review` independently reviewed integration and
audit. The maintainer implemented the contract and separate graph auditor.
These are internal reviews, not external peer review.

### Defects retained and corrected

1. **Fixed-input substitution / false seed initialization.** Initial contract
   allowed target-array replacement despite unchanged source labels, and checked
   claimed seed coordinates rather than the initialized live state/cache. Red run:
   171 passes/eight failures. Explicit fixed-array identity and actual model state/
   empty-cache checks repair both; 179 pass, independently rechecked.
2. **Large certificate duplication.** Read-only size inspection found that copying
   116 full certificates into the final controller event could exceed the existing
   8 MiB cap. Before integration execution, clarified the representation: preserve
   each complete certificate once, and put its hash-bound decision view in the
   unchanged controller. A full-budget synthetic test retains 140 KB proofs while
   keeping the search report below 2 MiB; the auditor checks every reference/flag.
3. **Ineffective invalidation / post-publication guard.** Independent review found
   that a no-op invalidator was only counted, and a final guard could fail after
   publishing a completed result. Red run: 51 passes/two failures. Require an empty
   cache before bundle dispatch and make final publication terminal.
4. **Malformed archive exception.** A correctly hash-bound but CRC-corrupt NPZ
   raised `BadZipFile` instead of returning a failed audit verdict. The one-test red
   reproduction is retained; the new audit boundary handles this exception without
   changing the qualified storage reader.
5. **Wrong live model after computation.** The returned bundle could match the
   request while the actual model coordinates differed. Retain the red run (53
   passes/one failure); verify the live coordinate schema/hash/bits before
   publication. All 54 cell tests now pass. This is a routing consistency check,
   not proof that the claimed field arrays were calculated correctly.

All development JUnit files and both compatibility-probe versions remain under
`artifacts/protected-cell-v1/`. The first probe's eight lint findings (seven
immediately invoked loop lambdas and one long line) are retained in its unchanged
script; the separately identified v2 script passes lint. Initial uncommitted
development source bytes are not retrospectively identified by the final commit.
The public suite passes 47 tests (3.755 s), and docs/Ruff/whitespace checks pass.
The initial shell check used unavailable `python`; rerunning with `python3`
succeeded. A documentation-test command named a nonexistent test file and collected
zero tests; its JUnit remains, followed by the corrected explicit test selection.

## Committed-source qualification

Registration `88fd4d6`, implementation `c17123a`: **2,918 passed, 334 existing
warnings, zero failures/errors/skips**, exit zero. Console time 260.63 s; JUnit
time 259.701 s. Both complete outputs are retained. The native environment was
not changed, and the checkout was clean before and after the full one-thread run.
This is a local regression, not hosted CI or an independent-machine reproduction.

The [qualification record](../../evidence/protected-cell-synthetic-v1.json) binds
19 source files and 22 artifacts, including the failed development controls,
eight-context compatibility probes and full regression. The separately authored
final review rerun passes all 299 tests (20.034 s JUnit); all three reviewed source
hashes match the committed implementation. Source hashes match their Git versions.
The certificate representation clarification was written before the first
integration execution but committed with implementation, not in a separate
pre-execution commit; both the original and effective protocol identities remain.

## Remaining gates

Next: a source-bound native adapter and
process/resource supervisor, independent physical reconstruction and runtime
derivative checks, then the registered diagnostic search and separate fine-grid
acceptance. The method review's limits on claiming fine-resolved improvement
remain. No later 4A transfer, 4B coupling, 4C pressure/confinement or 4D engineering
requirement is discharged by these software checks.
