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

## Portable checks

Without the maintainer's archives, supply a reference401 Wout. One can be regenerated
by vmecpp from the committed input in about 6 minutes:
`vmecpp.run(vmecpp.VmecInput.from_file("evidence/plasma-design-v2/reference-input-401.json"), max_threads=1).wout.save(path)`.
`--wout` rebuilds the three 64×64 interior archives
([`wout_target.py`](../../src/fusion_baselines/wout_target.py)). It accepts the
result as consistent only if the Wout boundary equals the input to 1e-12 and the public starter's
64 interior samples are reproduced to 1e-8. Normalization stays frozen; the measured
B2 is reported. These checks do not establish dense interior identity; reports
label `portable_target.check` as `consistency with public starter` and
`dense_identity_verified` as false. `check_coils.py` runs the same fine, geometry and interior checks on
a snapshot or a public candidate without fitting:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 MKL_NUM_THREADS=1 \
  .native/bin/python scripts/check_coils.py \
  --candidate submissions/length-headroom-six-coil/candidate.json \
  --wout results/wout_reference_regen.nc --output results/my-check
```

Positive control (4 October 2026, macOS, the [portable setup](../validation/ENVIRONMENT.md#portable-native-setup)):
- **Fine boundary and geometry:** reproduce the [archived length-headroom evidence](https://github.com/DrWorkhard/nuclear-fusion-at-home/blob/68db098b664bb072854b687040e103aaafee463c/evidence/coil-headroom-v3.json) to ≤1.5e-15
  (RMS 0.0019962675237, maximum 0.0094257750, length bound 3.4742191 m).
- **Interior:** reproduces 0.0114827 and 0.0114794 to 8e-11.

This control is reference401-only and from the same machine/OS family as the
reported evidence; it is not independent physical acceptance or improved-target
validation.

`check_coils.py` saves its converted `seed.json`, which `fit_coils.py --snapshot … --wout …`
accepts for a portable search.

## Realized-field surfaces

[`scripts/trace_surfaces.py`](../../scripts/trace_surfaces.py) traces a public
candidate's coil field at its flux-normalized current. Ten lines start on target
surfaces s = 0.05–0.95. The Wout must match reference401's symmetry, period count,
401 surfaces, boundary and edge flux before tracing. This establishes consistency,
not identity of its unsampled interior. Native coils must reproduce the public
kernel to 1e-12 at both published points and 64 independent seeded volume points.

Regenerate the Wout from committed input first (requires `vmecpp` in its own
environment; see the [native environment](../validation/ENVIRONMENT.md)):

```python
from pathlib import Path
import vmecpp

path = Path("results/wout_reference_regen.nc")
path.parent.mkdir(parents=True, exist_ok=True)
vmecpp.run(vmecpp.VmecInput.from_file(
    "evidence/plasma-design-v2/reference-input-401.json"), max_threads=1).wout.save(str(path))
```

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 .native/bin/python scripts/trace_surfaces.py \
  --candidate submissions/length-headroom-six-coil/candidate.json \
  --wout results/wout_reference_regen.nc --output results/my-surfaces --transits 200
```

The preserved local archive Wout is an alternative if already available; a fresh
clone does not include it. The interpolant must agree pointwise with the direct
field to 1e-6. This does not bound accumulated trajectory error. Confirm a positive
candidate with the same command plus `--direct` and a new output directory;
compare signed iota and the saved Poincaré crossings (`poincare.npz`/`.png`).
Direct mode bypasses interpolation entirely.

`all_confined_and_iota_matching` requires every line to stay inside the target,
complete at least the requested transits, and match **signed** iota within 0.02.
A transit stopping event is distinct from boundary escape; reaching the integration
time cap early cannot pass. The gridded stopping classifier (h = 0.02 m) can stop
lines a few mm inside the boundary. A `boundary` exit therefore requires an exact
point-in-section test of the stop point. Unconfirmed stops are reported as
`classifier_stop_inside_target`, which is inconclusive and cannot pass. The summary does not measure nestedness or island
widths. Plots are exploratory, not a nested-surface proof or physical acceptance.
The improved Step 3 target, edge s > 0.95 and benefit transfer remain untested.
[Confirmation, 4 October 2026](https://github.com/DrWorkhard/nuclear-fusion-at-home/tree/evidence-pr18-trace-confirmation-2026-10-04/evidence/pr18-trace-confirmation-2026-10-04)
uses clean producer `df9db024ef6170df820649e61cccd868f65f0b88`, archive `21886ce`.
For length-headroom-six-coil, direct and interpolated runs both complete 200
transits for 10/10 lines; maximum signed-iota mismatch is 0.004951. Between methods,
iota differs by at most 3.70e-6 and corresponding crossings by 0.097 mm. These
are same-machine diagnostics using the original Wout, not a nestedness proof or
physical acceptance. Other earlier positive summaries still need corrected reruns.

For old results, use their [original revisions](../validation/REPRODUCING_RESULTS.md),
not this prospective search. Evidence is linked from immutable tags; local raw outputs are preserved.
