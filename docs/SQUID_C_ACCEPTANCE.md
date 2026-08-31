# SQuID-C reproduction contract

This contract freezes the first paper-level checks before authoritative SQuID-C
machine files are ingested. Values reported with limited decimal precision are
accepted only inside their rounding intervals; tighter solver regressions will be
added from the supplied raw outputs without replacing these paper checks.

## Identity and state

- Source: Goodman et al., *A quasi-isodynamic stellarator configuration towards
  a fusion power plant*, DOI 10.1017/S0022377825100974.
- Primary coil-generated equilibrium: volume-averaged beta 2 %, with the linear
  pressure profile `p(s) proportional to 1-s`, including coil ripple.
- Required artifacts: fixed-boundary target, coil-generated free-boundary input
  and wout, pressure/current profiles, complete coil centre-lines or winding
  volumes, signed currents, MGRID recipe, solver controls, symmetry expansion,
  and physical scale.

The paper confirms that the coil optimization includes the plasma-current field,
targets volume-averaged beta 2%, and reports subsequent calculations on the
coil-generated equilibrium including coil ripple. It also reports separate
free-boundary finite-pressure scans. These states must not be collapsed into one
ambiguous `wout`.

## Machine-readable admission contract

SQuID-C uses manifest schema 2. Admission requires unique file roles for both
fixed- and free-boundary VMEC inputs and outputs plus profiles, coils, currents,
MGRID recipe, solver controls, and metadata. Every file declares byte size,
SHA-256, and either an authoritative source URL or its parent roles and exact
derivation recipe. The manifest also records:

- code versions, resolution, convergence tolerances, and free-boundary state for
  both equilibria;
- coordinate/current/angle/minor-radius conventions;
- physical minor-radius and field scale;
- field periods, stellarator symmetry, unique/full coil counts, and exact
  symmetry expansion;
- data authority, license, and retrieval timestamp.

The unfilled template is deliberately invalid. A complete synthetic package with
all ten roles is exercised in core tests and both equilibrium states reach the
generic intake without case-specific code.

## Paper-level coil checks

Relative normal-field error uses the paper's definition
`E = (B dot n_hat) / |B|`. On a grid independently generated from the serialized
coils and boundary:

- average absolute relative error must round to 0.27 % (interval
  `[0.265 %, 0.275 %)`);
- maximum absolute relative error must round to 1.2 % (interval
  `[1.15 %, 1.25 %)`), subject to reproducing the authors' grid. A separately
  frozen high-resolution maximum is reported because maxima are grid-sensitive.

For coil types 1 through 5, the tuples `(L/a, d/a, kappa*a, c/a, I_MA)` must round
to:

1. `(18.07, 0.595, 1.673, 0.953, 1.586)`;
2. `(20.82, 0.524, 1.669, 0.868, 1.532)`;
3. `(21.84, 0.512, 1.784, 0.880, 1.422)`;
4. `(22.83, 0.488, 2.028, 0.944, 1.313)`;
5. `(22.35, 0.488, 2.026, 0.992, 1.216)`.

Each value uses a half-unit tolerance in its final printed decimal place. Coil
ordering and the definitions of `d` and `c` must be confirmed from the authors'
data rather than inferred from geometry.

## Physics checks

- VMEC convergence is checked from force residuals and termination state, not
  merely from the legacy integer flag.
- Volume-averaged beta must reproduce 0.02; exact tolerance will be the larger of
  the source solver tolerance propagated to beta and the publication rounding
  interval `[0.0195, 0.0205)`.
- QI residual, second-invariant spread and maximum-J slope fraction are evaluated
  with the same generic interfaces used for the Goodman 2022 bridge.
- Coil-generated and target equilibria are compared separately; preserving QI
  after coil ripple is a protected objective.
- A free-boundary beta scan, island topology and fast-particle/neoclassical
  screening are validation outputs, never hidden training objectives.

## Acceptance rule

Paper metrics alone are necessary but not sufficient. Admission requires all raw
file hashes and conventions, successful reconstruction from coils, and an
explanation for every failed protected metric. Figure digitization is not an
authoritative substitute.
