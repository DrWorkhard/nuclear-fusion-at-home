# Bounded matching of realized-flux launch labels

**Exploratory question:** can four physically specified launch rays in each
frozen #25 coil field be adjusted to the same enclosed-flux label 0.75?
The [label qualification](ISSUE48_REALIZED_LABELS.md) finds phase-dependent offsets
and a sampling limitation. Removing those offsets is a prerequisite to testing
their effect on action diagnostics; it does not establish benefit transfer.

## Frozen inputs and rule

Use the same two Wouts, snapshots, currents, axis coordinates and four nominal
VMEC theta phases as the qualification. Keep the s=0.25 control start unchanged.
For each affected start, define physical coordinates explicitly:
`(R,Z)_new = (R,Z)_axis + rho * ((R,Z)_original - (R,Z)_axis)` at phi=0.
The scalar `rho` must stay in [0.95,1.05]; these are ray displacements, not a new
VMEC surface label or PEST alpha coordinate.

Round 1 uses `rho=sqrt(0.75/estimated_label)` from the refined qualification,
using the targeted two-section estimate for the previously failed reference ray.
This is an initializer, not an exact quadratic flux law. Both arms now use the
same 321-turn, two-section protocol and 1024/2048 angular, 24 radial quadrature.
All corrected traces must pass the unchanged reconstruction checks.

If the first round qualifies but its estimated label differs from 0.75 by more
than 5e-4, permit exactly one secant correction from the original and round-1
trials. Reject nonfinite, unresolved (scale difference <1e-10, slope <=1e-3),
nonpositive-slope or out-of-bounds proposals. Never clip or retry silently.
Retain every attempt; requalify each second-round trace. Stop rather than correct
from an unqualified first-round estimate. Keep already matched rays unchanged.
Success requires all four corrected estimates within 5e-4 of 0.75 and total
phase spread at most 1e-3 in each arm, as well as reconstruction qualification.
These tolerances describe estimated numerical labels, not guaranteed true flux.

Each round has at most 900 s and 256 MiB per arm, sequentially on one thread,
3 GiB initial / 2 GiB live reserve, with a 960 s supervisor. Record the actual
launch coordinates, scale inputs and hashes, source-label producer, residuals,
failures and elapsed time. Original outputs remain untouched. Use
[measure_flux_labels.py](../../scripts/measure_flux_labels.py) with
`--crossings 320 --half-period --launch-scales <frozen-json>`.

## Interpretation

Even success means only sampled enclosed-flux matching. It does not establish
unique nested surfaces, canonical/equal-alpha sampling, complete well coverage,
confinement or a valid replacement for the original 16-alpha action comparison.
Do not substitute four geometric phases for that domain or relax field gates.
Require adversarial review of the implementation and result before integration.
