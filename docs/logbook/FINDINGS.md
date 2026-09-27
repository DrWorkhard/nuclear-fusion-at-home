# Current research lessons

- **Wider coherent motion matters.** The [matched restart](../optimization/COHERENT_COIL_EXPLORATION.md)
  reaches RMS 0.004889 with checked geometry and improves both error and current
  against its matched control. Budget exhaustion is not an optimum.
- **Construction needs headroom.** The [longer/wider fit](../optimization/LONGER_COIL_EXPLORATION.md)
  passes the interior-vector component, but sampled lengths just below 3.5 m
  leave conservative length bounds unresolved. A tighter construction target
  resolves geometry at a modest boundary-error cost, but loses the interior
  pass. That trade-off is measurable; it is not fixed by lowering standards.
- **A solver stop is not an optimum.** The expanded headroom fit improves boundary
  RMS only 2.64%, with no active box bounds. It stops on objective change while
  the largest final gradient component is 3.40e-5 versus a 1e-9 tolerance.
  Investigate scaling/conditioning before attributing the plateau to coil count.
- **Check the right objective.** Raw-field and normalized errors can disagree;
  fixed loop flux does not preserve the whole field. Current-only negative
  results remain at the [freeze tag](../validation/REPRODUCING_RESULTS.md).
- **Geometry and field quality differ.** Sampled penalties can miss clearance
  failures; conservative bound rejection is not proof of impossibility.
- **Inspect numerical failures.** Larger finite-difference probes crossed
  curvature-penalty branches; a diagnosed smaller probe passed unchanged
  tolerances. Native field identity/cache tests caught a separate old defect.
- **Boundary fitting is only part of the physics.** Interior fields, actual field
  lines and transfer of the Step 3 benefit still need independent checks.
- **Use named coordinates and retained failures.** Numerical reproduction must
  bind geometry, currents, target and conventions—not array positions alone.

The [status page](../STATUS.md) owns numerical conclusions; this page records
lessons, not another result history.
