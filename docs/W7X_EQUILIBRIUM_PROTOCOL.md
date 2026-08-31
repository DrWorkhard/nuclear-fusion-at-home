# W7-X equilibrium regression protocol

## Purpose

The W7-X equilibrium is a software and physics regression, not a claim that a
fixed-boundary VMEC calculation validates the complete as-built machine. The
project gate and full-file cross-code V&V are reported separately.

## Immutable inputs and implementations

- Input: StellCoilBench
  `input.W7-X_without_coil_ripple_beta0p05_d23p4_tm`, SHA-256
  `f927a2a4d0adba1dc12406ae9fbf51a82d38cb6f00f0b9cab1ff8908ef35fac8`.
- Under test: VMEC++ 0.7.3 at commit
  `1d7e09941c89210be95b6b20f4d4d555f0a63096`.
- Independent implementation: STELLOPT tag `v251` at commit
  `e59affaec7713aee8da1f1bccdf05cc0612c12e3`, which reports VMEC 8.52.
- Array tolerances: Proxima's `vmecpp-validation` at commit
  `4017e53095c09e2ead20c6bb64c12796583520c5`.

The tracked STELLOPT patch turns on Nyquist output and corrects the NESTOR
argument ordering exactly as required by the upstream VMEC++ validation README.
Its third source change only updates the GNU Fortran `stat` buffer length, and
the remaining changes select the local Apple Silicon compiler and libraries.

## Project physics gate

The project gate implements WP2's original scope. It passes only if:

1. both outputs report VMEC 8.52 and use identical Fourier-mode arrays;
2. both reach `fsqr`, `fsqz`, and `fsql <= 1.01e-12`;
3. `aspect`, `volume_p`, `betatotal`, `iotaf`, magnetic axis, surface geometry,
   `|B|`, and contravariant magnetic coefficients pass the pinned fixed-boundary
   array tolerances;
4. reconstructed real-space `R`, `Z`, `B_R`, `B_phi`, and `B_Z` pass Proxima's
   W7-X tolerances both on a `37 x 36` grid and on an unconsumed `73 x 72` grid.

This selection follows the project plan's geometry, aspect, beta, iota, and
selected magnetic-metric scope. It is not called full `wout` validation.

## Full-file V&V and known failures

All 59 fixed-boundary fields are also compared without exceptions. That stricter
test currently passes 56/59 and therefore fails overall:

- `chipf` differs only at the magnetic axis: VMEC++ writes zero and VMEC 8.52
  writes `2.15`; every interior point passes the fixed-boundary tolerance. Source
  inspection shows that current VMEC++ initializes the assembled full-grid array
  to zero and updates only the interior and edge in the current-constrained path.
- `presf` and `pres` miss bit-near tolerances. Their largest absolute differences
  are below `7.5e-6 Pa`, and their L-infinity-relative differences are below
  `2.7e-11`.

The older available SIMSOPT reference reports VMEC 9.0. Comparing VMEC++ 8.52 to
that file passes only 47/59 fixed-boundary fields and produces a broad
`bsubsmns` mismatch. The matched 8.52 reference reduces the maximum absolute
`bsubsmns` coefficient difference to `2.10e-8`; the 9.0 comparison is retained
as a version-compatibility warning rather than treated as a failed physical
equilibrium.

## Reproduction

```bash
./scripts/bootstrap_vmecpp.sh
./scripts/bootstrap_vmec2000.sh
uv run python scripts/run_vmecpp_equilibrium.py \
  external/stellcoilbench/plasma_surfaces/input.W7-X_without_coil_ripple_beta0p05_d23p4_tm \
  artifacts/vmecpp/w7x-stellcoilbench
uv run python scripts/run_vmec2000_reference.py \
  external/stellcoilbench/plasma_surfaces/input.W7-X_without_coil_ripple_beta0p05_d23p4_tm \
  artifacts/vmec2000/w7x-v852-reference
uv run python scripts/compare_wout_core.py \
  artifacts/vmecpp/w7x-stellcoilbench/wout.nc \
  artifacts/vmec2000/w7x-v852-reference/wout_w7xbaseline.nc \
  evidence/w7x-vmecpp-v852-comparison.json
uv run python scripts/audit_w7x_equilibrium.py \
  artifacts/vmecpp/w7x-stellcoilbench/wout.nc \
  artifacts/vmec2000/w7x-v852-reference/wout_w7xbaseline.nc \
  evidence/w7x-vmecpp-v852-comparison.json \
  evidence/w7x-equilibrium-v852-vnv.json
```

The native VMEC reference took 2,922.57 seconds on the canonical M1 host.
Generated files remain ignored; their hashes, toolchain, dynamic libraries,
metrics, and normal-termination marker are recorded in evidence.

Primary implementation sources:

- <https://github.com/proximafusion/vmecpp>
- <https://github.com/proximafusion/vmecpp-validation>
- <https://github.com/PrincetonUniversity/STELLOPT>
