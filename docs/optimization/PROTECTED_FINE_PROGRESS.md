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

## Reviewed archived inputs, numerical bridge and cell integration

Subsequent scoped reviews cover archived intake (130 new tests), the numerical
bridge (73), full geometry composition (111) and cell orchestration (48).
The independent cell/bridge integration run has 121 passes. These are synthetic
tests, not a full-project regression or a fine evaluation of our actual designs.
Source hashes, independent reports and retained failures are in the separate
[bridge review record](../../evidence/protected-fine-bridges-v1.json).

A real **read-only** input check also passes in 18.252 seconds: all 1,004 inline
references / 345 unique files, eight completed coarse-case graphs, active numerical
packages and installed sources, four active Simsopt records, and three historical
registration edges. All eleven historical project-repository records remain
unchanged; current fine provenance is separate. Prior-qualified ancestry behind
pinned historical reports remains byte-bound, not generically re-expanded. The
check performs zero native requests and grants no execution permission.

The bridge constructs each model at the original seed, records its signed
100 kA initializer separately, then explicitly sets and bit-checks the selected
coordinates before diagnostics and flux. Every result retains the selected coarse
current and snapshot. Cell tests compose the actual bridge, fixed ledger and
immutable storage for all eight cases with changed and fallback coordinates.

The geometry tests additionally use the unchanged sampling and independent audit
on synthetic geometry: both 256-square full-torus surfaces, every physical pair,
all four grids, complete witnesses, the original-seed certificate and lossless
mask decoding. Cell-only geometry fixtures test accounting, not those maths.

## Remaining integration and scientific work

The saved-field and full-graph components now also pass reciprocal internal
review: 147 field-audit tests and 75 graph-audit tests, **222 passing** in each
independent rerun. The graph audit checks all 225 journal records, exact work
ordering and all 28 new raw archives. The numerical audit reconstructs eight
initializer scalars, six metric rows and eighteen flux grids; all five refinement
comparisons and 63 flux checks remain mandatory. Threshold failures are complete
negative results; inconsistent data raises an error. Tests include a deliberately
nonphysical real core/graph/field-interface composition and preserve failed test
setup/assertion attempts. See the [audit review record](../../evidence/protected-fine-audits-v1.json).

An additional **actual saved-data** replay reconstructs all eight previously
recorded original-seed initializer fluxes at 256 coil and 256 loop nodes. The
largest relative discrepancy is **6.514979e-16**, below the unchanged 5e-10 limit
with zero absolute slack. It confirms the signed 100 kA convention using the
independent direct kernel. It performs no native request, new selected-candidate
evaluation or 512-node fine initialization; it is not fine acceptance.

Complete and review the closed execution-source gate, worker and study launcher.
Require complete regression, committed qualification and a committed execution
checkpoint before any fine native call. An archived-input check or saved-seed
replay alone is never a substitute for that gate.

Then execute every registered diagnostic, flux and geometry check for all eight
fixed states. A correctly reconstructed threshold failure is a valid negative
result, not a reason to omit later checks. Only that evidence can determine fine
numerical qualification and absolute field/geometry acceptance. Neither outcome
alone establishes resolved improvement, realized plasma benefit, Step 4 or MS1.
