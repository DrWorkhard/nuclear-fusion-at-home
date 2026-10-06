# Headroom continuation with a passing interior component

An exploratory six-coil geometry from 327 more L-BFGS-B iterations, started at the
[length-headroom candidate](../length-headroom-six-coil/README.md). It trades a 2.6%
higher boundary error for a 5.8× lower interior error, with scoped geometry intact.
**Both boundary limits still fail. This is not an accepted design.**

## Original results (all checks on public inputs; evaluator revision `dc75fb3`)

| Check | Headroom start | This geometry | Limit |
| --- | ---: | ---: | ---: |
| Dense boundary normal RMS (64×64, one period) | 0.0019963 | 0.0020485 | 1e-4, fails |
| Dense boundary maximum normal error | 0.009426 | 0.009412 | 1e-3, fails |
| Interior vector RMS (ninner 64, 12,288 points) | 0.011479 | **0.0019880** | 0.01, **passes** |
| Coil–coil clearance lower bound | 0.06832 m | 0.06800 m | ≥0.06 m |
| Coil–plasma clearance lower bound | 0.13308 m | 0.13441 m | ≥0.08 m |
| Maximum sampled length / curvature | 3.4400 m / 10.04 | 3.4400 m / 10.02 | 3.5 m / 12 |
| Flux-normalized current | 308,140.6 A | 305,178.2 A | — |
| Public `sampled_normal_rms` (fixed current) | 0.0017440 | 0.0017899 | — |
| Public `sampled_inner_vector_rms` (fixed current) | 0.0361032 | 0.0341080 | — |

Public evaluation and replay (Python 3.14.8, macOS) give `report_replay_pass: true` and
`physical_admission: false`. The public sampled scores move in opposite directions:
- normal +2.6%, the same trade as the dense boundary;
- interior only −5.5%, because the public case freezes the current (see #9).

## How the dense and interior numbers were obtained

- **Boundary and current:** the original values used the `public dense-boundary` diagnostic then proposed in #7 (now merged; portable recheck below).
- **Interior target:** regenerated from the committed `evidence/plasma-design-v2/reference-input-401.json` with vmecpp 0.8.0, then loaded with the unchanged `fusion_baselines.coupled_coils.load_target`. The regenerated target matches the starter's 64 shipped samples to 3.4e-10. It reproduces the headroom candidate's native interior RMS 0.01147939 exactly (see #10).
- **Geometry:** from the unchanged `clear_coil_geometry_audit.distance_certificate`, with ncoil 1024 and a 512×512 full-torus surface. Run on the start point, it reproduces the recorded headroom bounds: coil exact, plasma to 9e-16.

## Portable recheck (5 October 2026)

The boundary table reproduces with the merged diagnostics, addressing the portable
part of [PR #12's review](https://github.com/DrWorkhard/nuclear-fusion-at-home/pull/12#pullrequestreview-5404918517).
Source: clean `e88421254c172a3060ef1040440805ac29a154e7`, CPython 3.12.3,
Ubuntu 24.04.5 LTS / Linux x86_64 (glibc 2.39). This used an existing checkout,
then a copy of its tracked files with this README update, **not a fresh network
clone**. The unchanged candidates were evaluated sequentially with the standard
library only; the recipe below also replays each saved 256/512-node report.

| Sparse diagnostic (64 points; 512 field-coil nodes) | Headroom control | Continuation |
| --- | ---: | ---: |
| Fixed-current sampled normal RMS | 0.00174403225046 | 0.00178991876372 |
| Fixed-current sampled interior RMS | 0.0361031885135 | 0.0341079799029 |
| Flux-normalized sampled interior RMS | 0.0107844754376 | 0.00185551068923 |

The fixed signed currents remain ±294,966.466322217 A. The separate normalized
interior diagnostic uses **256 coil nodes for flux and 512 for B**. Both it and
every dense check below keep the flux loop at **256 points**, targeting
`abs(phiedge) = 0.03141592653589793` Wb and preserving signed current ratios.

| Geometry | Coil nodes | Dense RMS (64×64 boundary) | Dense maximum | Flux-normalized max abs current (A) |
| --- | ---: | ---: | ---: | ---: |
| Headroom | 256 | 0.00199627036175 | 0.00942577501024 | 308140.584431910 |
| Headroom | 512 | 0.00199627036175 | 0.00942577501023 | 308140.584431910 |
| Continuation | 256 | 0.00204853393765 | 0.00941179326804 | 305178.242771584 |
| Continuation | 512 | 0.00204853393765 | 0.00941179326804 | 305178.242771584 |

For headroom / continuation respectively, dense 512-minus-256 differences are
RMS −5.64e-18 / −3.04e-18, maximum −1.51e-16 / −3.99e-17, and current
0 / −5.82e-11 A. Both fixed-current sampled RMS changes are below 4.49e-17;
all reported B/A relative quadrature differences are below 1.57e-15.
Continuation's dense RMS/max round to the published **0.0020485 / 0.009412**
(unrounded minus published: +3.394e-8 / −2.067e-7). Its dense RMS is 2.618%
higher than headroom while sparse normalized interior RMS is 5.812× lower.

Both same-code audits pass; the headroom report also matches the retained earlier
portable report byte-for-byte. The **0.00185551 sparse interior result does not
reproduce the reported 0.0019880 native 12,288-point result**. Native interior,
continuous geometry and the archived optimizer were not run. Boundary limits
still fail; `physical_admission:false` and `step4_pass:false` remain unchanged.
This is portability evidence using the same mathematical implementation, with
no magnetic-surface, benefit-transfer or physical-acceptance claim.

<details>
<summary>Byte identities and complete standard-library recipe</summary>

SHA-256 of the unchanged inputs and diagnostic sources (candidate hashes here
are file-byte hashes, distinct from the reports' canonical-JSON hashes):

```text
submissions/length-headroom-six-coil/candidate.json
  249d6668bdfa9d91d4164d7008adf4da17f1663e3e2a98c76b083a051db13c10
submissions/interior-pass-headroom-continuation/candidate.json
  521ed4e7ac5b3c0a343545287d05bd1872ed87634939b68ba2e84f9be235dfb4
examples/clear-coil-samples-v1/case.json
  6e5c51e54444f620450ab3df9e5d3969afbafd1e259d7b65c5fc9b49d1c0fadd
examples/clear-coil-samples-v1/manifest.json
  9e949f1247574e3f33e8a45d7a6c639fbb67018560ab3fcc58cf2f2dd2fba23c
evidence/plasma-design-v2/reference-input-401.json
  57394ef682f3c6399faa03012abc02da2eb1ce40703a4f99640ece3d07e5691f
src/fusion_public/dense.py
  68f40f1b652496c2c1fb5edb2c416d3af0496ae84ad1cd49938a854d487182b2
src/fusion_public/interior.py
  a6875fdd99bbf3970a07332319fa06f926160496cb25b8ec2109b735372c781b
```

From the repository root, Python 3.11+, no packages or archived artifacts. Save
the following block as `results/recheck-continuation.py` (create `results/` if
needed), then run `python3 -I -S -B results/recheck-continuation.py`. It uses the
existing public functions behind `evaluate`, `audit`, `dense-boundary` and
`normalized-interior`; the function call additionally exposes 512 dense coil
nodes, which the CLI does not select. Use a fresh output name on reruns.

```python
import hashlib
import platform
import sys
import time
from pathlib import Path

sys.path.insert(0, "src")
from fusion_public.data import load, load_case, save_new
from fusion_public.dense import dense_boundary
from fusion_public.interior import normalized_interior
from fusion_public.report import audit, evaluate

out = Path("results/continuation-portable-recheck")  # Choose a fresh name each time.
out.mkdir(parents=True, exist_ok=False)
inputs = {
    "headroom": Path("submissions/length-headroom-six-coil/candidate.json"),
    "continuation": Path("submissions/interior-pass-headroom-continuation/candidate.json"),
}
paths = sorted(Path("src/fusion_public").glob("*.py")) + list(inputs.values()) + [
    Path("fusion.py"), Path("examples/clear-coil-samples-v1/case.json"),
    Path("examples/clear-coil-samples-v1/manifest.json"),
    Path("examples/clear-coil-samples-v1/candidate.json"),
    Path("evidence/plasma-design-v2/reference-input-401.json"),
]
save_new(out / "inputs.json", {
    "python": sys.version, "platform": platform.platform(),
    "sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
})


def record(name, function, *args):
    start = time.monotonic()
    try:
        result = function(*args)
    except Exception as error:
        save_new(out / f"{name}-failure.json", {
            "error": str(error), "seconds": time.monotonic() - start,
        })
        raise
    save_new(out / f"{name}.json", result)
    save_new(out / f"{name}-time.json", {"seconds": time.monotonic() - start})
    print(name, "saved", flush=True)
    return result


case, digest = load_case()
for name, path in inputs.items():
    candidate = load(path)
    report = record(name + "-report", evaluate, candidate, case, digest)
    record(name + "-audit", audit, load(out / f"{name}-report.json"))
    for nodes in (256, 512):
        record(f"{name}-dense-{nodes}", dense_boundary, candidate, case, nodes)
    record(name + "-interior", normalized_interior, candidate, case)
print("Reports, audits, diagnostics, input hashes and timings:", out)
```

The reports retain both sampled errors at both coil resolutions and their B/A
quadrature differences. `inputs.json` records Python/OS and byte hashes of all
public source files and inputs, including the two diagnostic modules omitted
from the bound evaluator's four-file identity. Timings and any failures stay
beside the raw reports. This run's full logs and source manifest are retained
locally under ignored `results/`; they are not distributed in this submission.
The recipe needs only committed inputs and creates fresh evidence.

</details>

## Reproduce the historical construction

The candidate remains usable by the current public evaluator. Its completed
construction driver and dependencies are preserved at commit **`bf51e3a`**; run
the commands below in a separate checkout of that revision. See
[historical reproduction](../../docs/validation/REPRODUCING_RESULTS.md).

Python 3.12 with `numpy scipy netCDF4 simsopt==1.11.1 vmecpp==0.8.0`, and one thread
(`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`):

```bash
python -c "import vmecpp; r = vmecpp.run(vmecpp.VmecInput.from_file('evidence/plasma-design-v2/reference-input-401.json'), max_threads=1); r.wout.save('results/wout_reference_regen.nc')"
python submissions/interior-pass-headroom-continuation/continue_fit.py results/wout_reference_regen.nc results/continuation 12 327 100000
```

The VMEC solve takes about 6 minutes and the 327 iterations about 10 minutes.

Construction details:
- `CoupledCoils` method "V" (boundary objective plus a 0.05-weighted interior term), with the headroom study's 3.44 m length penalty;
- ncoil 512, 64×64 boundary, ninner 32;
- a ±0.02 m box around the start, which no coefficient reached.

On the producing machine, a repeat run reproduced the final objective bit for bit (J = 1.6502969092034605e-6). Other platforms or library versions may differ at rounding level; compare the table, not hashes.

## Limits

- **Not the native search's model.** The construction is a simplified stand-in for the headroom study's model, whose seed chain depends on unpublished artifacts. The selection here was not preregistered for this trade. The run's own preregistered rule (lowest boundary RMS) would have kept the start.
- **Not converged.** The run stopped at its iteration cap while still descending (max gradient 1.3e-5).
- **Sampled geometry only.** Length and curvature are sampled maxima, not continuous upper bounds. No interval proof or finite-build model.
- **Scope.** One start, one machine. No realized magnetic surfaces, QI quality, Step 3 benefit transfer or engineering assessment.

## Attribution

The continuation candidate was contributed by [pjckoch in PR #12](https://github.com/DrWorkhard/nuclear-fusion-at-home/pull/12);
the portable recheck changes no candidate coefficients or original native claims.
Candidate data follow the starter's CC BY 4.0 attribution. Credit Goodman et al.'s
plasma data as in the [data provenance](../../examples/clear-coil-samples-v1/README.md#provenance-and-attribution).
Equilibrium regeneration used vmecpp (Proxima Fusion, MIT); coil construction used SIMSOPT.
No endorsement or affiliation is implied. Prepared by an AI agent; this is not external review.
