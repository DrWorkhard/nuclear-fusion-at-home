# Conditional space screen before reactor-oriented optimization

Question, 7 October 2026: which scaled versions of the latest frozen scale035
coil geometry can be rejected by two finite-envelope separation requirements?
This desk calculation advances one missing input of the
[reactor screen](REACTOR_FEASIBILITY_SCREEN.md), not a complete operating point.
Use the [paired fit's](../optimization/ISSUE37_FIT_COUPLING_RESULT.md) trial 427,
its already checked geometry, exact boundary input and fixed physical mapping.
No new equilibrium, field, geometry or power simulation is required.

Define homothetic length scale λ and magnetic-field multiplier κ. Biot–Savart
scaling requires equivalent ampere-turns `I = |I0| λ κ`. Assume uniform circular
winding cross-section `r = sqrt(I/(π J))`, plus a casing allowance c. J is the
engineering current density of the whole winding pack, not of the conductor.
The assumed uniform casing-to-plasma separation is g. Require
`λ d_plasma ≥ r+c+g` and `λ d_coil ≥ 2(r+c)`.

[Stellaris Table 8](https://publikationen.bibliothek.kit.edu/1000179851/172386752)
reports winding-pack densities 112–124 A/mm² and a smallest casing-to-plasma gap
of 1.04 m. It uses square packs: our circular equivalent-area model is an
assumption, not a conservative enclosure of those packs. Neither the cited gap
nor its transferable current density is a universal reactor requirement.

Evaluate λ = 6, 8, 10, 12; κ = 4, 6, 8; J = 112, 120, 124 A/mm²;
c = 0, 0.05, 0.10 m and g = 1.04 m. Casing/gap values stay fixed in metres;
only the centerlines and plasma surface scale. Saved lower bounds and padded
sampled upper bounds bracket both clearances. An upper-bound failure excludes
that scenario; both lower bounds passing clears only these two checks; otherwise
it is unresolved. Compute the critical scale interval algebraically.

The [one-off script](../../scripts/screen_reactor_envelope.py) must complete in
30 s with 2 MiB output and 3/2 GiB initial/live reserve, preserving input/code
hashes and failures. Use the standard library only; the native environment stays
unchanged. Review source, units and interval logic before execution.

Normalized field errors are unchanged by scaling and still fail. All scaled
currents must be reported against the existing pilot cap; this screen does not
relax it. Even clear separation leaves coil self-overlap, supports, access,
attainable current density/peak field, neutron shielding, stresses, pressure,
confinement, net power and exhaust unqualified. An excluded circular envelope
is not a rejection of all reactor designs or joint optimization.
