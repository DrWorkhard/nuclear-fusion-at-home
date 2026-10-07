# The continuation does not supply a complete qualified flux-label grid

**Result: 19/20 points qualify; diagnose the failed reconstruction before launch
matching.** The same candidate that recovered the shallow #26 wells fails the
nominal s=0.5, geometric theta=pi launch. All 20 traces complete at least 320
transits and all controls pass; software completion is not numerical qualification.
Clean producer/evaluator and prospective protocol:
`3198a16c006e731aa62dba1588fd69d17bfa0c05`,
`docs/optimization/ISSUE48_CONTINUATION_LABELS.md` in this snapshot.

The failed point's final angular gap is 1.240256 rad (limit 0.4), last-prefix label
change 0.0424514 (limit 0.0005), and worst held-out radius error 0.0027803 m
(limit 0.0001). Subset label agreement and full/subset quadrature also fail.
The middle surface receives no qualified aggregate. All failures remain retained.

| Nominal s | Continuation max absolute offset | Continuation phase spread | Archived reference max offset |
| --- | ---: | ---: | ---: |
| 0.10 | 0.002664 | 0.003835 | 0.001236 |
| 0.25 | 0.004130 | 0.005222 | 0.004145 |
| 0.50 | Unqualified | Unqualified | 0.011721 |
| 0.75 | 0.040281 | 0.016237 | 0.034779 |
| 0.90 | 0.084890 | 0.016664 | 0.068137 |

The historical reference qualified 20/20 under the same estimator. It was not
retraced here; `context/` preserves its original report and manifest-verified
provenance from archive `2ee186bb347245072c98d983a42b06f8e02a16a9`, producer
`130347fe29e03852e257a63d0ce6ab9f828d2c85`. `metadata/unchanged-numerics.json`
records four byte-identical numerical files and ten unchanged helper definitions.
No causal claim follows from the two candidates' different optimization histories.

The single attempt took 991.365 s, within 1,800 s including initialization and
checks. Wall/monotonic elapsed times differ by 0.0202 s, within 5 s. One native
thread, 256 MiB aggregate ceiling and 3/2 GiB initial/live reserves were enforced;
owned process-group cleanup completed. All source/input hashes and 1,662 recorded
native package files matched before/after. The 49 original raw files total
58,491,480 bytes. `raw/` preserves every trace, attempt, control, diagnostic,
receipt and log. `inputs/` preserves the frozen continuation snapshot;
`metadata/` holds configuration, environment identity, source equivalence and checks.

The snapshot is copied unchanged from #26 archive
`2205e4dfd2716028e04682f738346a1e4ea925ac`, SHA256
`73972fc86375fcffa67a44833d1c87016e7ff9d070857aac97acc1dcf335bb97`.
It represents pjckoch's public interior continuation at frozen current
305178.2427715842 A. The original reference401 Wout remains external, identified
in `source-map.json`; no regenerated target or optimizer is used.

From a fresh shallow archive checkout, with NumPy/SciPy and a fresh log path:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python evidence/issue48-continuation-labels-v1/replay.py --manifest-sha SHA_FROM_TAG_ANNOTATION > /tmp/continuation-replay.json
```

Replay has a fixed 900 s budget. It verifies the manifest and distributed source
bindings, recomputes final-prefix/control/subset A-line integrals and reconstruction
diagnostics, and checks saved earlier-prefix, separate-plane and B-fan arithmetic.
It retains failures; it does not independently repeat trajectories, symmetry fields,
native B, Wout geometry or timing. Full scientific repetition additionally needs
the original Wout/native environment and the command in `raw/receipt.json`.

Geometric theta is not PEST alpha. These reconstructed labels do not prove nested
surfaces, island absence, confinement, common action coordinates, benefit transfer
or reactor feasibility. No physical gate changed; #48 remains open. Read-only
agent review is not external peer review. This archive is local only, not published
or remotely verified. Original raw files, Wout and environments remain intact
outside this Git backup. Goodman-derived data retain CC BY 4.0 attribution
(DOI:10.5281/zenodo.7220257); project source is MIT.
