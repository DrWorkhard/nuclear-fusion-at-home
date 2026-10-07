# Early reactor feasibility screen

**Decision: continue bounded magnetic-field research; defer reactor-scale search.**
A coupled power-plant operating point is missing; neither viability nor impossibility
is established.
[Issue #27](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/27) remains
open until the missing inputs below support a numerical continue/change decision.
Assessed source: `3a7ba6d`; desk analysis only.

## What is specified

The [reference input](../../evidence/plasma-design-v2/reference-input-401.json)
has two field periods, boundary Fourier coefficient R(0,0) = 1 m,
edge flux π/100 Wb and `pres_scale = 0`. These describe a vacuum model,
not a fueled operating point. The [headroom candidate](../../submissions/length-headroom-six-coil/README.md)
uses 24 filaments at approximately 0.308 MA equivalent current each; this is
ampere-turn excitation, not a specified conductor current or winding pack.
Its 0.13307 m plasma-to-filament clearance bound excludes vessel, blanket,
shield, structure and coil thickness. None is allocated reactor space.

## Unknowns and cheapest rejection checks

D–T is a **conditional branch**, not a selected fuel. Other fuels need their own
reaction/confinement/exhaust assumptions. These proposed checks have not passed.

| Input missing | Cheapest check before a detailed solver |
| --- | --- |
| Reactor size, field and fuel | Declare scale, volume, axis/peak conductor fields. Reject an operating point whose scaled component envelopes cannot fit. |
| Density, temperatures, pressure and confinement | Declare profiles/losses; balance auxiliary plus retained alpha heating against transport/radiation. Calculate required confinement time. Vacuum action scores supply none. |
| Fusion, thermal, gross and net electric power | Supply efficiencies and heating/cryogenic/pumping/fuel-cycle loads. Reject a point whose credible upper-bound net output misses the requirement. Plasma gain is insufficient. [ITER distinction](https://www.iter.org/fusion-energy/what-will-iter-do). |
| Winding, vessel, blanket and shield | Fit finite envelopes, supports and ports in three-dimensional clearance. For D–T, reject envelopes incompatible with breeding/inventory and neutron lifetime limits. [ParaStell method](https://www.frontiersin.org/journals/nuclear-engineering/articles/10.3389/fnuen.2024.1384788/full). |
| Magnet loads and protection | Supply conductor/temperature/current-density/stress limits; estimate peak-field forces, stored energy and quench extraction. Filament checks cannot qualify them. |
| Heat exhaust | Declare deposited power, radiation fraction, wetted area and cooling limit. Reject excessive local wall/divertor loads including peaking. |
| Maintenance and lifetime | Specify replacement paths, handling clearances, exposure limits and outages. Reject inaccessible routes before optimizing availability. |

## Two desk calculations that can change the decision

For geometrically similar filaments, length scaling λ and field scaling κ require
ampere-turn scaling λκ by Biot–Savart. Volume scales as λ³, while area scales as λ².
At fixed temperature, composition and beta, density scales as κ²; fusion power
therefore scales as κ⁴λ³ and average neutron wall loading as κ⁴λ, assuming unchanged
neutron fraction and wall coverage. These conditional sensitivities do not predict
confinement or engineering performance; enlarging the pilot changes reactor burdens.

Separately, define recovered thermal power `P_th`, conversion efficiency `eta_th`,
plasma-deposited auxiliary heating `P_heat`, wall-plug heating efficiency `eta_heat`
and all other electrical loads `P_other`. Then
`P_net = eta_th * P_th - P_heat / eta_heat - P_other`.
Count each recovered heat source and electrical load once. No numerical net-power
estimate is justified until these quantities and the operating profiles are supplied.

A [conditional finite-envelope calculation](ISSUE27_ENVELOPE_SCREEN.md) now excludes
some scaled copies of the latest coils. It supplies a numerical space constraint,
not a coupled operating point or engineering qualification.

**Next:** supply operating profiles, power balance and qualified component limits.
Reuse system-design/geometry tools only for unresolved decision needs.
