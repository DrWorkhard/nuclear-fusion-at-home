# SQuID-C reproduction contract

Audit correction (2026-09-09): this is a provisional reproduction specification.
The paper anchors below are literature values. Author clarification and an
executable coil/physics evaluator remain required for scientific admission.

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
ambiguous `wout`. The canonical linear-profile result is not explicitly identified
as free-boundary in the paper. The explicitly free-boundary stability scan uses
different pressure profiles. The schema-2 free-boundary role is a provisional
requested artifact; its mapping requires author confirmation.

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
generic intake without case-specific code. Non-wout fixture files are opaque test
payloads: this demonstrates dispatch and validation, not reconstruction. The
summary checks wout version, termination, residuals, beta and the full iotaf
profile when supplied. It reports scientific_admission_pass=false while the
listed unevaluated scientific checks have no implemented evaluator.

## Paper-level coil checks

Relative normal-field error uses the paper's definition
`E = (B dot n_hat) / |B|`. Absolute-value reduction, weights, field composition and
quadrature need author confirmation. The following intervals assume rounding to
nearest; they are not yet executable admission criteria:

- average absolute relative error must round to 0.27 % (interval
  `[0.265 %, 0.275 %)`);
- maximum absolute relative error must round to 1.2 % (interval
  `[1.15 %, 1.25 %)`), subject to reproducing the authors' grid. A separately
  frozen high-resolution maximum is reported because maxima are grid-sensitive.

For coil types 1 through 5, the tuples `(L/a, d/a, kappa*a, c/a, I_MA)` must round
to:

1. `(18.07, 0.595, 1.673, 0.953, 1.586)`;
2. `(20.82, 0.524, 1.669, 0.868, 1.532)`;
3. `(21.84, 0.512, 1.784, 0.88, 1.422)`;
4. `(22.83, 0.488, 2.028, 0.944, 1.313)`;
5. `(22.35, 0.488, 2.026, 0.992, 1.216)`.

Each inferred half-unit tolerance uses the final printed decimal place: coil 3
c/a has half-width 0.005, not 0.0005. The template preserves printed strings. Coil
ordering and the definitions of `d` and `c` must be confirmed from the authors'
data rather than inferred from geometry.

## Physics checks

- VMEC convergence is checked from force residuals and termination state, not
  merely from the legacy integer flag.
- Volume-averaged beta has nominal target 0.02. The old interval
  `[0.0195, 0.0205)` was unsupported and has been removed. Admission tolerance
  requires author output and a numerical-error justification.
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

Primary source: [Goodman et al., sections 2.2, 3 and 3.5](https://doi.org/10.1017/S0022377825100974).
The article license does not establish a license for a separate dataset.
