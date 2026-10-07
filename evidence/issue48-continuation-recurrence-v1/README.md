# Saved-point recurrence diagnosis of the continuation failure

The failed continuation s=0.5, geometric theta=pi launch has one resolved angular
reversal in each of its eleven sampled residue sequences on both section planes.
All four qualifying controls have zero reversals. The failed point is not described
by simple monotonic drift over these samples. Its 11-turn return RMS is
0.8321–0.8326 mm, versus 2.2459–3.3841 mm for the controls; its pooled final angular
gap stays 1.240256 rad. These finite samples do not classify islands, continuous
winding, nested surfaces or confinement. Original 19/20 qualification is unchanged.

Producer/evaluator: clean `2baca74707328b27e62a66e6515bda1a553b0f88`.
The prospective protocol, numerical code and tests remain at their original paths
in this snapshot. Five diagnostic function ASTs and `flux_labels.py` were unchanged
from recurrence archive `70619a97df51cd8ccc34d7265e540cb26a2d70db`.
One attempt completed in 1.18399775 seconds supervised total; 60 seconds begins
inside the driver run function, and the 75-second outer budget includes startup.
One thread, 256 MiB output, 3/2 GiB disk reserves and 5-second clock tolerance;
source/input identities and 1,662 native package files matched before and after.
Owned process cleanup succeeded. Original five output files (151,062 bytes) are
preserved under `raw/`; the external originals remain untouched at
`/private/tmp/issue48-continuation-recurrence-v1`.

`inputs/` contains exact original reports, manifests and the five consumed NPZs.
These are explicit subsets of the earlier archives, not complete copies:
continuation `191875d231b396e5960cbd9460a37a6c462b6381` (trace producer
`3198a16c006e731aa62dba1588fd69d17bfa0c05`) and reference
`2ee186bb347245072c98d983a42b06f8e02a16a9` (trace producer
`130347fe29e03852e257a63d0ce6ab9f828d2c85`). Original manifests retain every entry,
including files outside these subsets. All 54 direct source/input bindings of this
diagnostic resolve within this archive via `metadata/source-bindings.json`.
The Python/native environment is recorded, not distributed; no Wout is needed here.
Everything is local-only pending publication and remote verification.

## Reproduction

The original absolute-path configuration and supervisor helper are in `metadata/`.
With the original local paths and preserved native Python, from clean producer:

```bash
env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin TMPDIR=/private/tmp \
  PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  VECLIB_MAXIMUM_THREADS=1 MKL_NUM_THREADS=1 \
  /Users/sebastianwirkert/workspace/fusion/.venv/bin/python \
  scripts/run_saved_recurrence.py \
  --config /private/tmp/issue48-continuation-recurrence-config-v1.json \
  --config-sha fc1c1a2a913a72316c04c05afa0a17d39b6bf4b8ad62056a634bb82136c502d1 \
  --output /private/tmp/issue48-continuation-recurrence-reproduction \
  --revision 2baca74707328b27e62a66e6515bda1a553b0f88
```

For a relocated snapshot use a new configuration with `archive` and
`reference_archive` pointing to `inputs/continuation` and `inputs/reference401`,
`supervisor` to the recorded helper, and `environment` to its recorded identity.
Compute that configuration's SHA256 and retain it. The producer source checkout
must remain clean at its exact revision; the evidence snapshot has a different
commit and cannot be passed off as that producer.

A fresh shallow checkout of this evidence tag can instead run `replay.py
--manifest-sha <recorded SHA256>` with NumPy/SciPy available. The replay verifies
its payload and all 54 source bindings and independently invokes the same recorded
numerical functions on the saved crossings: all five cases, 110 residue sequences,
15 interpolation-prefix records and three analytic controls must agree exactly.
This is arithmetic replay with the same kernels, not independent physics validation,
native environment reproduction, retracing, field calculation or timing replication.
It leaves qualification unchanged. Budget: 60 seconds; no output files are written.
