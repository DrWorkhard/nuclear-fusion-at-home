# Current verification

Updated 27 September 2026. Latest completed work, not an append-only history.
Git retains previous versions; canonical result pages retain scientific checks
and failed attempts.

## Matched coherent-shape search complete and independently checked

At clean `c1d2260`, both 600-bundle arms complete in 233.572 s worker /
234.478 s supervised. Wider shapes reach fine normal RMS **0.0138430**, 81.80%
below the small-box control with 1.06% more current. All four fine independent
checks and both startup sequences pass; sources remain unchanged. Both searches
exhaust their budgets, so this is not an optimum.

The 15.557 s geometry follow-up uses no native fields. Wider-arm bounds pass:
length ≤2.82955 m, tighter curvature ≤10.1262/m, coil clearance ≥0.0639913 m,
plasma clearance ≥0.112898 m. Control clearance remains unresolved after two
levels, not physically disproven. Supplemental curvature bounds are explicit;
the old loose-curvature flag is not rewritten.

Checks actually performed in the existing `.venv`:

- **46 combined retry/coherent/constrained tests pass** (1.71 s main / 1.49 s
  independent preflight). Source-bound real preflight checks nineteen inputs.
- Independent saved-data audit verifies 45 sources, all 1,200 trial/attempt
  pairs, eight derivative checks, anchors/repeats, boxes, budgets and selections.
- Separate formulas reproduce 48 fine metrics, four full saved-loop fluxes,
  256 B and 256 A comparisons, and all 24 physical curves per endpoint.
- Geometry audit verifies seven source identities, exact snapshots, three
  levels' cover/bound arithmetic, 828 pair bounds, 72 plasma bounds and eighteen
  tighter curvature enclosures. No full distance-grid rerun or interval proof.
- NumPy-scalar serialization control passes before the geometry run. Publication
  and external process-group caps pass; no timeouts or late results occurred.
- **47 public tests pass** (3.417 s); documentation structure and whitespace
  checks pass after updating current summaries.

The [canonical result](../optimization/COHERENT_COIL_EXPLORATION.md) and
[evidence](../../evidence/coherent-coils-exploration-v2.json) retain the exact
questions, execution receipts, sources and complete local file manifest.
The wider RMS is still 138.43 times the acceptance limit. No interior, topology,
pressure, benefit-transfer or engineering acceptance follows from this result.

## Supporting results retained at their point of use

- The initial paired-search failure and thirty-bundle derivative diagnosis remain
  in the coherent-shape report. Additional independent analytic geometry replay
  checks 46,080 curvatures and 5,940 gradient entries; maximum gradient error is
  3.43e-15. The numerical probe change did not alter physical or derivative limits.
- [Independent-current study](../optimization/INDEPENDENT_CURRENT_EXPLORATION.md):
  normalized fits improve RMS modestly but weaken boundary fields. Raw-objective
  fits worsen normalized quality; all field gates remain failed.
- [Public shape52 example](../../submissions/constraint-aware-shape52/README.md):
  evaluation and same-code audit pass; the public current differs from its native
  normalization. This remains an example, not the newly accepted reference.
- [Matched calibration](../optimization/REFERENCE_CALIBRATION.md): thirteen rows,
  156 independently reproduced metrics and 832 field comparisons; no complete
  Goodman positive control.
- [Public release results](../validation/PUBLIC_RELEASE_RESULTS.md) retain exact
  dated portability checks and unverified hosted coverage.

No full native regression, separate-machine replay, hosted CI, external peer
review, release or Step 4 completion is claimed by this record.
