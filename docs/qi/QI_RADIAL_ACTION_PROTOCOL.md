# Fixed-invariant radial action pilot v1

Declared 2026-09-10 after inventory, before pilot traces and derivative results.

## Question and source

Can our independent VMEC tracer resolve the sign of the radial derivative of
individual complete bounce actions, without averaging over alpha or changing
the pitch parameter with radius? This is a measurement pilot, not a reproduction
of a published figure or a global maximum-J claim. The physical motivation and
fixed-invariant definition follow Goodman et al., sections 1.2–1.3 and 5:
[Constructing precisely quasi-isodynamic magnetic fields](https://doi.org/10.1017/S002237782300065X).

## Frozen scope

Four inputs: nfp2 and nfp3 vacuum plus their nominal beta=2.00% archive cases.
Hashes come from the existing transfer reference and finite-beta inventory.
Actual finite-beta values are 2.01147376% and 2.00998938%, respectively.
The configurations are not rescaled and currents/profiles are not changed.

For each case use s0=0.5, central radial steps h=0.04, 0.02, 0.01 and their
seven distinct radii. Trace eight equally spaced alpha values over four field
periods, with nphi=801,1601,3201. Fixed VMEC straight-field-line gauge is
theta+lambda=alpha+iota(s)*phi. Non-omnigenous derivatives can depend on radial
alpha-gauge choices; no gauge-independent claim is made.

Choose a *single* accessible Bstar interval per case, before action evaluation,
from the intersection of the min/max B ranges on every coarse trace line at
all seven radii. Five Bstar values divide this interval at q=0.1,0.3,0.5,0.7,0.9.
These exact Bstar values stay fixed across all radii and resolutions. This is a
sampled domain choice, not continuum-domain coverage or near-separatrix coverage.

Compute A=integral sqrt(1-B/Bstar) dl for every complete well using the existing
piecewise-linear exact integrator. A positive constant factor distinguishes this
one-way reduced action from the full invariant; it does not change signs at
fixed energy and magnetic moment. Preserve all incomplete wells as counts.

## Family matching and numerical screens

At each alpha/Bstar identify every complete s0 well whose midpoint lies in the
central two field periods. Match each by geometric-phi interval overlap to all
other traces (including s0 refinement). Require a unique one-to-one match, overlap
longer than half the shorter interval and each endpoint displacement less than
one quarter of the anchor interval length. Every other well with a midpoint in
the central window must be matched too. Ambiguity, births/deaths, missing wells
or an empty anchor set fail the cell; no nearest-action matching or censoring.
This is a restricted geometric continuation screen, not a proof of well topology
between the seven radial samples. Boundary-window wells remain outside scope.

For each family D(h)=[A(s0+h)-A(s0-h)]/(2h). Normalize all derivatives by the
matched finest s0 action. Use the finest h=0.01,nphi=3201 estimate. Define
e_trace=abs(D_3201(0.01)-D_1601(0.01))/A0 and
e_radial=abs(D_3201(0.01)-D_3201(0.02))/A0. Require each <=
max(0.01,0.05*abs(D_3201(0.01)/A0)); retain the h=0.04 result as another diagnostic.
Classify negative/positive only if the normalized derivative plus/minus
4*(e_trace+e_radial) excludes zero, otherwise unresolved. This allowance is
an empirical refinement screen, **not a rigorous truncation-error interval**.
Do not assume quadratic Richardson convergence: radial Fourier interpolation
is piecewise linear and crosses VMEC full/half-grid knots.

## Evidence and limits

Commit tested implementation before running. Preserve raw trace NPZ hashes, all
well counts/matches, all derivatives and code/input/protocol hashes. Report
failed/positive/unresolved cells and families, never just negative fractions.
Use analytical matching and radial-sign controls, then the full regression suite.
No claim about s outside the stencil, untraced alpha, excluded Bstar, global
maximum-J, equilibrium-grid convergence, turbulence or reactor performance.
