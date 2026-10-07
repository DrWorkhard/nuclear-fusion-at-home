# A spread 64-point layout improves the known cases but misses its accuracy hurdle

Decision: do not promote or retune this layout here. The single frozen midpoint
layout corrects the headroom/counterexample ranking and improves relative RMS
agreement in all three known cases. At 512 coil nodes, its relative error is
2.9150% for the seed, 6.7302% for headroom and 6.5453% for the counterexample.
The latter two exceed the preregistered 5% hurdle. Maximum relative 256/512 coil
quadrature change is 6.04e-14. This is a negative pilot, not a new public case,
independent physics verification or general ranking guarantee.

Clean producer/evaluator: `43d455116a860a745993ed9169cd0484aa8b606c`.
The full prospective protocol and code/tests are preserved at their original paths
in this snapshot. The original public case, candidate bytes and evaluator are
unchanged from parent main `7386e4b013e4a777cdf37e7a7a2e02988547d742`.
No target, signed current, fitting or physical acceptance criterion changed.

One run completed in 68.5875 s supervised total (68.3690 s worker), within
300 s worker including startup / 360 s outer, 32 MiB aggregate output, 3/2 GiB
initial/live disk reserve and 5 s clock tolerance. Source/input/executable identities
matched before/after and owned-process cleanup succeeded. The outer receipt is
authoritative for completion. Fourteen raw files (3,822,740 bytes), including all
six full-grid B arrays and their signed normal errors, remain byte-for-byte under
`raw/` and separately at `/private/tmp/issue8-spread-sampling-v1`.

All 18 distributed source/input bindings resolve within the snapshot using
`metadata/source-bindings.json`. The nineteenth binding is the preserved external
Python executable; its hash and version are recorded, not distributed. Site
packages were disabled with `-I -S -B`, and no native solver or external Wout was
used. The reviewed supervisor helper is included unchanged in metadata; the
study sets its aggregate cap to 32 MiB and adds the 360 s guard. Its original
source SHA256 is `dfc4e8cb750e28aa8d399f6c64691659674a874a1c2f1126133424d82b3cd15b`.

## Reproduction

Original command from the clean producer, using a fresh output path for any new run:

```bash
env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin TMPDIR=/private/tmp \
  PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  VECLIB_MAXIMUM_THREADS=1 MKL_NUM_THREADS=1 \
  /Users/sebastianwirkert/workspace/fusion/.venv/bin/python -I -S -B \
  scripts/check_spread_sampling.py \
  --output /private/tmp/issue8-spread-sampling-reproduction \
  --revision 43d455116a860a745993ed9169cd0484aa8b606c \
  --supervisor /private/tmp/fusion-issue48-continuation-evidence-20261007/scripts/run_continuation_labels.py
```

For relocation, point `--supervisor` at its preserved metadata copy; the source
checkout must be clean at the producer SHA, not the different evidence commit.
All scientific inputs are committed and the field calculation needs only the
standard library. A different Python executable has a new recorded identity.

A fresh shallow checkout of this evidence tag may instead run
`python -I -S -B evidence/issue8-spread-sampling-v1/replay.py --manifest-sha SHA256`.
This verifies the manifest and 18 distributed bindings, reconstructs the geometry,
and recomputes all 24,576 normal errors, RMS reductions, quadrature changes and
promotion checks from the six saved B arrays. It does not recompute fields or
reproduce original Python/timing. Same-kernel arithmetic replay, 60 s limit;
no files written. Everything is local-only pending publication and remote verification.
