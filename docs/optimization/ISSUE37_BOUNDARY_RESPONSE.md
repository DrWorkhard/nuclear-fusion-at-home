# Can four small boundary modes align with the fixed coils?

Exploratory question, 7 October 2026: before more coupled optimization, can the
four modes proposed in [draft PR59](https://github.com/DrWorkhard/nuclear-fusion-at-home/pull/59)
produce a substantial reduction in the latest candidate's normal-field error
with its coils held fixed? This is a local surface-alignment diagnostic, separate
from that contributor's moving-coil optimizer and from equilibrium acceptance.

Use the [paired fit's](ISSUE37_FIT_COUPLING_RESULT.md) frozen scale035 trial 427,
its exact target input and currents. Perturb only rbc(1,1), rbc(2,0), zbs(1,1),
zbs(2,0), each within ±0.5 mm. All other modes and physical coil coefficients and
currents remain fixed. No equilibrium solve, ideal score, coil fit or flux
renormalization occurs. The displaced surface is not a qualified plasma target.

The [study script](../../scripts/explore_boundary_response.py) computes central
responses at 10 and 5 micrometres on the 64-square grid, including field-point
motion, normals, |B| normalization and changing area weights. Each Jacobian
column must agree to relative 1e-3. Minimize the linearized area-weighted RMS
inside the four-dimensional box by enumerating its active faces. Freeze that
single step before nonlinear evaluation on the original grid and two fine
128-square grids at shifts 0 and 0.5, with 512 coil nodes. No second step is chosen.

Require nonlinear residual-vector disagreement ≤1% of baseline RMS and coarse/fine
RMS disagreement ≤0.1% before interpreting the model. Baseline fields must match
the saved fine subsample and each new fine grid must pass an independent 64-point
B check to 1e-12. A promising shortcut must halve RMS on **both** fine grids.
Otherwise record no substantial local fixed-coil shortcut; derivative/model or
numerical failures are inconclusive. Report maximum error and volume/flux changes.
Even a positive needs fresh equilibrium, ideal and engineering checks. A negative
leaves moving coils, other steps and nonlinear/global solutions untested.

One exploratory attempt: 180 s total including imports/checks/reporting, 32 MiB
output, 3 GiB initial / 2 GiB live reserve, one native thread, dual clocks with
≤5 s disagreement. Timing is not a matched-compute or continuous-host claim.
Preserve all probes, failures and source/environment identities. No new optimizer
framework or acceptance change. Software/adversarial review precedes execution;
results and archive identities will replace this prospective note after completion.
