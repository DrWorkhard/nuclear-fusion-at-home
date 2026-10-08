# Engineering scope

Screen reactor feasibility now: device scale, magnetic field and pressure,
net power balance, winding/blanket/shield space, loads, heat exhaust and maintenance.
Record assumptions and missing evidence before detailed simulations. Start with the
[early feasibility screen](REACTOR_FEASIBILITY_SCREEN.md): specified pilot inputs,
missing operating assumptions and the cheapest rejection checks. The completed
[conditional envelope screen](ISSUE27_ENVELOPE_SCREEN.md) excludes some scaled
copies under explicit winding/gap assumptions, while leaving the operating point
unestablished. The
[programme](../optimization/STEP4_RESEARCH_PROGRAMME.md) defines the decision this
screen supports; a boundary-error threshold alone does not establish readiness.

Reuse established community tools when a specific design decision requires
finite-build, load or manufacturing-response analysis. Historical mesh/FEM code,
environment manifests and reports resolve through
[reproduction](../validation/REPRODUCING_RESULTS.md).
Filament geometry checks are not engineering qualification.
