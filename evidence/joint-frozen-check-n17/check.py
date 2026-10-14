"""N17: frozen ns101/201 derivative check of joint-protocol.json (#59 head 9d7c1b8, #63).

Usage (repository root, one thread): python check.py OUTDIR
"""

import copy
import json
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import vmecpp

sys.path.insert(0, "src")
from fusion_baselines import coil_bounce as bounce  # noqa: E402
from fusion_baselines.vmec_trace import trace_geometry  # noqa: E402

MODES = (("rbc", 1, 1), ("rbc", 2, 0), ("zbs", 1, 1), ("zbs", 2, 0))
BASES = {"ref": "evidence/plasma-design-v2/reference-input-401.json",
         "sel": "evidence/plasma-balanced-v1/selected-input-401.json"}
NS = {101: ([12, 25, 51, 101], [1e-8, 1e-10, 1e-11, 1e-11]),
      201: ([12, 25, 51, 101, 201], [1e-8, 1e-10, 1e-11, 1e-11, 1e-11])}
PLAN = [(101, h) for h in (5e-6, 1e-5, 2e-5)] + [(201, 1e-5)]
BUDGET = 3600
out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=False)
work = Path(tempfile.mkdtemp(dir=out))
t0, log = time.monotonic(), []


def boundary(base, shift):
    data = copy.deepcopy(base)
    for (key, m, n), delta in zip(MODES, shift, strict=True):
        hits = [row for row in data[key] if (row["m"], row["n"]) == (m, n)]
        if len(hits) != 1:
            raise ValueError(f"mode {key}({m},{n}) not unique")
        hits[0]["value"] += float(delta)
    return data


def A(data, ns, tag):
    if time.monotonic() - t0 > BUDGET:
        raise TimeoutError("3600 s budget reached")
    path = work/f"{tag}.json"
    path.write_text(json.dumps(data))
    inp = vmecpp.VmecInput.from_file(path)
    inp.ns_array = np.array(NS[ns][0])
    inp.ftol_array = np.array(NS[ns][1])
    inp.niter_array = np.array([10000]*len(NS[ns][0]))
    started = time.monotonic()
    wout = work/f"{tag}.nc"
    vmecpp.run(inp, max_threads=1, verbose=False).wout.save(str(wout))
    solve = time.monotonic() - started
    cells = []
    for s in (0.25, 0.5, 0.75):
        m = bounce.measure(trace_geometry(str(wout), s, 801, 16, 2))
        cells += [c for c in m["cells"] if c["q"] in (0.1, 0.3, 0.5, 0.7, 0.9)]
    if len(cells) != 15:
        raise ValueError("incomplete narrow domain")
    value = float(np.mean([c["score"] for c in cells]))
    log.append(dict(tag=tag, ns=ns, A=value, solve_s=round(solve, 2)))
    wout.unlink()
    path.unlink()
    return value


report = dict(protocol="joint-protocol.json frozen_next_check @ 9d7c1b8", plan=PLAN, ns=NS,
              derivatives={}, checks={}, status="incomplete")
try:
    for name, source in BASES.items():
        base = json.loads(Path(source).read_text())
        for ns, h in PLAN:
            g = []
            for i in range(4):
                step = [h*(i == j) for j in range(4)]
                plus = A(boundary(base, step), ns, f"{name}-ns{ns}-d{i}+{h}")
                minus = A(boundary(base, [-x for x in step]), ns, f"{name}-ns{ns}-d{i}-{h}")
                g.append((plus - minus)/(2*h))
            report["derivatives"][f"{name}|ns{ns}|h{h}"] = g
        g201 = np.array(report["derivatives"][f"{name}|ns201|h1e-05"])
        big = abs(g201) > 0.05*abs(g201).max()
        g101 = np.array(report["derivatives"][f"{name}|ns101|h1e-05"])
        resolution = bool(np.all(np.sign(g101[big]) == np.sign(g201[big]))
                          and np.all(abs(g101[big] - g201[big]) <= 0.2*abs(g201[big])))
        stack = np.array([report["derivatives"][f"{name}|ns101|h{h}"] for h in (5e-6, 1e-5, 2e-5)])
        spread = (stack.max(axis=0) - stack.min(axis=0))/abs(stack).max(axis=0)
        report["checks"][name] = dict(
            big=big.tolist(), resolution_rel=(abs(g101 - g201)/abs(g201)).tolist(),
            resolution_ok=resolution, h_spread=spread.tolist(),
            h_ok=bool(np.all(spread[big] <= 0.10)), passed=resolution and bool(np.all(spread[big] <= 0.10)))
    both = all(c["passed"] for c in report["checks"].values())
    report["status"] = ("pass: search at ns 101, h 1e-5" if both
                        else "fail: J arm not viable at this budget")
except Exception as exc:
    report["status"] = f"incomplete: {type(exc).__name__}: {exc}"
report.update(log=log, seconds=round(time.monotonic() - t0, 1), vmecpp=vmecpp.__version__
              if hasattr(vmecpp, "__version__") else "0.8.0 (pip)")
(out/"result.json").write_text(json.dumps(report, indent=1))
print(json.dumps({k: v for k, v in report.items() if k != "log"}, indent=1))
