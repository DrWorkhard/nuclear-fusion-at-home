# Joint plasma/coil comparison protocol (draft for #37)

Question: under matched coil constraints and budgets, does releasing the Step 3
plasma modes together with the coils realize **more** of the Step 3 action benefit
in actual coil fields than fitting coils to a fixed target? Settings are in
[joint-protocol.json](joint-protocol.json). Review requests are tracked in #63.
**Status: not ready to run.** The derivative-reliability check (below) failed its
preregistered tolerance at the proposed search resolutions.

## Arms (sequential, one thread, same machine)

| Arm | Target | Free variables |
| --- | --- | --- |
| F-ref | reference401, fixed | 198 coil coefficients |
| F-sel | selected401 (Step 3), fixed | 198 coil coefficients |
| J | reference401 boundary with the **four Step 3 modes** released | 198 coils + `rbc(1,1)`, `rbc(2,0)`, `zbs(1,1)`, `zbs(2,0)` |

The four modes are those Step 3 changed. Each moved by about 1e-4 in Step 3; J may
move each within ±5e-4 of reference401. All other boundary modes, `phiedge`, nfp = 2,
stellarator symmetry and the six order-5 coils stay fixed. Every arm starts from the
length-headroom coils. Coil penalties, coil eligibility, current limit and the #55
trial handling are unchanged. Every arm gets 1800 s of search, including equilibrium
solves and startup, reported separately.

## Comparability (measured, not assumed)

J candidates are eligible only if volume, aspect ratio, major radius and B0 stay
within ±1% of reference401 (ns = 25). Actual changes are reported. At the eight
single-mode ±5e-4 extremes, the largest change was 0.17% (B0), so the bounds stand.
Fixed flux and fixed modes alone do not guarantee comparability; this tolerance does.

## Objective and selection

- F arms: the existing fitter. It selects the lowest boundary RMS among eligible
  completed candidates.
- J objective: J_flux + geometry penalties + w · A. A is the ideal narrow action
  score (3 surfaces × 5 pitches, 801 points, 16 α) of the current equilibrium.
  - **w = 0.09** is frozen. It is the preregistered break-even weight
    w = ΔJ_flux / (A(0) − A(1)) along Step 3's own boundary change with fixed
    coils: A fell 3.9% while J_flux rose 2.1%.
- **J selection:** the lowest *J objective* among completed candidates that meet
  coil eligibility, the comparability tolerance, equilibrium convergence and a
  complete A. Boundary RMS is reported, not used for selection. Independent checks
  follow freezing.
- Plasma gradients are central differences; coil gradients are analytic. A failed
  equilibrium is a rejected trial. The selected J boundary is re-solved at
  ns = 401, and its normalization is recomputed once and frozen.

## Derivative reliability: failed, so the J arm is not ready

Central-difference ∂A for the four modes, at the reference and selected boundaries.
Tolerances: at most 10% spread across h; within 20% of ns = 101 with the same sign.
- At the selected boundary, ns = 25 and ns = 51 both fail the resolution test. For
  `rbc(2,0)`, ns = 25 gives 2.1e-4 and ns = 51 gives 4.8e-4, against 6.9e-4 at ns = 101.
- At the reference boundary, h = 3e-5 is already nonlinear (spread up to 19%).

By the preregistered rule the pilot does not run. Proposed change, which needs the
maintainer's agreement: search at ns = 101 with h = 1e-5 (about 22 s per
evaluation, about 10 plasma-gradient steps per arm), after one more check of
ns = 101 against ns = 201 under the same tolerances.

## Endpoints, validation exposure and decision scope

- **Exploratory scores:** coil-field narrow and wide action scores from
  `scripts/measure_coil_bounce.py`, launched from *target* labels. Labels drift up to
  0.068 in realized flux and differ across α (#48), so these scores are not
  comparable physics across arms.
- **Confirmatory endpoint:** needs qualified, matched realized-surface sampling.
  No tool supplies it yet. Until it exists, a pilot can decide only feasibility:
  whether J runs within budget, moves the plasma modes, and changes the exploratory
  scores. Incomplete endpoints are inconclusive.
- **Validation exposure:** the wide domain and pitches 0.03/0.97 were inspected in
  #25/#35, so they are extra validation, not untouched holdouts. Frozen now, for any
  confirmation: an independent check on s = 0.35 and 0.65 with α offset by half a
  spacing (16 lines). These have not been inspected.
- **Pilot rule:** J ≤ 0.975 × F-sel on the exploratory narrow score, geometry passing,
  and own-target boundary RMS ≤ 1.10 × F-sel. This is a resource-allocation rule, not
  physical acceptance. A negative result concerns this four-mode local search at
  this budget, not joint optimization in general.

## Equilibrium identities

Original Wouts reproduce historical runs exactly. A regenerated equilibrium may
substitute only under its own identity (vmecpp version and SHA-256) and after a
parity check; the same policy applies to every arm.
- **Reference401 (vmecpp):** passes, with starter samples matching to 3.4e-10 and
  the ideal narrow score to 3.4e-8 of #35.
- **Selected401 (vmecpp):** passes, with the ideal narrow score matching to 1.0e-7
  (`ier_flag` 0).

Not included: finite pressure, transport, winding packs, other optimizers or
targets. One seed, one budget per arm; not physical acceptance.
