# Active coil research

One normalized fitter, one set of field/geometry checks.
[Evidence](../STATUS.md) · [Next decision](STEP4_RESEARCH_PROGRAMME.md) ·
[Contribution ideas](RESEARCH_HINTS.md)

## Native workflow

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv/bin/python scripts/fit_coils.py \
  --snapshot artifacts/coil-headroom-v3/run/headroom/selected-snapshot.json \
  --output artifacts/my-fit --seconds 300 --check-seconds 120
```

Requires the preserved [native environment](../validation/ENVIRONMENT.md) and local
reference401 field archives. The snapshot is explicit; the driver no longer loads
an entire chain of previous experiments. Historical absolute artifact paths are
not portable. Use the [public candidate](../../submissions/length-headroom-six-coil/README.md)
for an installation-free contribution.

1. Verify fixed target/source hashes and named physical coil/current mapping.
2. Check derivatives and exact repeat, then run penalized normalized L-BFGS-B.
   Retain completed candidates with sampled geometry/current limits and length
   at most 3.45 m; select the lowest boundary RMS. Probes cannot win; no fallback.
3. Freeze the selected currents. Check two fine boundary grids, continuous
   geometry bounds, three interior resolutions and independent B/A calculations.
4. Save inputs, source identities, attempts, failures, fields and a short result.
   `completed` means diagnostic execution succeeded; it does **not** mean the
   field limits passed or a physical design was accepted.

The prospective search removes inherited coefficient boxes and evaluation caps;
its objective and acceptance limits are unchanged. Length construction target is
3.44 m, acceptance is 3.5 m. Default budgets are 300 s search (including startup)
and 120 s checking, each capped at 1,800 s; output is capped at 256 MiB including
interior files, with 3 GiB initial / 2 GiB live disk reserve. Calls are checked
before and after execution: in-flight native work can overrun, and late checks
cannot claim completion. Use a fresh output directory. Failures remain on disk.

Implementation: [driver](../../scripts/fit_coils.py),
[objective and search](../../src/fusion_baselines/coil_fit.py),
[checks and target intake](../../src/fusion_baselines/coil_check.py).
Independent geometry/field mathematics stay separate from optimization penalties.
This driver supports reference401 only; matched improved-target fitting and
realized-plasma-benefit diagnostics remain to be implemented in the
[next experiment](STEP4_RESEARCH_PROGRAMME.md).

For old results, use their [original revisions](../validation/REPRODUCING_RESULTS.md),
not this prospective search. Evidence is linked from immutable tags; local raw outputs are preserved.
