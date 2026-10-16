# Plasma physics

The completed [Step 3 vacuum study](../steps/README.md#step-3-vacuum-plasma-diagnostic) improved one
bounce-action diagnostic. It does not establish global QI, confinement, finite
pressure or transfer into an actual coil field.

Completed plasma/QI production pipelines and detailed qualifications are
[frozen in Git](../validation/REPRODUCING_RESULTS.md). Their target data and
evidence remain available; small field-grid helpers needed by active coil checks
remain in the source tree. Current transfer requirements are on the
[Step 4 page](../steps/STEP_4_PLASMA_AND_COILS.md).

[Unapproved plasma-requirements proposal](PLASMA_REQUIREMENTS.md): static JSON
for the #113 owner decision, with hard bounds, preferences/objectives and explicit
unresolved items. No optimizer or acceptance check consumes this draft.

[ConStellaration metrics](CONSTELLARATION_METRICS.md), 11 October 2026: scored with
`constellaration==0.2.6`, the improved Step 3 target shows no measurable change in
the L∇B coil-simplicity proxy compared with reference401 (−0.026%). Neither target
is feasible for any of the three benchmark problems.

[Route A scoping for #114](ISSUE114_ROUTE_A_SCOPING.md), 15 October 2026: near selected401, vacuum well
and mirror ratio can be repaired, but flux compression floors at 1.06–1.09 (bound 0.9) and pushing it costs QI.
