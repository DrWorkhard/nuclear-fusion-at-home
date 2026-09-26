# Protected coil-fit pilot: coarse results

26 September 2026. [Scientific registration](PROTECTED_COIL_FIT_PROTOCOL.md) ·
[Method review](PROTECTED_METHOD_REVIEW.md) ·
[Execution qualification](PROTECTED_PILOT_EXECUTION_RESULTS.md) · [Index](README.md)

## Result and scope

**All eight registered native searches and independent coarse audits completed.**
Every case lowers its own objective and both reported RMS field errors while
retaining the original cumulative geometry certificate. Normal RMS decreases
0.4463–0.4857%; inner-vector RMS decreases 1.1881–2.1916%. These are reconstructed
coarse-grid changes, **not resolved fine-grid gains or physical acceptance**.
Normal RMS remains 0.26794–0.27478 against 0.0001; interior RMS remains
0.35727–0.36405 against 0.01. Step 4A–4D and MS1 remain open.

| Case | Selected normal RMS | Change | Selected inner-vector RMS | Change | Accepted steps |
| --- | ---: | ---: | ---: | ---: | ---: |
| reference-n6-N | 0.274721637 | -0.4817% | 0.363286325 | -2.1269% | 17 |
| reference-n6-V | 0.274710365 | -0.4857% | 0.363258118 | -2.1345% | 14 |
| reference-n8-N | 0.267946316 | -0.4470% | 0.357274742 | -1.1881% | 12 |
| reference-n8-V | 0.267936144 | -0.4508% | 0.357267014 | -1.1903% | 12 |
| selected-n6-N | 0.274782097 | -0.4806% | 0.364049605 | -2.1827% | 16 |
| selected-n6-V | 0.274771314 | -0.4845% | 0.364016550 | -2.1916% | 17 |
| selected-n8-N | 0.268007487 | -0.4463% | 0.357990644 | -1.2301% | 16 |
| selected-n8-V | 0.267997682 | -0.4499% | 0.357982069 | -1.2325% | 13 |

“Selected” in the case label means the Step 3 plasma target, not a winning method.
Changes compare each case with its own search seed. N and V objectives differ and
are not ranked against each other. Their own objective decreases span
6.3127–9.1611%; that larger percentage must not be substituted for field-error gain.

## What stopped the searches

All eight terminate `certificate-limited`: their next descent direction fails
certification at all 16 registered backtracking lengths. Every field-evaluated
search proposal was accepted; no current or Armijo rejection occurred. Across the
matrix: 117 accepted proposals, 582 geometry rejections. The last rejected
certificate in every case fails **only its curvature upper-bound gate**.

Selected coarse sampled maximum curvatures are 9.4877–9.6664/m, while the cumulative
continuous bounds approach the unchanged 12/m limit. This suggests conservatism
worth investigating, but sampled values do not prove the between-node maximum or
a tighter continuous certificate. An upper bound exceeding 12/m does not prove
the true curvature violates 12/m, and a blocked direction is not an optimum.

The first six-coil reference N case illustrates why metrics stay separate:
objective falls 9.16%, normal RMS 0.48% and interior RMS 2.13%. Its independently
reconstructed geometry penalty is zero at both endpoints; boundary field RMS
changes from 1.28635 to 1.23369 and current from 294.966 to 283.050 kA, with the
registered flux normalization retained. This is not a fixed-current comparison.

## Execution and verification

- Clean source checkpoint `2015ac5e6f79600497aafc731dbcc444c2a43962`.
  Runtime source admission and canonical manifest round-trip pass in 24.754 s.
- The serial launcher exits zero and explicitly returns the complete study
  summary. Source-before and source-after are byte-identical: SHA-256
  `0aaf8eb998a96f59426d21a5d55e37551d9e350e80879776dc930ac50988224d`.
  No tracked edits, environment sync or competing heavy job during execution.
- Actual work: **16 model initializations, 213 full bundles, 795 certificates,
  1,933 native requests**, below 2,320 construction requests. No equilibrium solve.
  All eight parent acknowledgements and separate saved-physics reports are retained.
- Independent reconstruction checks all 795 certificates, including 582 negative
  proposals, all 213 bundles and 64 recorded/reconstructed startup-direction checks.
  Sampled direct B/A: 1,278 statistics, 81,792 vectors, 245,376 scalar components;
  largest relative discrepancy **1.803858e-15**, limit 5e-10.
- Exact original-seed repeat and fresh-model selected-state replay pass. This is
  not a second execution of each complete search trajectory or verification of
  every full-grid field value and every gradient component.
- The qualified software's preceding full regression has 3,487 passes and 334
  existing warnings. Native success does not resolve the documented netCDF4 warning.
- A separate internal post-run review verifies 11,602 files / 488,174,792 bytes,
  including all 213 raw archives, 16 journal streams / 8,144 chained records and
  819 checkpoint-prefix heads. It confirms counts, deltas and certificate reasons;
  no additional physics, array-loading audit or full historical-source admission
  was run by that review. Its hash-bound report is linked from the evidence record.

[Machine-readable evidence](../../evidence/protected-coil-fit-coarse-v1.json)
binds the returned summary, full case graphs, source checkpoint and diagnostic
values. Raw immutable evidence remains in `artifacts/protected-coil-fit-v1/`;
live notes are explicitly separate from acceptance evidence. Internal independent
reviews are not external peer review.

## Required next work

**Update:** the mandatory fixed-candidate fine study has now completed at
`e0ac3f7`; all eight pass numerical and geometry checks, all fail field limits.
See the separate [fine results](PROTECTED_FINE_RESULTS.md). The following records
the required follow-up at the coarse checkpoint; no coarse data or selection changed.

Run the original separate fine phase for **all eight fixed selections**: six
field/interior grids, two complete flux blocks, four direct geometry grids,
sampled B/A and original-seed certificates, with selected coarse currents frozen.
The [fine registration](PROTECTED_FINE_PROTOCOL.md) now defines the reviewed
implementation task. Implementation and execution must be separately qualified; fine results
cannot alter this completed selection.

Only afterward consider a separately registered tighter curvature proof or
geometry-aware directions under unchanged physical limits. Neither small coarse
gains nor a finished negative pilot closes realization/transfer 4A, coupled
improvement 4B, pressure/confinement 4C or finite-build robustness 4D.
The [local-bound proposal](../geometry/LOCAL_CURVATURE_BOUND_OPTIONS.md) is planning
only and does not change any preserved certificate decision.
