# Fixed field probe: prospective method and input review

26 September 2026. [Protocol](FIXED_FIELD_PROBE_PROTOCOL.md) · [Index](README.md)

## Decision

Two independent internal planning reviews support a small diagnostic comparison
of the newly certified proposals with their immediate predecessors. No new fields,
bounds, gradients or optimizer were run. Registration permits implementation and
qualification, not native execution before its separate checkpoint. It does not
establish external peer review, physical admission or Step 4 completion.

The four states and six grids give exactly 24 original-seed models, **168 native
requests / 804,864 point requests**. The independent saved-data checks include 24
initializers, 24 metric rows, 144 B/A statistics / 9,216 vectors, 20 refinements
and 24 diagnostic loop-flux checks. The full historical flux/geometry acceptance
schedule is deliberately outside this diagnostic.

## Corrections incorporated

- Clear the value cache once per model, never between snapshot, metrics and
  arrays. The coarse calculation stays unfrozen throughout; calling frozen
  diagnostics afterward would add three prohibited native requests.
- Preserve existing sampled geometry penalties and the full objective. The
  exclusion concerns additional acceptance-geometry jobs, not arithmetic needed
  by the unchanged evaluator and independent metric reconstruction.
- Use the exact original search scalar and saved Armijo RHS, not a replay or
  almost-identical bundle value. Tolerance checks reconstruction; the decision
  itself has no added slack. Report current separately.
- Normalize every state on the coarse grid, retain its new snapshot and freeze
  that current for refinement. Compare controls against historical numerics;
  never mix old and new normalizations or treat baseline currents as proposal data.
- Keep original refinement checks separate from the new, conservative empirical
  margins. Each gain label requires complete reconstruction and data coverage.
  Normal/interior errors have distinct labels, with maximum-error/current trade-offs.
- Require both states' six diagnostic loop fluxes to meet the existing 1e-6
  relative target tolerance before either gain label. Frozen current alone is
  insufficient; this uses existing arrays and does not claim full flux qualification.

Reviewer `local_curvature_review` inspected method, APIs, saved runtimes and work
counts; `curvature_audit_redteam` independently reviewed scientific inference and
requested the matched-flux prerequisite. The retained long review is
`artifacts/local-curvature-v1/FIELD_PROBE_REVIEW.md`. Final registration adds
navigation, exact manifest binding, formatting and explicit normalization/search
scalar semantics already recommended there, without changing grids or margins.

## Input identity

The [manifest](../../evidence/fixed-field-probe-inputs-v1.json) is a byte-identical
copy of the frozen metadata selector output: 378,385 bytes, SHA-256
`4997daf18d1ec5d94e1e6fd73f74e2a9ca8a83d269986241fdf64fb80c456699`.
Its ordered indices are 2, 10, 4, 11 in the curvature input manifest. All four
geometry parent/index chains and 112 producer plus 112 audit curve references
are bound. The two proposals still have no field bundle or measured current.

Selector checks rehash 294 files / 48,375,383 bytes with scientific imports
blocked; repeat output is byte-identical and five tampering controls reject.
Retain the initial selector row-versus-whole-report failure and correction.
Main independently rehashes the same files, checks all four named hashes and
coordinate bits, and reconstructs direction, active update and Armijo context.
The controls are exactly accepted predecessors 93→94 and 49→50, not inferred
from the final selection label. Original RHS values are 0.03574020711548009 and
0.03304822327847573. The old source graph is preserved; fresh runtime/native
admission remains a separate requirement.

Implementation, independent code review, focused/full regression and the separate
committed execution checkpoint remain. No numerical result has been selected
or a success rule adjusted using new field observations.
