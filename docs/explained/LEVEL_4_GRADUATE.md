# Level 4: for a graduate student

Updated 5 October 2026 · [All five levels](README.md) ·
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

- Best geometry-checked fit: boundary RMS **0.001996**, maximum **0.00943**,
  interior RMS **0.01148**; all three field limits fail. Geometry passes: length
  ≤ 3.474 m, coil–coil ≥ 0.068 m, coil–plasma ≥ 0.133 m, curvature ≤ 10.05/m
  (normalized scale). Widening the coefficient box gained only 2.64% boundary RMS.
- A matched restart lowered boundary RMS by 55% with 8.6% less current. A wider
  run passed the interior limit (0.00977), but its length bounds were
  unresolved. Construction headroom then fixed geometry and lost the interior pass.
- Failures that shaped the method: coarse clearance sampling missed 1.8–6.7 mm
  gaps; a certified small-step search followed a poorly aligned objective; adjusting
  currents alone could not close the gap.
- All coil fits so far target reference401, **not** the improved Step 3 target.

## New diagnostics (October 2026)

- **Realized-field tracing:** ten field lines started on target surfaces
  s = 0.05–0.95 in the best coil field stay inside for 200 toroidal transits;
  maximum signed-ι mismatch is 0.004951 against a 0.02 tolerance. Interpolated and
  direct field evaluation agree. This does not measure nestedness or island widths,
  and s > 0.95 is untested.
- **Portable checks:** a regenerated Wout can rebuild the interior targets outside
  the maintainer's machine, checked for consistency against the public samples;
  a positive control reproduces the archived boundary and geometry metrics to
  1.5e-15. It ran on the same machine family, so it is not an independent
  reproduction.

Details: [active coil research](../optimization/README.md).

## Open problems and the next decision

1. Fit the improved Step 3 target with matched effort and compare the bounce-action
   diagnostic in both coil fields on matched domains (benefit transfer).
2. Diagnose optimizer conditioning and stopping once, rather than adding variants.
3. Screen reactor feasibility: device scale, field, power balance, magnet loads,
   blanket and shield space, heat exhaust.
4. Finite pressure (4C) and finite-build robustness (4D) remain deferred.

**24 October 2026:** continue the fixed-target recipe only if a matched reference401
comparison at least halves boundary RMS without worsening interior RMS and the
realized-field diagnostics support pursuing transfer; otherwise switch to another
coil family, another target, or joint plasma–coil optimization.
[Programme](../optimization/STEP4_RESEARCH_PROGRAMME.md).

## Good entry points

Reproduce the best candidate and probe sparse-sampling artifacts with the dense
boundary diagnostic; trace surfaces for other candidates; compare conditioning
under a matched time budget; or try to break a claim. See the
[research hints](../optimization/RESEARCH_HINTS.md) and
[open issues](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues).
