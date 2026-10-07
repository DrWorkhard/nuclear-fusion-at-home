# Engineering scope

Screen reactor feasibility now: device scale, magnetic field and pressure,
net power balance, winding/blanket/shield space, loads, heat exhaust and maintenance.
Record assumptions and missing evidence before detailed simulations. Start with the
[early feasibility screen](REACTOR_FEASIBILITY_SCREEN.md): specified pilot inputs,
missing operating assumptions and the cheapest rejection checks. The
[programme](../optimization/STEP4_RESEARCH_PROGRAMME.md) defines the decision this
screen supports; a boundary-error threshold alone does not establish readiness.

Reuse established community tools when a specific design decision requires
finite-build, load or manufacturing-response analysis. Historical mesh/FEM code,
environment manifests and reports resolve through
[reproduction](../validation/REPRODUCING_RESULTS.md).
Filament geometry checks are not engineering qualification.

The [conditional finite-envelope screen](ISSUE27_ENVELOPE_SCREEN.md) tests
whether scaled copies of the latest coils can satisfy two declared separation
requirements, without promoting filament geometry to reactor qualification.
