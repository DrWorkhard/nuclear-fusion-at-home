# Millimetre perturbations selected on sparse coil scores

The selected +2 mm change lowers sparse normal RMS by 10.46% but raises
dense boundary RMS by 1.47%. This is a sampled/dense ranking counterexample.

Question: does a small, fixed search from the [length-headroom geometry](../length-headroom-six-coil/README.md)
retain a sampled-score advantage on the full boundary and under the separate
flux-normalized interior diagnostic? The decision is whether its selected
geometry deserves a separate native check. No native fitting programme is extended.

The prespecified 27 configurations are the baseline; each of -2, -1, -0.5,
+0.5, +1 and +2 mm on each named coefficient below separately; then all eight
lexicographically ordered +/-1 mm combinations. Their coordinate order is
`coil[0]/xc(0)` (Cartesian x constant), `coil[2]/zc(1)` (z cosine mode 1),
`coil[4]/ys(1)` (y sine mode 1). The recipe applies metre-valued offsets from the
same baseline through `set_coefficient`. This tests 5–20 times the earlier
100-micrometre scale, including coupled changes; it is not an adaptive search.

Selection uses only nonbaseline trials lowering **both** 512-node fixed-current
sampled RMS errors. Minimize normal RMS, then interior RMS, then the offset tuple.
If none qualifies, the same ordering over all nonbaseline trials produces a
labelled trade-off/negative diagnostic. Freeze the selected JSON before audit,
dense-boundary checks at 256/512 coil nodes, and normalized-interior checks.
The baseline's previously public dense values were known beforehand. These are
public, same-kernel diagnostics, not an independent implementation or hidden holdout.

## Result: the sparse boundary advantage reverses

All 27 configurations completed. Among the 26 alternatives, seven lowered both
512-node sampled errors, five lowered only normal RMS, five only interior RMS,
and nine neither. Selection froze trial 18: **+2 mm on `coil[4]/ys(1)`**,
from 0.06864646109874588 to 0.07064646109874588 m; every other coefficient is
unchanged. This is an endpoint of the fixed set, not an established optimum.

| Diagnostic | Coil nodes | Headroom baseline | Selected | Relative change |
| --- | --- | ---: | ---: | ---: |
| Fixed-current sampled normal RMS | 256 / 512 | 0.00174403225046 | 0.00156163439219 | -10.45840% |
| Fixed-current sampled interior RMS | 256 / 512 | 0.0361031885135 | 0.0360880049261 | -0.04206% |
| Dense boundary normal RMS (4096 points) | 256 / 512 | 0.00199627036175 | 0.00202555464278 | +1.46695% |
| Dense boundary maximum | 256 / 512 | 0.0094257750102 | 0.0095228314454 | +1.02969% |
| Sparse flux-normalized interior RMS | 512 field / 256 flux | 0.0107844754376 | 0.0107230312716 | -0.56975% |

For each 256 / 512 row, both resolutions round to the displayed values. Across
the baseline and selection, the largest absolute quadrature differences are bounded by
7.75e-17 sampled normal, 4.17e-17 sampled interior, 5.64e-18 dense RMS and
1.53e-16 dense maximum; the largest reported relative B/A difference is 1.57e-15.
This tests filament quadrature, not spatial-grid independence.

Fixed maximum absolute current stays **294966.466322217 A**. Flux normalization
preserves signed ratios and uses a 256-point loop: maximum absolute current is
**308140.584431910 A** for baseline and **308120.023020396 A** for selection
(a 20.561411514 A decrease). Its 256/512-coil-node difference is zero at the
reported precision; sparse normalized interior uses 512 field and 256 flux nodes.
Uniform current scaling leaves the normal metric invariant.

**Decision:** do not prioritize native checking on this sampled-score gain alone.
The selected geometry worsens dense boundary RMS and maximum while slightly
improving sparse normalized interior. It is a reproducible ranking counterexample,
not a joint field improvement. Both dense boundary limits (1e-4 RMS, 1e-3 maximum)
still fail. No other trial was selected or tuned after these diagnostics.

Source: `e88421254c172a3060ef1040440805ac29a154e7`, unchanged public evaluator and
inputs, Python 3.12.3. Selection replay passed (`independent_implementation:false`).
The executed README recipe used **131.54 s**, including startup, and retained
3.5 MB of run output: 26 new sampled reports, one new selected replay, two new
dense checks and one new normalized-interior check. Four baseline results were
reused only after matching source/input/Python identities and artifact hashes.
No failed numerical operations occurred. Full logs are local-only, not distributed;
the complete recipe below regenerates the experiment without them. Acquisition
used the existing checkout; no fresh network clone or native reproduction was run.

| Identity | SHA-256 |
| --- | --- |
| Baseline candidate, canonical JSON | `204df06fb52b48d54f0c6d7a303a61440266041012d87f081d80c2ba263ff060` |
| Selected candidate, canonical JSON | `727245c843ffaeeb8629c2e551e5713c609643cc258f8c2e98929b185a61a4c8` |
| Bundled case, bytes | `6e5c51e54444f620450ab3df9e5d3969afbafd1e259d7b65c5fc9b49d1c0fadd` |
| Reference input, bytes | `57394ef682f3c6399faa03012abc02da2eb1ce40703a4f99640ece3d07e5691f` |


## Complete recipe

From the repository root with Python 3.11+, create `results/` if needed,
then save the following block as
`results/millimetre-study.py`, then run `python3 -I -S -B results/millimetre-study.py results/millimetre-study-run`.
On Windows use an installed Python 3.11+ launcher, for example `py -3.12`.
Choose fresh paths. The default run uses only repository inputs; no local cache,
native package, archive or network is required. Every candidate, full report,
failure, operation time/hash and frozen selection stays under the output path.

The study has a 600-second wall limit including numerical process startup,
one CPU/job/thread, 2 GiB memory, 128 MiB new output and 2 GiB free-disk reserve.
The recipe enforces subprocess timeouts, disk/output checks, and Linux CPU affinity;
on Unix it bounds each of the parent and single child to 768 MiB of address space.
On Windows apply the memory limit through the host. A failed/incomplete run must
remain labelled incomplete; do not extend the budget or tune after dense checks.

For exact retained evaluations only, an optional second argument supplies a
`reuse.json` manifest. Source/input/Python identities and artifact hashes must
match; the recipe still regenerates all configurations and the selection.
Omit it to recompute everything. Canonical candidate identities in the table use
`sha(canonical(load(path)))` from `fusion_public.data`, independent of checkout
line endings; generated candidate files use LF. Local file-freeze hashes are
also saved before the dense checks.

```python
import itertools
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

START = time.monotonic()
OUT = Path(sys.argv[1])  # A fresh directory under results/, from the repository root.
OUT.mkdir(parents=True, exist_ok=False)
for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[key] = "1"
if hasattr(os, "sched_setaffinity"):
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
try:
    import resource
except ImportError:  # Windows: use a host memory limit; the calculation is stdlib-only.
    resource = None
if resource is not None:
    # Parent plus one child stay below 2 GiB, including interpreter overhead.
    resource.setrlimit(resource.RLIMIT_AS, (768 * 1024**2, 768 * 1024**2))

sys.path.insert(0, "src")
from fusion_public.data import canonical, load, load_case, sha  # noqa: E402
from fusion_public.usability import set_coefficient  # noqa: E402

BASE = Path("submissions/length-headroom-six-coil/candidate.json")
NAMES = ("coil[0]/xc(0)", "coil[2]/zc(1)", "coil[4]/ys(1)")
METRICS = ("sampled_normal_rms", "sampled_inner_vector_rms")
baseline = load(BASE)
case, case_sha = load_case()
paths = sorted(Path("src/fusion_public").glob("*.py")) + [
    Path("fusion.py"), Path("examples/clear-coil-samples-v1/case.json"),
    Path("examples/clear-coil-samples-v1/manifest.json"),
    Path("examples/clear-coil-samples-v1/candidate.json"),
    Path("evidence/plasma-design-v2/reference-input-401.json"),
]
identity = {"sha256": {str(p): sha(p.read_bytes()) for p in paths},
            "baseline_canonical_sha256": sha(canonical(baseline)), "python": sys.version}
cache = load(sys.argv[2]) if len(sys.argv) == 3 else {"identity": identity, "operations": {}}
assert cache["identity"] == identity, "Reuse requires identical source, inputs and Python"
offsets = [(0.0, 0.0, 0.0)]
for axis in range(3):
    for delta in (-0.002, -0.001, -0.0005, 0.0005, 0.001, 0.002):
        offsets.append(tuple(delta if j == axis else 0.0 for j in range(3)))
offsets += list(itertools.product((-0.001, 0.001), repeat=3))
assert len(offsets) == len(set(offsets)) == 27


def write(path, value):
    payload = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(payload)  # LF bytes on every platform.


def limits():
    assert shutil.disk_usage(OUT).free >= 2 * 1024**3, "Disk reserve exhausted"
    assert sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file()) < 128 * 1024**2
    remaining = 600 - (time.monotonic() - START)
    if remaining <= 0:
        raise TimeoutError("600-second study limit; preserve partial results")
    return remaining


write(OUT / "protocol.json", {
    "identity": identity, "coordinate_names": NAMES, "offsets_m": offsets,
    "selection": "Nonbaseline: both 512-node errors strictly lower; minimize normal, "
                 "interior, then offset tuple. If none qualify, use the same ranking "
                 "over all nonbaseline trials and label trade-off/negative.",
    "limits": {"wall_seconds": 600, "output_MiB": 128, "disk_reserve_GiB": 2,
               "jobs": 1, "threads": 1, "memory_GiB": 2},
    "physical_admission": False, "step4_pass": False,
})
flat = [v for coil in baseline["base_coefficients"] for axis in coil for v in axis]
origins = [flat[baseline["parameter_names"].index(name)] for name in NAMES]
for i, delta in enumerate(offsets):
    candidate = baseline
    for name, origin, change in zip(NAMES, origins, delta, strict=True):
        if change:
            candidate = set_coefficient(candidate, name, origin + change)
    write(OUT / f"trial-{i:02d}-candidate.json", candidate)

# The single child only calls the trusted public functions; no shell or native imports.
WORKER = """
import sys
sys.path.insert(0, "src")
from fusion_public.data import load, load_case, save_new
from fusion_public.dense import dense_boundary
from fusion_public.interior import normalized_interior
from fusion_public.report import audit, evaluate
op, source, output = sys.argv[1:]
case, digest = load_case()
value = load(source)
if op == "report":
    result = evaluate(value, case, digest)
elif op == "audit":
    result = audit(value)
elif op == "interior":
    result = normalized_interior(value, case)
else:
    assert op in ("dense-256", "dense-512")
    result = dense_boundary(value, case, int(op.split("-")[1]))
save_new(output, result)
"""
operations = {}


def run(label, operation, source):
    remaining = limits()
    started = time.monotonic()
    output = OUT / f"{label}.json"
    binding = {"operation": operation, "input_sha256": sha(canonical(load(source)))}
    meta = dict(binding, exit_code=None, reused=False)
    try:
        if label in cache["operations"]:
            old = cache["operations"][label]
            assert all(old[k] == v for k, v in binding.items())
            assert old["exit_code"] == 0
            raw = Path(old["path"]).read_bytes()
            assert sha(raw) == old["sha256"], "Cached output changed"
            with output.open("xb") as stream:
                stream.write(raw)
            meta.update(reused=True, origin=old["path"], original_seconds=old["seconds"])
            meta["exit_code"] = 0
        else:
            command = [sys.executable, "-I", "-S", "-B", "-c", WORKER,
                       operation, str(source), str(output)]
            with (OUT / f"{label}.stdout").open("xb") as stdout:
                with (OUT / f"{label}.stderr").open("xb") as stderr:
                    result = subprocess.run(command, stdout=stdout, stderr=stderr,
                                            timeout=remaining, check=False)
            meta["exit_code"] = result.returncode
            if result.returncode:
                raise RuntimeError(f"{label} failed; see retained stderr")
        limits()
        meta.update(path=str(output), sha256=sha(output.read_bytes()))
        value = load(output)
    except BaseException as error:
        meta["error"] = type(error).__name__ + ": " + str(error)
        if isinstance(error, subprocess.TimeoutExpired):
            meta["exit_code"] = 124
        raise
    finally:
        meta["seconds"] = time.monotonic() - started
        write(OUT / f"{label}-operation.json", meta)
    operations[label] = meta
    print(label, "reused" if meta["reused"] else "computed", flush=True)
    return value


trials = []
try:
    for i, delta in enumerate(offsets):
        report = run(f"trial-{i:02d}-report", "report", OUT / f"trial-{i:02d}-candidate.json")
        assert report["case_sha256"] == case_sha
        assert report["scope"]["physical_admission"] is report["scope"]["step4_pass"] is False
        scores = tuple(report["levels"][1]["metrics"][m] for m in METRICS)
        trials.append({"index": i, "offsets_m": delta, "scores_512": scores,
                       "candidate_sha256": report["candidate_sha256"]})
    eligible = [t for t in trials[1:]
                if all(a < b for a, b in zip(t["scores_512"], trials[0]["scores_512"],
                                            strict=True))]
    chosen = min(eligible or trials[1:], key=lambda t: (*t["scores_512"], t["offsets_m"]))
    selected = OUT / "selected-candidate.json"
    write(selected, load(OUT / f"trial-{chosen['index']:02d}-candidate.json"))
    write(OUT / "selection.json", {
        "selected": chosen, "joint_improvement": bool(eligible), "eligible_count": len(eligible),
        "candidate_file_sha256": sha(selected.read_bytes()), "trials": trials,
        "frozen_before_new_dense_results": True,
    })
    replay = run("selected-audit", "audit", OUT / f"trial-{chosen['index']:02d}-report.json")
    assert replay["report_replay_pass"] is True
    for label, source in (("baseline", OUT / "trial-00-candidate.json"), ("selected", selected)):
        for op in ("dense-256", "dense-512", "interior"):
            run(f"{label}-{op}", op, source)
    limits()
    write(OUT / "complete.json", {"seconds": time.monotonic() - START,
                                  "physical_admission": False, "step4_pass": False})
except BaseException as error:
    write(OUT / "incomplete.json", {"error": type(error).__name__ + ": " + str(error),
                                    "seconds": time.monotonic() - START, "trials": trials})
    raise
finally:
    write(OUT / "reuse.json", {"identity": identity, "operations": operations})
```

## Scope and attribution

The evaluator, case, reference input, target B²/flux, signed current ratios and
all gates are unchanged. Sparse fixed-current scores, sparse flux-normalized
interior error and dense boundary error are distinct diagnostics. There is no
dense interior, continuous-geometry, magnetic-surface, confinement or physical
benefit claim. `physical_admission:false` and `step4_pass:false` remain unchanged.

The project supplied the headroom geometry (expanded-box trial1459, native
producer `5a3c1d0`). The range responds to [PR #5 review 5400194847](https://github.com/DrWorkhard/nuclear-fusion-at-home/pull/5#pullrequestreview-5400194847);
the dense comparison addresses the ranking risk in [issue #8](https://github.com/DrWorkhard/nuclear-fusion-at-home/issues/8),
without resolving its broader sampling work. Underlying plasma data: Alan Goodman,
*Data for paper “Constructing precisely quasi-isodynamic magnetic fields”*, v1.0,
[doi:10.5281/zenodo.7220257](https://doi.org/10.5281/zenodo.7220257), CC BY 4.0;
see the [full provenance](../../examples/clear-coil-samples-v1/README.md#provenance-and-attribution).
These coefficient changes are a derived exploratory contribution, with no author endorsement.
