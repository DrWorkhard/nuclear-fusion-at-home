# Free-boundary holdout protocol

Status: frozen before the first LPQA candidate free-boundary run on 2026-08-31.

## Separation rule

Free-boundary equilibrium is a validation stage, not an optimization objective
in the present project phase. The stage receives only an immutable serialized
coil field, target boundary, profiles, current convention, and toroidal flux.
It emits an evidence record and may reject a candidate. It exposes no gradients
and writes no coil, current, boundary, or profile parameters back to an
optimizer. Any later optimization after a rejection is a new, separately named
experiment; its final candidate must undergo a fresh holdout.

The fixed-boundary objective and squared-flux metric therefore remain cheap
search proxies. A claim that survives them but fails this stage is not an
accepted improvement.

## First pipeline-qualification case

The first input is the serialized LPQA engineering-v1.1 L-BFGS-B candidate. It
is not a feasible magnetic baseline (`squared_flux = 1.10e-6`, versus the frozen
`1e-8` cut-in), so this run qualifies interfaces and failure handling only.

- Four unique coils are exported to a MAKEGRID filament file and expanded with
  `nfp=2` and stellarator symmetry.
- All physical coils are one current circuit. Their relative currents remain in
  the file; `extcur` restores the first unique coil's reference current.
- The enclosed toroidal flux is calculated by the line integral of the
  serialized Biot-Savart vector potential around the target boundary at
  `phi=0`; the sign is fixed by the toroidal field near the target axis.
- The target boundary is truncated to `mpol=6`, `ntor=6` for this first screen.
- VMEC++ vacuum continuation uses `ns=[8,16,31]`, `ftol=1e-9` at every level,
  at most 2,000 iterations per level, `nzeta=24`, and a `101 x 101 x 24` MGRID
  response grid with a 40% R/Z margin around the target boundary.
- A fixed-boundary run with the identical truncated boundary, flux, vacuum
  pressure/current profiles, and numerical resolution is the reference.

## Acceptance for a converged screen

Both runs must converge with finite outputs. The free-boundary result then must
satisfy all of:

1. enclosed volume within 5% of the truncated target;
2. enclosed volume within 5% of the fixed-boundary reference;
3. magnetic-axis R curve within 2% RMS of the fixed-boundary reference, using
   the fixed-boundary mean R as normalization;
4. boundary cross-section RMS distance within 5% of the target minor-radius
   proxy at `phi=0` and at one quarter of a full toroidal turn.

These are screening tolerances, not SQuID-C paper-reproduction tolerances. A
passing result still requires MGRID/resolution convergence, finite-pressure and
current-profile scans, island/topology diagnostics, and an independent solver
or code-version holdout before it supports a design claim.

### MGRID refinement declared after the first passing screen

The standard `101 x 101 x 24` result is repeated with `151 x 151 x 24`, leaving
all other inputs unchanged. The response-grid screen passes if relative changes
in free-boundary volume, aspect ratio, axis iota, and edge iota are each below
0.5%, while the absolute changes in both normalized target-cross-section RMS
errors are below 0.005. This is a response-grid check only; radial/Fourier VMEC
convergence remains a separate requirement for a physics claim.
