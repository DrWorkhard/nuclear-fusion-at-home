# Level 4: for a graduate student

Updated 8 October 2026 · [All five levels](README.md) ·
Previous: [Level 3](LEVEL_3_UNIVERSITY.md) · Next: [Level 5](LEVEL_5_EXPERT.md)

We run a two-stage stellarator design study in the open: improve a QI vacuum
target, then test whether filamentary coils can realize it and keep the benefit.
Construction (optimization) and acceptance (fixed, independent checks) are
deliberately separate. Numbers below come from the [status page](../STATUS.md)
and the [Step 4 page](../steps/STEP_4_PLASMA_AND_COILS.md).

## Configuration and conventions

- **Target:** reference401, a Goodman open QI case. VMEC input with nfp = 2,
  stellarator symmetry, zero pressure, mpol = 5, ntor = 10, radial resolution up
  to 401 surfaces, edge toroidal flux π/100 Wb at the normalized scale. Inputs
  are [committed](../../evidence/plasma-design-v2/reference-input-401.json);
  the Wout can be regenerated with VMEC++ in about six minutes.
- **Coils:** six base filaments, Cartesian Fourier order 5 (198 named
  coefficients), mapped by the nfp = 2 and stellarator symmetries to 24 coils.
  The native stack builds on SIMSOPT and VMEC++.
- **Currents:** research checks rescale currents so the coil field reproduces the
  target's toroidal flux (flux normalization). The public starter freezes
  currents instead, so public and native scores of the same geometry differ.

## Step 3: the plasma result

Four boundary-coefficient changes reduced the variance of the bounce action (the
second adiabatic invariant, evaluated across field lines) by **11.17%** in a wide
and **4.85%** in a narrow domain. All ten registered gates passed, including a
finer independent recomputation. Both domains informed construction, so neither
is a blind holdout. A first design that improved only the narrow metric worsened
the wide one by 15.53% and remains rejected.

## Step 4: fitter and checks

- **Fit:** penalized, flux-normalized L-BFGS-B over the coil coefficients.
  Lengths above 3.44 m are penalized (acceptance limit 3.5 m). Among completed
  candidates within sampled geometry and current limits, the lowest boundary RMS
  wins; probes cannot win and there is no fallback.
- **Checks, with currents frozen:** two fine boundary grids, continuous geometry
  bounds (padded floating point, not interval proofs), interior field at three
  resolutions, and independent B and vector-potential calculations.
- **Acceptance:** boundary RMS of B·n/|B| ≤ 1e-4, maximum ≤ 1e-3, interior
  vector RMS ≤ 0.01 (normalized by the target's mean B²), plus geometry limits.
  A solver success flag or a low objective value is not acceptance.

## Results and lessons

- Length-headroom fit (the public candidate): boundary RMS **0.001996**, maximum
  **0.00943**, interior RMS **0.01148**; all three field limits fail. Geometry passes: length
  ≤ 3.474 m, coil–coil ≥ 0.068 m, coil–plasma ≥ 0.133 m, curvature ≤ 10.05/m
  (normalized scale). Widening the coefficient box gained only 2.64% boundary RMS.
- A matched restart lowered boundary RMS by 55% with 8.6% less current. A wider
  run passed the interior limit (0.00977), but its length bounds were
  unresolved. Construction headroom then fixed geometry and lost the interior pass.
- Failures that shaped the method: coarse clearance sampling missed 1.8–6.7 mm
  gaps; a certified small-step search followed a poorly aligned objective; adjusting
  currents alone could not close the gap.
- **Matched targets ([issue #25](../optimization/ISSUE25_MATCHED_TARGETS.md)):**
  from the same start, two 300 s searches fit reference401 and the improved Step 3
  target. Fine boundary RMS 0.001932 / 0.001953, maximum 0.00907 / 0.00927,
  interior RMS 0.01072 / 0.01089; geometry passes and field limits fail in both.
  These errors are against different targets, so they are not a benefit measure.

## New diagnostics (October 2026)

- **Realized-field tracing:** ten field lines started on target surfaces
  s = 0.05–0.95 in the length-headroom coil field stay inside for 200 transits;
  maximum signed-ι mismatch is 0.004951 against a 0.02 tolerance. Interpolated and
  direct field evaluation agree. This does not measure nestedness or island widths,
  and s > 0.95 is untested.
- **Portable checks:** a regenerated Wout can rebuild the interior targets outside
  the maintainer's machine, checked for consistency against the public samples;
  a positive control reproduces the archived boundary and geometry metrics to
  1.5e-15. It ran on the same machine family, so it is not an independent
  reproduction.

- **Action diagnostic in the coil fields:** trajectories launched from target
  coordinates (801 toroidal samples, 16 field-line labels) reuse the Step 3
  statistic. The wide domain is incomplete in both arms because required wells
  are missing (32 / 33 failed launch lines); no failed cell is dropped. The narrow
  score is 5.07% lower for the improved arm, but both are degraded relative to
  their ideal targets. Matched-fit tracing: 10/10 lines, signed-ι mismatch
  0.005262 / 0.005641.

Details: [active coil research](../optimization/README.md).

## Open problems and the next decision

1. Diagnose why shallow wells are lost in the coil fields and validate realized
   flux-surface labels before any benefit-transfer confirmation.
2. Fix the fitter: one failed trial discards a run, and `ftol` acts as an
   absolute threshold because the objective is about 5e-6 ([#52](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/52)).
3. Specify a reactor operating point: the [feasibility screen](../engineering/REACTOR_FEASIBILITY_SCREEN.md) records the
   missing inputs (scale, field, power balance, magnets, blanket and shield space,
   heat exhaust) and defers reactor-scale search.
4. Finite pressure (4C) and finite-build robustness (4D) remain deferred.

**Decision, 6 October 2026: the fixed-target recipe has stalled.** The hurdle was
to halve boundary RMS without worsening interior RMS. The preregistered 30-minute
conditioning/stopping comparison ([#31](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/31)) reached 0.0018761 (−6.0%); a
scale-free objective added about 1.2% before a trial failure. A matched
[coil-freedom probe](../optimization/ISSUE53_COIL_FREEDOM.md) then lifted six coils to Fourier order 8 under the same
30-minute budget: boundary RMS 0.0017815 versus 0.0018486 (ratio 0.964, required
≤ 0.5), with both arms ending at the curvature and length construction penalties.
**Route chosen, 8 October 2026: joint plasma–coil optimization** ([#36](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/36)),
starting with a preregistered feasibility pilot ([#37](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/37)).
[Programme](../optimization/STEP4_RESEARCH_PROGRAMME.md).

## Good entry points

Reproduce the best candidate and probe sparse-sampling artifacts with the dense
boundary diagnostic; trace surfaces for other candidates; compare conditioning
under a matched time budget; or try to break a claim. See the
[research hints](../optimization/RESEARCH_HINTS.md) and
[open issues](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues).
