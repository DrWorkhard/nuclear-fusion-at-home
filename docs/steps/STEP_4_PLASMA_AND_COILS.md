# Step 4: develop plasma and coils together

**In progress, 27 September 2026.** A better plasma target must be realized by
practical coils and retain its benefit in their magnetic field.
[All steps](README.md) · [Roadmap](../PROJECT_PLAN.md) · [Status](../STATUS.md)

## Completion requirements

| Package | Required result | Status |
| --- | --- | --- |
| 4A — Realization and transfer | Accepted coil fields/geometry, verified magnetic surfaces and transfer of the Step 3 benefit | Open; active focus |
| 4B — Coupled improvement | Independently accepted plasma/coil improvement against coil-only controls | Open |
| 4C — Pressure and confinement | Validated finite-pressure/current response and realized-field confinement diagnostics | Open; detailed work deferred |
| 4D — Finite geometry and robustness | Qualified winding/build/load models and manufacturing-perturbation response | Open; detailed work deferred |

Deferring detailed work is not completing it. Revisit the deferred physics once
a coil set reaches within 10× of the boundary RMS limit.

## Current result

The [longer-fit comparison](../optimization/LONGER_COIL_EXPLORATION.md) reaches
normal RMS **0.004713** with scoped geometry passing. Its wider-box endpoint
reaches **0.001948**, but continuous length bounds remain **unresolved**.
Both fail boundary RMS 1e-4 and maximum normal error 1e-3.

The wider endpoint passes the interior-vector component: **0.009770** against
0.01 on all three checked grids. This is a component success, not acceptance
of the whole design. Construction now needs length headroom, without changing
the 3.5 m acceptance limit. The 1e-2 exploratory signal supports continued work.
All these coil fits use the original reference401, not the improved Step 3
target. Realized magnetic surfaces, confinement and benefit transfer remain open.

## Lessons retained from closed work

The first coil pilot failed fine clearance checks (1.8–6.7 mm). Better starts
solved scoped geometry, not field fidelity. Certified small-step search gained
little: its objective aligned poorly with normalized acceptance error.
Current-only freedom did not close the gap. Normalized fitting with geometry
penalties and coherent shape changes has been more productive so far.

These failures and their original protocols are preserved at the
[freeze tag](../validation/REPRODUCING_RESULTS.md), not maintained as active
search infrastructure. No historical result or threshold is rewritten.

## Tools and detailed evidence

Use the [active fitting path](../optimization/README.md) and its existing
fine-field and continuous-geometry checks. The
[boundary calibration](../optimization/REFERENCE_CALIBRATION.md) supplies a
positive component control, not a complete Goodman acceptance control.

The [programme](../optimization/STEP4_RESEARCH_PROGRAMME.md) owns next experiments
and the October decision. Keep exploration records short; check the best two or
three candidates before making claims. Software checks are recorded separately
in [current verification](../logbook/VALIDATION_LOG.md).
