# Ubuntu server public-reference reproduction — 2 October 2026

Question: does the portable public reference reproduce on this Ubuntu server at
source revision `fb7eda796728103af287685e141132436dc3e92b`? **Yes, within the
public sampled-field profile.** This contributor report verifies the supplied
setup run `20261002T110414Z-3`; it makes no new design or physical acceptance claim.

The checkout was clean at that revision before this documentation change.
The server reports Ubuntu 24.04.5 LTS (Noble Numbat), Linux
`7.0.0-28-generic`, x86_64, glibc 2.39, and `/usr/bin/python3` version
`3.12.3 (main, Aug 31 2026, 10:18:26) [GCC 13.3.0]`.
No packages or native research dependencies were needed.

Commands ran from the repository root. Setup exit statuses and wall times below
come from the supplied manifest; the referenced local stdout/stderr files were
read to confirm their results. Logs `0.stdout`/`0.stderr` through
`4.stdout`/`4.stderr`, in table order, are retained in the contributor’s private local reproduction archive
(not distributed with this report).

| Exact setup command | Exit | Seconds | Observed result |
| --- | ---: | ---: | --- |
| `/usr/bin/python3 fusion.py public cases` | 0 | 0.166 | `clear-coil-samples-v1` available |
| `/usr/bin/python3 fusion.py public demo --output results/server-reproduction-20261002T110414Z-3` | 0 | 10.752 | `reference_reproduced:true` |
| `/usr/bin/python3 -I -S scripts/test_public.py` | 0 | 11.055 | 48 tests, `OK` |
| `/usr/bin/python3 -I -S scripts/check_docs.py` | 0 | 0.468 | PASS, 0 errors |
| `/usr/bin/git diff --check` | 0 | 0.010 | No whitespace errors |

The saved report gives both dimensionless errors below at **both 256 and 512
quadrature nodes per filament**; each has zero change from the reference in the
512-node comparison. These are numerical errors, not command failures.

| Metric | Value |
| --- | ---: |
| `sampled_normal_rms` | 0.3042070280768691 |
| `sampled_inner_vector_rms` | 0.3804347184410837 |

The 256-node B/A comparison with saved native reference arrays passes its
`5e-10` tolerance (largest relative error `8.061439928464242e-16`). The saved
audit has `report_replay_pass:true`, `seed_native_reference_pass:true` and
`independent_implementation:false`. All four recorded evaluator file hashes
match both the checkout and the pinned Git revision; the case, candidate template
and data manifest also match that revision byte-for-byte. The case digest is
`6e5c51e54444f620450ab3df9e5d3969afbafd1e259d7b65c5fc9b49d1c0fadd`.

The three original files remain unchanged in ignored
`results/server-reproduction-20261002T110414Z-3/` (128,740 bytes total).
Recomputed **file-byte SHA-256** hashes match the setup manifest; these differ
from the canonical JSON digests embedded in the audit.

| File | SHA-256 |
| --- | --- |
| `candidate.json` | `a4d242dd0eab58226d3f435becb819e1cf0fb6b457bb942e293e70c7592c2a1e` |
| `report.json` | `c9b2a739b5cbdf2e7a3d79e675e15bfd852522db6f913959bba0a81502fa450d` |
| `audit.json` | `952f8afebbd076e86db780a0b10815b21bede4a3037f5952acc4fe0f3362f540` |

Contributor verification repeated the isolated public-test and documentation
commands and `git diff --check` above: all exited **0**, with **48 tests OK** and
**0 documentation errors**. A fresh replay also exited **0**:

```bash
/usr/bin/python3 -I -S fusion.py public audit --report results/server-reproduction-20261002T110414Z-3/report.json --output results/server-reproduction-20261002-worker-attempt2/audit.json
```

Its audit is byte-identical to the original. Verification logs, data provenance
and the exact argument-array recipe are retained in ignored
`results/server-reproduction-20261002-worker-attempt2/`. Verification used one CPU,
one sequential job and BLAS/OpenMP thread limits of one. For another demo or audit,
use a fresh output path; do not overwrite these retained runs.

This is a server portability observation and same-code replay, not an independent
implementation, external peer review, or native research-suite reproduction.
The six base coils generate 24 symmetry-related filaments at 192 public points
(64 boundary, 64 interior, 64 loop), with fixed signed currents and fixed target
conventions. Coordinates are metres, B tesla and A tesla-metres; currents are not
renormalized to restore target flux. Sparse public samples can be overfit;
quadrature agreement does not bound all spatial or modeling errors. Full-surface
fields, continuous clearance/curvature, flux normalization, magnetic surfaces and
islands, QI/confinement and benefit transfer, finite pressure, finite-build
engineering and robustness remain unchecked. The research limits `1e-4` and
`0.01` belong to a different full-grid, flux-normalized profile and cannot be
used as public acceptance ratios. **`physical_admission:false` and
`step4_pass:false` remain unchanged**; neither software success nor these scores
establish a feasible or better reactor. See the [quickstart](PUBLIC_QUICKSTART.md)
and [data conventions and attribution](../../examples/clear-coil-samples-v1/README.md).
