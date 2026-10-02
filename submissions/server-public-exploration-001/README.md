# A small base-coil x-translation sweep

Does changing only `coil[0]/xc(0)` by ±10, ±50 or ±100 µm lower both public
sampled errors? Each trial starts from the unchanged bundled seed at reference
and evaluator revision `fb7eda796728103af287685e141132436dc3e92b`. The named
Cartesian coefficient translates base coil 0 and its prescribed symmetry copies;
all other coefficients, metre units, signed currents, targets and gates stay fixed.
This is a narrow exploration, not a new best coil fit or physical acceptance.

| Offset (µm) | `sampled_normal_rms` (512 nodes) | `sampled_inner_vector_rms` (512 nodes) |
| ---: | ---: | ---: |
| 0 (reference) | 0.304207028077 | 0.380434718441 |
| −100 (selected) | 0.304193024356 | 0.380424635173 |
| −50 | 0.304200024671 | 0.380429674784 |
| −10 | 0.304205627149 | 0.380433709386 |
| +10 | 0.304208429129 | 0.380435727658 |
| +50 | 0.304214034572 | 0.380439766146 |
| +100 | 0.304221044156 | 0.380444817902 |

The rule declared before computation selected the offset minimizing the worse of
the two candidate/reference error ratios among trials lowering both errors.
The [candidate](candidate.json) changes `0.9608191138350243` to
`0.9607191138350243` m: normal RMS changes by −0.0000140037212518 (−0.00460335%)
and interior RMS by −0.0000100832683998 (−0.00265046%). All positive offsets
failed to improve either metric; their candidates and full reports are retained.
The selected endpoint is best only within this sweep, not an established optimum.

Nine study evaluations (reference, six offsets, selected repeat and replay) took
22.67 seconds sequentially on Python 3.12.3, one CPU/thread, about 27 MiB peak RSS.
Limits were 12 evaluations, 600 seconds, 1 GiB process address space, 4 GiB retained
outputs and a 1 GiB free-disk reserve. No software failures occurred. The reference
matched saved native fields; the selected repeat report matched exactly and
`report_replay_pass:true`, `independent_implementation:false`.

From the repository root, using fresh output names, reproduce the selected result:

```bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 BLIS_NUM_THREADS=1 OMP_THREAD_LIMIT=1
python3 -I -S fusion.py public evaluate --candidate submissions/server-public-exploration-001/candidate.json --output results/server-public-exploration-check01.json
python3 -I -S fusion.py public audit --report results/server-public-exploration-check01.json --output results/server-public-exploration-audit01.json
```

Local ignored evidence is in `results/public-bounded-exploration-001-attempt1-20261003/`:
`recipe.py`, `run/plan.json` (inputs, source hashes, limits and selection), all seven
`run/trial-*/` candidates/reports/comparisons (including non-improving trials 04–06),
`run/selected/`, `run/replay/report.json`, `run/summary.json` and `run/sha256.json`.
The exact sweep command was:

```bash
python3 -I -S results/public-bounded-exploration-001-attempt1-20261003/recipe.py results/public-bounded-exploration-001-attempt1-20261003/run
```

Retain that directory separately from Git; reruns require a fresh output directory.
SHA-256 identities (file bytes, not the reports' canonical-JSON hashes):

- Candidate: `54428d868d4443170bfe5d0f03b1222d49839ff2a65efdedb61c0047bb8c782d`
- Unchanged case: `6e5c51e54444f620450ab3df9e5d3969afbafd1e259d7b65c5fc9b49d1c0fadd`
- Recipe: `93c7ad5a58386d9dc5cc8f5c67d491bf61ce9430e81647a0c00647ccb2859546`
- Run hash manifest: `9fcf3980b26d12617a7280b91d82446f34450627cfce045b283d7da5874cbbf4`

The 256/512-node fields agree within 2.06e-15 relative across this sweep, but both
use the same public spatial samples. Sparse samples can be overfit; fixed currents
are not flux-normalized, and a same-code replay is not independent validation.
No unseen/fine spatial grid, continuous geometry, confinement or reactor benefit
was checked. `physical_admission:false` and `step4_pass:false` remain unchanged.
Data derive from the starter under CC BY 4.0; credit Goodman et al.'s plasma data
and the project's coil construction as described in the
[provenance](../../examples/clear-coil-samples-v1/README.md#provenance-and-attribution).
