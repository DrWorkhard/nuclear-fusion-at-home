# Conditional space constraints exclude some scaled coil copies

**Decision: supplement reactor-oriented design choices with finite-envelope
constraints; do not interpret the existing filament fit as a reactor design.**
A desk screen of frozen trial 427 from the scale035 coupling study
completed on 7 October 2026. This advances the [early screen](REACTOR_FEASIBILITY_SCREEN.md)
without establishing the coupled operating point still required by #27.

Let λ scale all centerlines and the plasma surface, and κ multiply the magnetic
field. Equivalent ampere-turns scale as `I = |I0| λκ`. Assume circular winding
radius `r = sqrt(I/(π J))`, casing allowance c and uniform casing-to-plasma gap g.
The two conditions are `λ d_plasma ≥ r+c+g` and `λ d_coil ≥ 2(r+c)`.
Casing and gap stay fixed in metres. λ is also the scaled R(0,0) coefficient in
metres here; κ is a multiplier, not a field value in tesla.

[Stellaris Table 8](https://publikationen.bibliothek.kit.edu/1000179851/172386752)
motivates J=112–124 A/mm² for the whole winding pack and g=1.04 m.
Its packs are square; our circular model is an assumption, not a conservative
enclosure. Transferring its density/gap does not establish their adequacy here.
Casing allowances 0, 0.05 and 0.10 m are explicit scenario choices.

For **J=120 A/mm², c=0.05 m, g=1.04 m**:

| Length scale λ | Field ×4 | Field ×6 | Field ×8 |
| --- | --- | --- | --- |
| 6 | Excluded | Excluded | Excluded |
| 8 | Unresolved | Excluded | Excluded |
| 10 | Clears two checks | Clears two checks | Clears two checks |
| 12 | Clears two checks | Clears two checks | Clears two checks |

An upper-clearance-bound failure excludes a scenario; both lower bounds passing
clears only these two checks. Otherwise it is unresolved. For κ=6 the transition
is bracketed by **8.1983–9.4177**. At λ=10 the winding radius is 0.22136 m,
excitation **18.4719 MA-turns**, and lower plasma/inter-coil margins are
0.07413 / 0.12624 m. Across all 108 cases, 45 are excluded, 12 unresolved and 51
clear these checks. All λ=6 cases are excluded; the grid counts are not probabilities.

Saved bounds use padded floating point, not interval arithmetic. Scaling leaves
the filament-model RMS **0.0019663**, still failing; finite-pack fields are untested.
Every scaled excitation exceeds the unchanged 0.5 MA pilot cap. No gate is relaxed.
Self-clearance, supports/access, attainable current density/peak field, stresses,
neutron shielding/breeding, pressure/confinement, net power and exhaust remain
unqualified. Larger size clearing two inequalities is not reactor feasibility.

Clean arithmetic producer/evaluator: `532f3b72302ecb75a857072beae1816cbdbee4de`;
original geometry producer: `56fd845f2ff84553092ac1690aa430283e14acdf`,
geometry archive: `8a200dae194fc972ee535ad8532525aa17aff749`.
Local archive: `328f9b461431ac36a0f6b7add1e91a07891397aa`; annotated tag
[evidence-issue27-envelope-v1](https://github.com/DrWorkhard/nuclear-fusion-at-home/tree/evidence-issue27-envelope-v1), tag object
`7adfb3d1fdf1ff64bd9603201dce1faa992a3bd2`; published; remote identities and manifest retrieval verified. It preserves the 92,360-byte
raw result, original inputs, exact assumptions, command and completed script/tests.
The 12-entry manifest SHA256 is
`1b25e35d40760898c83ee1c9a0204b71bda18b253e47cdbb447ec1133e497da9`.
One 30 s / 2 MiB calculation took 0.0334 s with 3/2 GiB disk reserves; no native
environment changed. Independent 50-digit Decimal replay, repeated for this integration, checks all 108 cases
and five source bindings, agreeing within 5.57e-16 normalized arithmetic error.
It does not recalculate geometry, validate source physics or re-attest timing.
Paper identity, external availability and reproduction are recorded in the archive.
Agent review is not external physics peer review.
