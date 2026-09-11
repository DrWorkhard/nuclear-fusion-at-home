# Independent complex-step clearance qualification — 2026-09-11

Retrospective response to the failed seed-47 forward-difference screen at the
selected direct candidate. The four failed rows are inter-coil clearances;
their 1e-8 finite differences subtract values much larger than the small change.
All other rows pass. Do not relabel the failed original diagnostic as passing.

Independently reconstruct all sixteen physical Fourier curves from frozen
coefficients and symmetry transforms, without native geometry derivatives.
For every one of the 120 pairs evaluate the same smooth squared-distance row
using complex arithmetic, with no conjugation in squared distances:

    q = a0^2 sum_d (gamma_i - gamma_j)_d^2,
    lower = anchor - log(sum(exp(-512*(q-anchor))))/512,
    g = lower/(1.10^2)-1.

Anchor is the real minimum at the unperturbed state and is held fixed for all
complex steps. Reconstruct gamma with independent sine/cosine Fourier matrices
at the original 200 nodes. The sum is never divided by the sample count.

Both frozen states from direct-descent-diagnostic-v1 are mandatory. Real-valued
rows must match all stored native-backed rows to normalized 1e-10. In the original
named source basis use seeds 47 and 48, each normalized to unit Euclidean length.
For h=1e-12,1e-20,1e-28 require every complex-step Im(g(x+ih*d))/h to agree with
the stored analytic directional derivative to normalized 1e-9. Require all steps
mutually consistent to normalized 1e-10. All current columns of the geometric
Jacobian must be zero. Save source coefficient/direction arrays and all comparisons.

Core controls: analytic Fourier circles, length/rotation/translation behavior of
positions, known constant-distance log-sum-exp offset, and comparison of complex
directional derivatives with independent real central differences. Malformed and
nonfinite inputs must fail. This kernel checks pair-clearance values/derivatives,
not magnetic flux, plasma-distance, native curvature or continuous clearance.

Only if this separate qualification passes may a new version of the bounded
descent diagnostic use a composite gate: the original unchanged finest-step
screen for every non-pair row, plus this independent qualification for all pair
rows. The original all-row forward-difference failure must still be explicit in
the new report. Keep the same two states, three radii, LP controls and all nonlinear
probe rules; do not tune the radii or reinterpret a linear step as admission.
