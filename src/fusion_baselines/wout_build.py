"""Documented VMEC++ path from a hash-bound input JSON to a 401-surface Wout (#115).

The Step 3 production pipeline is archived. This solves an input with its own explicit
ns/ftol/niter schedule, one thread, and records what is needed to reproduce or compare
the result. A regenerated Wout has its own identity (vmecpp version and SHA-256); it is
never relabelled as an archived one.
"""

import numpy as np

SCHEDULE = ("ns_array", "ftol_array", "niter_array")
SCALARS = ("ier_flag", "ns", "nfp", "mpol", "ntor", "volume_p", "aspect", "Rmajor_p",
           "Aminor_p", "b0", "betatotal", "wb")
PROFILE_ENDS = ("iotaf", "phi", "presf")


def need(condition, message):
    if not condition:
        raise ValueError(message)


def schedule(data):
    """Explicit multigrid schedule that ends at 401 surfaces."""
    need(all(k in data for k in SCHEDULE), "explicit ns_array/ftol_array/niter_array required")
    ns, ftol, niter = (list(data[k]) for k in SCHEDULE)
    need(len(ns) == len(ftol) == len(niter) > 0, "matched schedule lengths required")
    need(all(type(n) is int and n >= 3 for n in ns) and ns == sorted(set(ns)),
         "increasing integer ns schedule required")
    need(ns[-1] == 401, "schedule must end at 401 surfaces")
    need(all(0 < float(f) < 1 for f in ftol) and all(type(i) is int and i > 0 for i in niter),
         "positive tolerances and iteration limits required")
    return dict(ns_array=ns, ftol_array=[float(f) for f in ftol], niter_array=niter)


def read(data, key):
    return np.ma.asarray(data[key][...], dtype=float).filled(np.nan)


def summary(data):
    """Scalars and profile end points of an open Wout (netCDF4 Dataset or dict)."""
    result = {k: read(data, k).item() for k in SCALARS if k in data}
    for key in PROFILE_ENDS:
        if key in data:
            profile = read(data, key)
            result[f"{key}_axis"], result[f"{key}_edge"] = float(profile[0]), float(profile[-1])
    return result


def compare(a, b):
    """Per-variable differences between two Wouts; missing or reshaped variables listed."""
    rows, only_a, only_b = {}, sorted(set(a) - set(b)), sorted(set(b) - set(a))
    for key in sorted(set(a) & set(b)):
        try:
            x, y = read(a, key), read(b, key)
        except (TypeError, ValueError):
            rows[key] = dict(comparable=False, equal=bool(np.array_equal(a[key][...], b[key][...])))
            continue
        if x.shape != y.shape:
            rows[key] = dict(comparable=False, shapes=[list(x.shape), list(y.shape)])
            continue
        both = np.isfinite(x) & np.isfinite(y)
        same_nonfinite = bool(np.array_equal(np.isfinite(x), np.isfinite(y)))
        diff = np.abs(x - y)[both]
        scale = float(np.max(np.abs(x[both]))) if both.any() else 0.0
        top = float(diff.max()) if diff.size else 0.0
        rows[key] = dict(comparable=True, shape=list(x.shape), identical=bool(
            same_nonfinite and np.array_equal(x[both], y[both])),
            same_nonfinite=same_nonfinite, max_abs=top, scale=scale,
            max_rel=top/scale if scale > 0 else (0.0 if top == 0 else None))
    finite = [r["max_rel"] for r in rows.values() if r.get("max_rel") is not None]
    worst = max(rows, key=lambda k: rows[k].get("max_rel") or 0.0) if finite else None
    return dict(variables=rows, only_first=only_a, only_second=only_b,
                identical=all(r.get("identical", r.get("equal", False)) for r in rows.values())
                and not only_a and not only_b,
                worst_variable=worst, worst_max_rel=max(finite) if finite else None)
