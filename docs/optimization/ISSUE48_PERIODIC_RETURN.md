# Prospective local eleven-period return test

Decision: do the reproduced failed samples lie near a numerically resolved
nontrivial periodic field line with elliptic or hyperbolic linear behavior?
The eleven separated sampled patches motivate testing resonant structure before
trying to bridge them with a single contour. This is an exploratory local search,
not a proof of islands or a confirmatory transfer claim.

Freeze the continuation snapshot and refined failed-launch NPZ from archive
`d12b01bedbb3d4e89ab891d03a9e6048f0690918`. Its manifest SHA256 is
`a6e1708bbb3996752d331cb61485cefc656d40d59948deadabda6f9488ed39f7`.
Seed = arithmetic mean of the first eleven-residue sequence of 320 phi=0 refined
crossings (indices 0,11,22,...). This is a data-informed seed, fixed before native
root calculations. No scan or alternative seed if it fails.

Define P as the unchanged DOP853 direct R,Z map through one field period, phi=0
to pi, from producer `5a0d06303a2d0405f52e0f179176bc2ada532536`. Solve
P^11(x)-x=0 using SciPy hybr, xtol=1e-9, with every root trial within 1 cm of the
seed. Independently start 512-node (rtol=1e-10, atol=1e-12) and 1024-node
(1e-11, 1e-13) runs from that seed. Require solver success, residual <=1e-9 m,
point agreement <=1e-7 m and |P(x)-x|>1e-3 m to exclude the one-period axis.
Since 11 is prime, the latter distinguishes a nontrivial eleven-period return
from a one-period fixed point in the symmetry-reduced section. Eleven field
periods are 5.5 toroidal turns; the physical orbit closes after eleven turns.

At each resolved point, estimate D(P^11) with central differences at h=1e-5 and
5e-6 m in named R,Z coordinates. Record complete matrices, traces, determinants
and (2-trace)/4 residues. Numerical linear classification is permitted only when
all four determinants differ from one by <=1e-4, trace spread <=1e-3, and every
trace lies in the same region separated from ±2 by max(1e-3, ten times spread).
Otherwise report unresolved. Regions: (-2,2) elliptic, above 2 hyperbolic, below
-2 reflection-hyperbolic. These finite-difference tests are not rigorous bounds.
Method basis: [Davies et al., section 2](https://doi.org/10.1017/S0022377826101287).
Check independent filament B at all twelve saved orbit endpoints to error <=1e-12
on scale max(1,|B|). Record one-period separation and every root trial.

One attempt: 300 s inside the driver after imports / 330 s supervised total,
one thread, 256 MiB, 3/2 GiB reserves, 5 s clock discrepancy. Reuse reviewed
owned-process supervision and frozen native environment verification. Analytic
affine-map controls test root finding, differentiation and unresolved boundaries
before running. No retries, extra seeds, longer traces or outcome-driven tuning.
Preserve original outputs; no field, current, label or acceptance gate changes.

A resolved elliptic point would motivate island-aware reconstruction checks; a
failed/unresolved search identifies no absence of resonance. Neither establishes
an island width, separatrix, nonlinear stability, confinement, common flux labels
or benefit transfer. Original 19/20 qualification remains unchanged. Adversarial
review precedes local integration; publication remains unauthorized.
