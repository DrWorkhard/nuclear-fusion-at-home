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
  [pending residual diagnosis](../optimization/FIELD_RESIDUAL_PROGRESS.md) and
  reference calibration address this distinction. Do not relax gates merely
  because the current designs fail them.
- **Use named physical coordinates.** Positional optimizer arrays can change
  meaning across processes. The [mapping correction](../optimization/REPLAY_MAPPING_REMEDIATION.md)
  explains why replay must bind names, coefficients and physical fields.
- **Plasma-proxy improvement is not reactor improvement.** The
  [Step 3 result](../steps/STEP_3_PLASMA_TARGET.md) is a vacuum diagnostic; realized
  coil fields, confinement, pressure and finite-build robustness remain separate
  [Step 4 requirements](../steps/STEP_4_PLASMA_AND_COILS.md).

Keep each result's failures and limits in its canonical report and evidence.
Replace this summary as understanding changes; Git retains superseded findings.
