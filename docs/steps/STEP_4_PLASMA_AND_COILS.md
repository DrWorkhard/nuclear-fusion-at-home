# Step 4: plasma and coils together

**In progress.** Updated 27 September 2026.
[All steps](README.md) · [Roadmap](../PROJECT_PLAN.md) · [Scientific status](../STATUS.md)

## What the step has to show

The required chain is ideal plasma target → actual coils → realized field
surfaces/topology → preserved plasma benefit. A favorable vacuum field fit alone
does not complete Step 4.

| Package | Required evidence | State |
| --- | --- | --- |
| 4A — Realization and transfer | Coils for reference and Step 3 targets pass numerical, geometry and field checks; realized-field topology and plasma benefit verified | In progress; absolute field limits fail |
| 4B — Coupled improvement | Actual coupled plasma/coil improvement against coil-only controls, independently accepted | Open |
| 4C — Pressure and confinement | Validated finite-pressure/current response and realized-field confinement diagnostics | Open |
| 4D — Finite geometry and robustness | Qualified winding/build/load models and manufacturing-perturbation response | Open |

Detailed method choices are in [coupled design options](../optimization/COUPLED_DESIGN_OPTIONS.md).
The [scientific status](../STATUS.md) is the canonical current result summary.

## What the experiments taught us

The [first coil pilot](../optimization/COUPLED_COIL_PILOT_RESULTS.md) failed:
fine evaluation exposed only 1.8–6.7 mm plasma clearance where coarse sampling
looked much better. Preserve that negative result. The subsequent
[initialization study](../geometry/CLEAR_COIL_INITIALIZATION_RESULTS.md) found
twelve geometry-admissible starts, but their
[magnetic fields](../optimization/CLEAR_COIL_FIELD_START_RESULTS.md) remained
far from the target. Geometric validity and field fidelity are separate problems.

[Cumulative perturbation bounds](../geometry/COIL_PERTURBATION_RESULTS.md)
made local movement checkable. The
[protected search](../optimization/PROTECTED_COIL_FIT_RESULTS.md) then found
small improvements in eight cases before hitting a conservative curvature bound.
[Fine validation](../optimization/PROTECTED_FINE_RESULTS.md) retained all
absolute field failures. A tighter
[whole-path curvature check](../geometry/LOCAL_CURVATURE_RESULTS.md)
certified two previously rejected steps under unchanged limits, and the
[matched field comparison](../optimization/FIXED_FIELD_PROBE_RESULTS.md)
confirmed small normal-error gains. This proves useful movement for two steps,
not a generally effective search or a path to feasibility.

## Current decision, not another automatic search extension

The [strategic review response](../review/STRATEGIC_REVIEW_RESOLUTION.md)
prioritizes gate calibration and exploration of achievable field/geometry
trade-offs. The [saved residual diagnosis](../optimization/FIELD_RESIDUAL_RESULTS.md)
is complete: observed responses align much better with the raw objective than
normalized field error. The [matched boundary calibration](../optimization/REFERENCE_CALIBRATION.md)
now demonstrates low refined RMS on QUASR and reproduces LPQA's reported mean/max
under tested conventions. It supports an objective comparison, without claiming
a matched positive control for all Goodman gates.
A reviewed one-step continuation proposal remains optional. No further long
protected search is justified merely by the recent small gains.

The [matched objective experiment](../optimization/NORMALIZED_OBJECTIVE_EXPLORATION.md)
now completes: local-normalized fitting lowers fine RMS to 0.18779 versus raw
0.20869, but uses more current and both endpoints violate curvature. The raw
endpoint also violates plasma clearance. The [static start screen](../optimization/COIL_START_SCREEN.md)
then finds more curvature room in circles, but no better initial field. The next
[constraint-aware comparison](../optimization/CONSTRAINED_COIL_EXPLORATION.md)
tests stronger penalties and low-order freedom, not relaxed acceptance limits.

The [research programme](../optimization/STEP4_RESEARCH_PROGRAMME.md) owns
calibration, decision windows, the open challenge and MS0. No gate or historical
verdict changes with this reprioritization.

## Tools and detailed evidence

Software qualifications support the experiments; they are not additional
scientific milestones. Their complete reports remain available:

- [Search controller](../optimization/PROTECTED_SEARCH_SOFTWARE_RESULTS.md),
  [storage](../optimization/PROTECTED_RUNNER_STORAGE_RESULTS.md),
  [execution components](../optimization/PROTECTED_RUNNER_RESULTS.md) and
  [method review](../optimization/PROTECTED_METHOD_REVIEW.md).
- [Integrated cell](../optimization/PROTECTED_CELL_RESULTS.md),
  [native plumbing](../optimization/PROTECTED_NATIVE_PLUMBING_RESULTS.md),
  [saved-physics checker](../optimization/PROTECTED_PHYSICS_RESULTS.md) and
  [pilot launcher](../optimization/PROTECTED_PILOT_EXECUTION_RESULTS.md).
- [Fine pipeline qualification](../../evidence/protected-fine-qualification-v1.json),
  [fixed field qualification](../../evidence/fixed-field-probe-qualification-v1.json) and
  [completed residual analysis](../optimization/FIELD_RESIDUAL_RESULTS.md).

The last recorded full research regression passed 5,654 tests at its stated
implementation; it is not a regression of every later edit.
Required protocols, source identities and scientific evidence remain available;
superseded overviews and progress diaries are recoverable through Git. There is
still no demonstrated transfer of the Step 3 benefit into an accepted coil field.
