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
