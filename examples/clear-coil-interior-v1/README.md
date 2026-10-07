# Dense interior targets for both matched fits

This derived packet makes the original and improved #25 target fields usable
without VMEC, SIMSOPT, NumPy or a historical evidence download. It is separate
from `clear-coil-samples-v1`; that case's fixed-current reports are unchanged.
The candidate schema still describes its six order-5 coil shapes. Select the
target explicitly when using these shapes with the new diagnostic:

```sh
python fusion.py public dense-interior --target reference401 --candidate examples/clear-coil-interior-v1/reference401-candidate.json
python fusion.py public dense-interior --target selected401 --candidate examples/clear-coil-interior-v1/selected401-candidate.json
```

The standard-library computation may take several minutes. Its default 600 s
ceiling can be lowered with `--seconds`. Failures exit nonzero without a completed
JSON report. A completed calculation is not physical acceptance.

Each target JSON contains 12,288 rows `[x,y,z,Bx,By,Bz]`, Cartesian metres/tesla,
on target surfaces s=0.25,0.5,0.75. Each surface has 64 geometric toroidal angles
φ=πj/64 and 64 VMEC poloidal angles θ=2πk/64, excluding periodic endpoints;
θ varies fastest, then φ, then s. These are target coordinates, not qualified
realized-flux labels. The metric equally weights these samples and divides by
the frozen target B²; it is not a volume integral. Each surface score uses the
same global B² denominator.

The target boundary defines a 256-point φ=0 flux loop. The command uses 256 coil
nodes to normalize the public case's signed current ratios to the saved negative
target flux, then freezes that current for the 512-node interior field. Wrong-sign
or zero flux is rejected. The original 0.01 interior limit is displayed as a
metric comparison only. Quadrature convergence, geometry, boundary errors,
realized surfaces and confinement still need separate checks.

The manifest fixes both target packets and the two original fitted coil shapes.
Source: published archive
[`05a4511`](https://github.com/DrWorkhard/nuclear-fusion-at-home/tree/05a4511084912fea9bd8d03e81f01018882396b8/evidence/issue25-matched-v1),
clean producer/evaluator `a551289e63e44d7dbae7b5d5a0e5f4b6026db257`.
Every target row is copied exactly from that target's `fit/interior/level-2.npz`;
input, Wout and NPZ hashes are embedded. Original Wouts are not required or
distributed by this packet. Export qualification does not replace the native
selected-Wout identity gate. The exporter verifies the published 6,258-entry
manifest, all coordinates/field components and the physical current-ratio mapping.

Underlying configuration: Alan Goodman, *Data for paper “Constructing precisely
quasi-isodynamic magnetic fields”*, [DOI:10.5281/zenodo.7220257](https://doi.org/10.5281/zenodo.7220257),
CC BY 4.0. Changes: project vacuum equilibrium calculation, improved Step 3
boundary, fitted coils, dense target sampling and this JSON extraction. These
derived data retain CC BY 4.0 attribution; project code is MIT. No endorsement
or new physics qualification is implied. See [NOTICE](../../NOTICE.md).

The [qualification record](../../docs/validation/ISSUE10_DENSE_INTERIOR.md)
states the exact source revision, checks and remaining limits. This preparation
is local; publication is pending.
