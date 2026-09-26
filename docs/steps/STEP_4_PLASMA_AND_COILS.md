# Step 4 results so far: plasma and coils together

**In progress.** Results through 26 September 2026. The detailed reports are
mostly in German; this page summarizes them in English and links each one.
The detailed reports and evidence files remain authoritative.
[All steps](README.md) · [Roadmap and next actions](../PROJECT_PLAN.md) · [Status](../STATUS.md)

## What the step has to show

A plasma target is only useful if real coils can produce its magnetic field and
the produced field keeps the plasma benefit. The missing chain is: ideal plasma
surface → real coils → the field those coils actually make → that field's
surfaces and physics. A small field error on the desired surface alone does not
close this chain, and a favorable vacuum coil fit does not complete Step 4.
Step 4 consists of four work packages:

| Package | What it requires | State |
| --- | --- | --- |
| **4A — Realization and transfer** | Realize both the reference and our Step 3 plasma with actual coils; pass the numerical, geometry and field gates; then check field surfaces/topology and whether the plasma benefit survives | In progress: certified coil geometry and qualified field calculations exist, but field errors fail by a large factor |
| **4B — Coupled improvement** | Compare coil-only controls with genuine coupled plasma/coil changes, and independently accept an actual improvement; a proposed optimizer or predicted gain is not enough | No study registered yet |
| **4C — Pressure and confinement** | Qualify finite-pressure/plasma-current and realized-field assumptions, with response/refinement and confinement diagnostics; vacuum targets and first-order drift tests are not enough | No study registered yet |
| **4D — Finite geometry and robustness** | Qualify winding, build and load assumptions and actual manufacturing/perturbation responses, keeping absolute physical limits | No study registered yet |

The [method options and reviews](../optimization/COUPLED_DESIGN_OPTIONS.md) (German)
explain why paired coil realization comes first and which coupled methods follow.

## Results in order

### 1. First actual-coil pilot — all six designs rejected (14 September)

Coils were fitted for the reference and our Step 3 plasma, with 6 or 8 base coils
and two objectives. Six of eight start qualifications passed (both 8-coil
reference starts failed); all six searches completed and were independently
audited. **All six were physically rejected:** normal-field RMS 0.113–0.288,
inner vector RMS 0.73–1.09, sampled curvature above the 12/m limit, and only
17 of 30 refinement pairs stable. The key finding: coarse sampling had shown
35–52 mm plasma clearance, but fine sampling found only **1.8–6.7 mm against the
required 80 mm**. Geometry therefore needs certified continuous bounds, not samples.
[Detailed report](../optimization/COUPLED_COIL_PILOT_RESULTS.md) ·
[evidence](../../evidence/coupled-coil-pilot-v1/)

### 2. Coil starts with certified clearance — all twelve pass (19 September)

Twelve registered coil sets (6 or 8 base coils; circular or shaped; 100, 140 or
180 mm offset) were built by linear programs, without field evaluations. All
twelve pass independent geometric acceptance against unchanged limits: coil
length ≤ 3.5 m, curvature ≤ 12/m, coil–coil distance ≥ 60 mm and plasma
clearance ≥ 80 mm. Selected by a rule fixed in advance: `n6-shape-d100mm` and
`n8-shape-d100mm`, with certified plasma clearance of at least 98.414 mm and
98.214 mm. The bounds are conservative floating-point bounds, not interval proofs.
[Detailed report](../geometry/CLEAR_COIL_INITIALIZATION_RESULTS.md) ·
[audit](../../evidence/clear-coil-initialization-v1-audit.json)

### 3. Magnetic field of these starts — numerically qualified, physically far off (19 September)

Four cells (reference and Step 3 plasma × 6 and 8 base coils) pass complete
independent numerical qualification: eight derivative screens, all 20 grid
refinements (largest difference 0.0195% against 1%), 768 direct field/potential
comparisons (largest 5.3e-15 against 5e-10) and 252 flux gates. Physically, all
four fail only the three field-error limits; current, length, curvature and
clearances pass.

| Plasma / base coils | Normal RMS | Normal max | Inner vector RMS | Current (kA) |
| --- | ---: | ---: | ---: | ---: |
| Reference / 6 | 0.2761 | 0.5980 | 0.3712 | 294.97 |
| Reference / 8 | 0.2691 | 0.6015 | 0.3615 | 216.63 |
| Step 3 target / 6 | 0.2761 | 0.5979 | 0.3722 | 295.68 |
| Step 3 target / 8 | 0.2692 | 0.6016 | 0.3624 | 217.16 |
| **Limit** | **0.0001** | **0.001** | **0.01** | **500** |

The normal-field error is about 2,700 times its limit and the inner vector error
about 36–37 times. The public starter's coil set is derived from the reference
with 6 base coils. [Detailed report](../optimization/CLEAR_COIL_FIELD_START_RESULTS.md) ·
[audit](../../evidence/clear-coil-field-start-v1-audit.json)

### 4. How far coils can move while staying certified (20 September)

To let a later search change coil shapes without losing the geometry guarantee,
a 52-state matrix tested small cumulative perturbations of both selected coil
sets. Both seeds, their repeats and all twelve smallest (1e-5) signed probes are
certified; 30 of 48 changed probes are certified overall. Largest certified tested
radius: 1 mm along smooth damped directions (both coil sets); 0.1 mm (6 coils)
and 0.01 mm (8 coils) for a single high mode. The 18 uncertified probes are
conservative negative bound decisions, not proven violations.
[Detailed report](../geometry/COIL_PERTURBATION_RESULTS.md) ·
[audit](../../evidence/coil-perturbation-v1-audit.json)

### 5. Protected-search controller — software qualified (24 September)

The controller for a geometry-protected field fit and a separate trajectory
auditor pass 108 synthetic tests. This makes the next search auditable; it does
not run a search or improve a field.
[Report](../optimization/PROTECTED_SEARCH_SOFTWARE_RESULTS.md) (English) ·
[evidence](../../evidence/protected-search-software-v1.json)

### 6. Durable event storage for the search runner — software qualified (25 September)

A fail-closed, hash-linked event journal records every controller event before it
is acknowledged; 155 focused tests pass together with the controller and auditor.
The full-regression report records 2,229 passes with no failures/errors/skips;
source and artifact identities are bound. This qualifies single-writer POSIX
storage, not the remaining native-budget/source orchestration or physical audit.
[Report](../optimization/PROTECTED_RUNNER_STORAGE_RESULTS.md) (English) ·
[protocol](../optimization/PROTECTED_RUNNER_STORAGE_PROTOCOL.md) ·
[evidence](../../evidence/protected-runner-storage-v1.json)

### 7. Execution components and second method review — software qualified (26 September)

Source admission, exact work accounting, immutable raw snapshots and startup/replay
helpers pass 390 synthetic tests after independent internal review found and
helped correct budget reentry, storage-allocation and startup-check defects.
Component qualification is complete: full regression passes 2,619 tests and the
new source-admission check passes against all eight saved seed bundles. The
integrated native worker and physical audit remain pending.
The second method review conditionally supports a bounded diagnostic pilot; it
does not approve native execution yet. [Results](../optimization/PROTECTED_RUNNER_RESULTS.md) ·
[Method review](../optimization/PROTECTED_METHOD_REVIEW.md).

### 8. Integrated protected cell — synthetic qualification complete (26 September)

The startup/search/replay chain now has complete numerical boundaries and a
separate saved-graph/accounting auditor. Focused tests and independent internal
review cover rejection, both budgets, exact replay and injected failures.
Read-only schema checks accept all eight historical seeds; no new native coil
search ran. All 299 focused tests and the 2,918-test full regression pass;
19 source files and 22 artifacts are hash-bound. Native process/resource
supervision and independent physical reconstruction remain separate gates.
[Results and retained defects](../optimization/PROTECTED_CELL_RESULTS.md).

### 9. Native plumbing — software qualification complete (26 September)

The source-bound native bridge and isolated parent/worker connection are now
implemented. All eight synthetic cases pass the complete subprocess and graph
audit path; injected source/thread changes and a nonzero exit after return cannot
produce a parent acknowledgement. Independent review has corrected control and
adapter defects. At `fd069e9`, all 315 focused tests and 3,233 full-regression tests
pass; all eight actual saved contexts and source-bound adapters validate without
native work. Thirteen sources and 28 artifacts are bound. Independent physics
reconstruction is registered next; no new native search has run.
[Report](../optimization/PROTECTED_NATIVE_PLUMBING_RESULTS.md).

## What is not shown yet

No coil set whose field meets the limits, no check that the Step 3 benefit survives
in a coil-produced field, and no coupled, finite-pressure, confinement or
robustness result. Numerical qualification means the calculations are
trustworthy, not that the design is acceptable. The next actions for 4A are in the
[roadmap](../PROJECT_PLAN.md).
