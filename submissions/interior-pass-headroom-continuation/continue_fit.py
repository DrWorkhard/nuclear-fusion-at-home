"""Bounded L-BFGS-B continuation from the length-headroom candidate.

Usage: python continue_fit.py WOUT OUTPUT_DIR [KAPPA_RULE] [MAXITER] [SECONDS]
Needs numpy, scipy, netCDF4 and simsopt; run from the repository root, one thread.
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, "src")
from simsopt.objectives import QuadraticPenalty  # noqa: E402

from fusion_baselines.coupled_coils import CoupledCoils  # noqa: E402

wout, out = Path(sys.argv[1]), Path(sys.argv[2])
inp = Path("evidence/plasma-design-v2/reference-input-401.json")
cand = json.load(open("submissions/length-headroom-six-coil/candidate.json"))
m = CoupledCoils(wout, inp, 6, 5, "V", ncoil=512, nphi=64, ntheta=64, ninner=32, offset=0)
m.geometry = (sum(QuadraticPenalty(j, 3.44, "max") for j in m.length_terms)
              + 1000*m.cc + 1000*m.cs + 1e-4*sum(m.curvature_terms))
if cand["parameter_names"] != m.names:
    raise SystemExit("candidate DOF names/order differ from native canonical names")
x0 = np.array(cand["base_coefficients"], dtype=float).reshape(-1)
KEYS = ("J", "normal_rms", "normal_max", "vector_rms", "scale", "lengths", "kappa_max",
        "coil_distance", "surface_distance")


def eligible(mt):
    return (max(mt["lengths"]) <= 3.45 and mt["coil_distance"] >= 0.06
            and mt["surface_distance"] >= 0.08 and max(mt["kappa_max"]) <= KAPPA)


KAPPA = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
MAXITER = int(sys.argv[4]) if len(sys.argv) > 4 else 5000
CAP = float(sys.argv[5]) if len(sys.argv) > 5 else 600
log, best, t0 = [], None, time.time()
errors = 0


def f(x):
    global best, errors
    try:
        J, g, mt = m.evaluate(x)
    except ValueError:
        errors += 1
        return 1e3, np.zeros_like(x)
    row = {k: mt[k] for k in KEYS} | dict(t=round(time.time()-t0, 2),
                                          gmax=float(np.max(abs(g))), eligible=eligible(mt))
    log.append(row)
    if row["eligible"] and (best is None or mt["normal_rms"] < best[0]["normal_rms"]):
        best = (row, x.copy())
    return J, g


def stop(xk):
    if time.time() - t0 > CAP:
        raise StopIteration


start = f(x0)
start_row = log[0]
box = list(zip(x0-0.02, x0+0.02, strict=True))
res = minimize(f, x0, jac=True, method="L-BFGS-B", callback=stop, bounds=box,
               options=dict(ftol=1e-15, gtol=1e-9, maxls=20, maxiter=MAXITER, maxfun=50000))
summary = dict(
    start=start_row, end=log[-1], best_eligible=best[0] if best else None,
    evaluations=len(log), seconds=round(time.time()-t0, 1), message=str(res.message),
    nit=int(res.nit), names_ok=len(x0) == 198, model_errors=errors,
    coefficients_at_box=int(np.sum(np.isclose(abs(res.x-x0), 0.02, atol=1e-9))),
    start_gmax=start_row["gmax"],
    normal_rms_change_pct=(100*(best[0]["normal_rms"]/start_row["normal_rms"]-1)
                           if best else None),
    vector_rms_change_pct=(100*(best[0]["vector_rms"]/start_row["vector_rms"]-1)
                           if best else None))
out.mkdir(parents=True, exist_ok=False)
json.dump(log, open(out/"history.json", "w"))
for label, xv in (("start", x0), ("final", res.x)):
    json.dump(dict(cand, base_coefficients=np.asarray(xv).reshape(6, 3, 11).tolist()),
              open(out/f"{label}-candidate.json", "w"), indent=1)
np.save(out/"final-x.npy", res.x)
summary["final_J_recomputed"] = float(m.evaluate(res.x)[0])
summary["kappa_rule"] = KAPPA
if best:
    snap = dict(cand, base_coefficients=best[1].reshape(6, 3, 11).tolist())
    json.dump(snap, open(out/"best-eligible-candidate.json", "w"), indent=1)
json.dump(summary, open(out/"summary.json", "w"), indent=1)
print(json.dumps(summary, indent=1))
