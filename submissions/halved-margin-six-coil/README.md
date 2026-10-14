# Six-coil fit with halved construction margins

The halved-margin arm of the
[construction-margin probe](../../docs/optimization/ISSUE70_CONSTRUCTION_MARGINS.md)
(#70, arm M; reference401; maintainer run). It passes
[acceptance v2](../../docs/validation/ACCEPTANCE_V2.md) and fails the original v1
limits; see also the [leaderboard](../../docs/validation/LEADERBOARD.md).
It is **not an accepted reactor design**: magnetic surfaces, transfer of the
Step 3 benefit, pressure and engineering remain open.

## Reproduce and modify

From the repository root, Python 3.11+; no installations or native artifacts:

```bash
python fusion.py public evaluate --candidate submissions/halved-margin-six-coil/candidate.json --output results/halved-margin-report.json
python fusion.py public audit --report results/halved-margin-report.json --output results/halved-margin-audit.json
python fusion.py public dense-boundary --candidate submissions/halved-margin-six-coil/candidate.json
python fusion.py public normalized-interior --candidate submissions/halved-margin-six-coil/candidate.json
```

Use fresh output paths. Copy the candidate to your own submission folder and use
`public set-coefficient` to edit named values. Report both scores and trade-offs.

| Public diagnostic | [Length-headroom](../length-headroom-six-coil/README.md) | This geometry |
| --- | ---: | ---: |
| Sampled normal RMS, fixed current | 0.00174403 | **0.00148216** |
| Sampled interior-vector RMS, fixed current | 0.03610319 | **0.03546733** |
| Dense boundary RMS / maximum, 64 × 64 grid | 0.0019963 / 0.0094258 | **0.0017283 / 0.0080629** |
| Sparse interior RMS, flux-normalized | 0.01078448 | **0.00832837** |

Computed 13 October 2026 with the unchanged public evaluator; the replay audit passes
(`report_replay_pass: true`, `independent_implementation: false`,
`physical_admission: false`).

## Native result and limits

Shared checks on the 128 × 128 fine grid with flux-normalized current
(307,521.9 A; the public case freezes 294,966.5 A, so public and native scores
differ): boundary RMS **0.0017283**, plain mean **0.00143**, maximum **0.00806**;
interior RMS **0.009015** at all three resolutions. Continuous geometry passes with
length ≤ 3.4852 m, coil–coil ≥ 0.0606 m, coil–plasma ≥ 0.1495 m and curvature
≤ 11.05 /m. The margins are thin: coil–coil distance is 0.6 mm above its limit, and
the length bound passed only at the finer level. Ten traced field lines stay
confined for 200 transits with signed-ι mismatch ≤ 0.0058; that is not a nestedness
proof. The fit targets reference401, not the improved Step 3 plasma.

Verdicts ([evaluation](../../docs/validation/ACCEPTANCE_V2_RESULTS.md)): acceptance v2
**pass**; v1 fail (boundary RMS limit 1e-4, maximum 1e-3). v2 was set with this
result known.

## Identity

The coefficients equal native snapshot SHA-256 `4eab51ebfec6b494…`. Converting this
file back with `scripts/check_coils.py --candidate` reproduced every recorded native
metric bit for bit. Canonical candidate SHA-256 (as printed by `public evaluate`,
independent of line endings): `4f9562f24a22a5d8aa6ae16f3e9d323f53911db7e320d1cc9e7934683ed6879c`.
Raw native outputs remain under the maintainer's ignored
`artifacts/issue70-construction-margins/`.

## Attribution

Candidate data follow the starter's CC BY 4.0 attribution. Credit Goodman et al.'s
underlying plasma data as specified in the
[data provenance](../../examples/clear-coil-samples-v1/README.md#provenance-and-attribution).
The project generated these coil coefficients, starting from the
[length-headroom geometry](../length-headroom-six-coil/README.md). No author
endorsement, Proxima affiliation, state-of-the-art advantage or reactor-performance
claim is implied.
