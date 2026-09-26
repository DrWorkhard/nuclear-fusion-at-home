# Fixed-candidate fine validation: implementation progress

26 September 2026. [Registration](PROTECTED_FINE_PROTOCOL.md) ·
[Coarse results](PROTECTED_COIL_FIT_RESULTS.md) · [Index](README.md)

The eight coarse selections remain unchanged. **Fine native execution has not
started.** This page separates completed software work from the still-required
numerical and physical checks. Step 4 remains In progress.

## Reviewed components

The fixed schedule, geometry-mask codec, dispatch ledger and separate process
boundary have independent internal review and **726 passing synthetic tests**
(670 new tests plus 56 existing storage controls). The final reviewed report has
zero failures, errors or skips; JUnit time is 6.983 seconds. Source and test-artifact
identities are retained in the [scoped review record](../../evidence/protected-fine-components-v1.json).
This is not full integrated qualification or authorization to launch native work.

- The plan binds all eight cases, explicit N/V method, original-seed model grids
  and complete selected coordinates, including their signed-zero bits.
- The ledger requires eight model initializations and 24 operations in order:
  exactly 80 native requests and 552,960 queried points per case. It rejects
  omitted, duplicated or misordered work and records raw publication before
  completion. Swallowed callback failures permanently stop the cell.
- The codec changes only the boolean curvature mask to canonical uint8 storage;
  other numeric arrays retain dtype, shape and element bytes. It does not itself
  verify complete geometry or physical truth.
- The separate supervisor requires a single explicit returned reference, valid
  source/configuration/process bindings, single-thread settings, exit zero and
  owned-process-group cleanup. Scientific acceptance flags remain false.

Tests use synthetic fields and real nonphysical subprocesses, not new native
magnetic calculations. Retained negative controls exposed six plan/codec cases,
two late thread-drift cases and two terminal-publication clock cases; fixes and
successful reruns are retained alongside the failures. In particular, a slow
final write may leave a file but cannot return an acknowledged result after the
1,800-second deadline. The stored acknowledgement timestamp explicitly precedes
terminal persistence; the returned reference additionally requires the final
clock check to pass.

## Remaining integration and scientific work

Complete the archived-source intake, original-seed/selected-state native bridge,
geometry sampling, saved-data audit and cell/launcher integration. Recheck the
entire coarse input graph without rebinding its historical repository metadata
to today's commit. Current fine implementation provenance is a separate layer.
Require independent review, complete regression, committed qualification and a
committed execution checkpoint before any fine native call.

Then execute every registered diagnostic, flux and geometry check for all eight
fixed states. A correctly reconstructed threshold failure is a valid negative
result, not a reason to omit later checks. Only that evidence can determine fine
numerical qualification and absolute field/geometry acceptance. Neither outcome
alone establishes resolved improvement, realized plasma benefit, Step 4 or MS1.
