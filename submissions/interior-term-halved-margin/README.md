# Six-coil fit with an interior field term and halved margins

Arm I of the [interior-term record](../../docs/optimization/ISSUE98_INTERIOR_TERM.md)
(#98; reference401; contributor run by @pjckoch with Claude). The active fitter ran with
`--margins halved --interior-weight 0.05`. The interior term is the method of
[#12](../interior-pass-headroom-continuation/README.md), and the halved margins come
from [#70](../halved-margin-six-coil/README.md). It passes
[acceptance v2](../../docs/validation/ACCEPTANCE_V2.md) and fails the original v1
limits. It is **not an accepted reactor design**: magnetic surfaces, transfer of the
Step 3 benefit, pressure and engineering remain open.

## Reproduce and modify

From the repository root, Python 3.11+; no installations or native artifacts:

```bash
python fusion.py public evaluate --candidate submissions/interior-term-halved-margin/candidate.json --output results/interior-term-report.json
python fusion.py public audit --report results/interior-term-report.json --output results/interior-term-audit.json
python fusion.py public dense-boundary --candidate submissions/interior-term-halved-margin/candidate.json
python fusion.py public normalized-interior --candidate submissions/interior-term-halved-margin/candidate.json
```

Use fresh output paths. The candidate file has SHA-256
`a7e3953d525347910ac68e48d5bff8c9eef5f882af351c3b71f57156c257ca44`.

| Public diagnostic | [Halved-margin fit](../halved-margin-six-coil/README.md) | This geometry |
| --- | ---: | ---: |
| Sampled normal RMS, fixed current | 0.00148216 | 0.00158357 |
| Sampled interior-vector RMS, fixed current | 0.03546733 | **0.03410069** |
| Dense boundary RMS / maximum, 64 × 64 grid | 0.0017283 / 0.0080629 | 0.0018082 / 0.0080768 |
| Sparse interior RMS, flux-normalized | 0.00832837 | **0.00171482** |

Computed 13 October 2026 with the unchanged public evaluator; the replay audit passes
(`report_replay_pass: true`, `independent_implementation: false`,
`physical_admission: false`). The boundary is slightly worse than the halved-margin
fit; the interior is about five times better.

## Native result and limits

Shared checks on the 128 × 128 fine grid with flux-normalized current (305,275.1 A):
boundary RMS **0.0018082**, plain mean **0.00150**, maximum **0.00833**; interior RMS
**0.00184 / 0.00183 / 0.00183** at the three resolutions. `check_coils.py` on this
file reproduces the fit's own checks. Continuous geometry passes at the finer level
with length ≤ 3.4853 m, coil–coil ≥ 0.06055 m, coil–plasma ≥ 0.1479 m and curvature
≤ 11.022 /m. The margins are thin: coil–coil distance is 0.55 mm above its limit.
Ten traced field lines stay confined for 200 transits with signed-ι mismatch
≤ 0.0049 (interpolated field); that is not a nestedness proof.

All native runs used a vmecpp-regenerated reference401 Wout (`0f2b626c…`), not the
maintainer's archive. The search was unconverged (time budget). The fit targets
reference401, not the improved Step 3 plasma. Verdicts: acceptance v2 **pass**; v1
fail (boundary RMS limit 1e-4, maximum 1e-3). v2 was set with reference401 results known.
