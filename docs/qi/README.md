# Plasma physics

The completed [Step 3 vacuum study](../steps/README.md#step-3-vacuum-plasma-diagnostic) improved one
bounce-action diagnostic. It does not establish global QI, confinement, finite
pressure or transfer into an actual coil field.

Completed plasma/QI production pipelines and detailed qualifications are
[frozen in Git](../validation/REPRODUCING_RESULTS.md). Their target data and
evidence remain available; small field-grid helpers needed by active coil checks
remain in the source tree. Current transfer requirements are on the
[Step 4 page](../steps/STEP_4_PLASMA_AND_COILS.md).

[ConStellaration metrics](CONSTELLARATION_METRICS.md), 11 October 2026: scored with
`constellaration==0.2.6`, the improved Step 3 target shows no measurable change in
the L∇B coil-simplicity proxy compared with reference401 (−0.026%). Neither target
is feasible for any of the three benchmark problems.

[Route A scoping for #114](ISSUE114_ROUTE_A_SCOPING.md), 15 October 2026: near selected401, vacuum well
and mirror ratio can be repaired, but flux compression floors at 1.06–1.09 (bound 0.9) and pushing it costs QI.

[Plasma scorecard](PLASMA_SCORECARD.md): full metric rows and benchmark-bound
verdicts for the two registered targets, with unscored historical inputs and
remaining qualification work explicit.

[Radial sensitivity](PLASMA_RADIAL_SENSITIVITY.md): ns99/ns199 changes QI by
1.1–1.5%, less for the other three metrics, with no benchmark-bound crossing.

The [scorecard](PLASMA_SCORECARD.md#recorded-boundary-attempt-25-october-2026) also
records the rejected first design and N21’s frozen-model VMEC nonconvergence.

[Seeded dataset comparison protocol](SEEDED_DATASET_COMPARISON.md): prospective
twelve-metric compatibility rule for the three fixed #112 rows; native execution
still requires a frozen launcher and a current resource handoff.
