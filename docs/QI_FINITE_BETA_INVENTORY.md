# Finite-pressure Goodman data inventory

## Scope declared before metadata inspection, 2026-09-10

The existing, release-MD5-verified Goodman ZIP contains 31 finite-pressure
equilibria and their input files under `Files/configurations/nfp?/beta/`.
The original bootstrap extracted only vacuum configurations. Finite-pressure
maximum-J work is therefore not blocked solely on SQuID-C author data.

The new importer selects exactly these 62 regular files, validates the published
archive MD5 and records SHA-256 for the archive and every member. It refuses an
existing target/output, unsafe paths, duplicate entries and symlinks. Original
vacuum files are not modified. Extraction is an inventory, not an equilibrium
rerun or scientific admission. A failed extraction is retained, not overwritten.

Record actual beta, radial/angular resolution, symmetry, fixed/free-boundary
flag, termination flag, force residuals and finite pressure ranges. Filename beta
labels are descriptive only; no beta or convergence acceptance tolerance is
invented from the names. Missing metadata stays unknown.

Next: select pressure states by an explicit protocol, establish an accessible
fixed-invariant domain on the radial stencil, match individual complete wells
by geometry, refine both tracing and radial differences, and assess derivative
signs without alpha averaging. Neither the inventory nor a sampled negative
derivative can certify global maximum-J.

Run from the repository root after the regular QI bootstrap:

```sh
PYTHONPATH=src .venv/bin/python scripts/bootstrap_qi_finite_beta.py
```

## Inventory result

Implementation 08ac18e preceded the metadata run. All 62 selected files extracted
and matched their SHA-256 values; the release archive SHA-256 is
`e2ad0abf5a474ff35716a67d4882f564a04cbc39c9e9c3dde3e8eb1307ae5dca`.
All 31 wouts report ier_flag=0, stellarator symmetry and fixed boundary. All
pressure arrays are finite. These are reported solver metadata, not an independent
equilibrium validation or a pressure-resolution study.

- nfp1: nominal beta 1%, actual 1.00616064%, ns=51, mpol=8, ntor=14;
  maximum recorded residual 9.925e-15.
- nfp2: 15 nominal beta labels 0.25–3.75%, actual 0.25018170–3.79033452%;
  ns=201, mpol=5, ntor=10; maximum recorded residual <1e-16.
- nfp3: same 15 nominal labels, actual 0.25014859–3.78505178%;
  ns=201, mpol=9, ntor=10; maximum recorded residual <1e-16.

Nine importer tests pass, including path traversal, symlink, missing selection,
hash mismatch and overwrite rejection. Machine-readable evidence is
`evidence/qi-finite-beta-inventory-v1.json`. No maximum-J conclusion follows yet.
