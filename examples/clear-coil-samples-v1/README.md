# A real-coil starter, not a feasible stellarator

Six nonplanar base coils (Cartesian Fourier order5),24 symmetry-related physical
filaments, frozen signed currents, and192 field-evaluation points. This is the
`reference-n6` starting geometry from our independently audited field-start study.
Its field quality fails the full research acceptance limits. It is a useful
reference and a starting point for contributions, **not a reactor design**.

Run from the repository root with Python3.11 or newer, no installation:

```bash
python fusion.py public demo --output results/first-demo
python fusion.py public evaluate --candidate examples/clear-coil-samples-v1/candidate.json --output results/seed.json
python fusion.py public audit --report results/seed.json --output results/seed-audit.json
```

Use new output names on repeated runs; existing evidence is never overwritten.
The report contains the candidate, case/code digests,256/512-node field arrays,
sampled errors and explicit scope flags. A replay audit uses the same public
evaluator, so is not an independent implementation or physical acceptance.

## Files and conventions

- `candidate.json`: an editable copy of the original six-coil coefficients.
  `parameter_names` defines the exact order; metres, `c0,s1,c1,...,s5,c5` per
  Cartesian axis, with parameter t∈[0,1]. Do not reorder unlabeled arrays.
  Exactly: `parameter_names[33*i + 11*axis + k]` labels
  `base_coefficients[i][axis][k]`, with zero-based coil `i`, axis `0=x,1=y,2=z`
  and component `k=0..10`. Use `public set-coefficient --help` for named edits.
- `case.json`: authoritative fixed data for this version: seed, symmetry
  matrices, signed currents in amperes, target B² and three groups of64 points.
  B is in tesla, A in tesla-metres, coordinates in metres at the reference's
  normalized equilibrium scale. This is not a plant-scale engineering model.
- `manifest.json`: hashes of both data files. These establish identity inside
  a trusted project checkout, not independent authenticity of an unknown fork.

Physical coordinates use the historical right-row convention x'=xQ; coefficient
column tensors therefore transform by Qᵀ. Current is fixed by the case and is
not a candidate parameter in this profile. In particular, candidate evaluation
does **not** restore target flux after changing shape. Do not compare its sampled
numbers to the historical full-surface, flux-normalized objective as if identical.

The64 points per group are selected by floor(k·(N−1)/63), k=0,…,63, from each
previously stored array. They are public, sparse, and are not a hidden holdout.
Boundary weights are renormalized over this subset. Lower sample error can
overfit this sample and says nothing about continuous geometry or confinement.

## Provenance and attribution

This is a **new derived packet**, not an edited historical record. Its manifest
and parent digests bind the original native seed bundle, input equilibrium,
output equilibrium, raw arrays and independent audit at project revision3334f1e.
The originals and their private-machine paths have not been rewritten.
The completed exporter is `scripts/export_public_starter.py` at revision
`8c5753c`; see [historical reproduction](../../docs/validation/REPRODUCING_RESULTS.md).
Ordinary users need only this packet.

Underlying plasma configuration: Alan Goodman, *Data for paper “Constructing
precisely quasi-isodynamic magnetic fields”*, version1.0,18October2022,
[doi:10.5281/zenodo.7220257](https://doi.org/10.5281/zenodo.7220257),
[CC BY4.0](https://creativecommons.org/licenses/by/4.0/).
License/creator/version checked against the Zenodo record API on2026-09-23.
Related publication: Goodman et al., J. Plasma Phys.89 (2023),
[doi:10.1017/S002237782300065X](https://doi.org/10.1017/S002237782300065X).

Changes: the project performed a401-surface vacuum equilibrium calculation,
constructed its own coil seed, evaluated fields and selected the stored samples.
The three JSON data files are distributed under CC BY4.0 with this attribution.
Project source code remains under the repository's MIT license. No affiliation,
author endorsement or reproduction of the full published dataset is implied.

See [public quickstart and limits](../../docs/validation/PUBLIC_QUICKSTART.md)
and [the original numerical result at the freeze tag](../../docs/validation/REPRODUCING_RESULTS.md).
