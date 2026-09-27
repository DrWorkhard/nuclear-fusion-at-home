# Research lessons and unresolved questions

The [scientific status](../STATUS.md) owns the current result summary; the
[programme](../optimization/STEP4_RESEARCH_PROGRAMME.md) owns next experiments.
These lessons guide that work rather than duplicating the full result chronology.

- **Geometry and field quality are separate.** Coarse samples missed small
  clearances in the [first coil pilot](../optimization/COUPLED_COIL_PILOT_RESULTS.md).
  Continuous geometric checks later passed, while
  [fine field errors](../optimization/PROTECTED_FINE_RESULTS.md) still failed.
  A geometrically certified step is not an accepted design.
- **A conservative rejection is not physical impossibility.** The
  [local curvature check](../geometry/LOCAL_CURVATURE_RESULTS.md) certified two
  previously blocked proposals. Their [field comparison](../optimization/FIXED_FIELD_PROBE_RESULTS.md)
  shows small gains, not a demonstrated route to feasibility.
- **Compare the same metric and conventions.** Objective descent does not by
  itself imply normal-RMS improvement; raw LPQA flux, Goodman normalized fields
  and the sparse public scores are different comparisons. The
  [completed residual diagnosis](../optimization/FIELD_RESIDUAL_RESULTS.md) shows
  this difference in our observed steps. [Matched references](../optimization/REFERENCE_CALIBRATION.md)
  reproduce the archived LPQA mean/max and show that near-zero QUASR collocation
  error becomes finite after refinement. Neither clipping nor collocation is
  physical perfection. Do not relax gates merely because current designs fail.
- **One fixed flux does not preserve the whole field.** In the
  [independent-current study](../optimization/INDEPENDENT_CURRENT_EXPLORATION.md),
  raw-error minima weaken boundary fields and worsen normalized error despite
  meeting the target loop flux. Direct normalized fitting helps, but still leaves
  weak-field trade-offs. Retain amplitudes, maxima and interior checks; a favorable
  single boundary score does not establish field fidelity or confinement.
- **Finite differences can cross penalty switches.** The
  [coherent-shape startup](../optimization/COHERENT_COIL_EXPLORATION.md) fails its
  original derivative check when larger probes straddle sampled curvature
  penalty branches. A fixed component/step-size study supports smaller probes
  under the same tolerances. Preserve the failure and diagnose convergence;
  neither silent probe changes nor relaxed physical gates are justified.
- **Use named physical coordinates.** Positional optimizer arrays can change
  meaning across processes. The [mapping correction](../optimization/REPLAY_MAPPING_REMEDIATION.md)
  explains why replay must bind names, coefficients and physical fields.
- **Test interacting native caches, not only repeatability.** The
  [objective experiment](../optimization/NORMALIZED_OBJECTIVE_EXPLORATION.md)
  caught an instrumentation wrapper assigning two fields equal native identities.
  Seed repeats passed while one field cache stayed stale. Perturb/reset checks
  with two fields and fresh unwrapped controls now cover that failure.
- **Plasma-proxy improvement is not reactor improvement.** The
  [Step 3 result](../steps/STEP_3_PLASMA_TARGET.md) is a vacuum diagnostic; realized
  coil fields, confinement, pressure and finite-build robustness remain separate
  [Step 4 requirements](../steps/STEP_4_PLASMA_AND_COILS.md).

Keep each result's failures and limits in its canonical report and evidence.
Replace this summary as understanding changes; Git retains superseded findings.
