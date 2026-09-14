"""Local two-domain proposal model, never a substitute for actual physical admission."""

import warnings

import numpy as np
from scipy.optimize import linprog

FD_STEP = 1e-5
BOX = 1e-4
SCALES = (1.0, 0.5, 0.25)


def arrays(measurement):
    return {key: np.array([c[key] for c in measurement["cells"]]) for key in ("mean", "envelope")}


def construction(narrow, wide, base_narrow, base_wide, meta, base_meta):
    a, b = arrays(base_wide), arrays(wide)
    if (
        a["mean"].shape != (35, 2)
        or b["mean"].shape != (35, 2)
        or any(not np.isfinite(v).all() for v in (*a.values(), *b.values()))
        or np.any(a["mean"] <= 0)
        or np.any(b["mean"] <= 0)
    ):
        raise ValueError("complete positive broad action domain required")
    scores = np.array([narrow, wide["score"], base_narrow, base_wide["score"]])
    finite = bool(np.isfinite(scores).all() and np.all(scores >= 0) and np.all(scores[2:] > 0))
    return dict(
        finite=finite,
        narrow=finite and narrow <= 0.995 * base_narrow,
        wide=finite and wide["score"] <= 0.985 * base_wide["score"],
        mean=bool(np.max(abs(b["mean"] / a["mean"] - 1)) <= 0.02),
        envelope=bool(
            np.all(b["envelope"] <= np.maximum(1.1 * a["envelope"], a["envelope"] + 0.002))
        ),
        geometry=bool(
            abs(meta["volume"] / base_meta["volume"] - 1) <= 0.01
            and np.max(abs(np.array(meta["iota"]) - base_meta["iota"])) <= 0.02
        ),
    )


def select(rows):
    eligible = [
        i for i, r in enumerate(rows) if r.get("construction") and all(r["construction"].values())
    ]
    return min(eligible, key=lambda i: (rows[i]["wide_score"], i)) if eligible else None


def proposal(narrow, wide, means, baseline_narrow, baseline_wide, baseline_means):
    narrow, wide, means, baseline_means = [
        np.asarray(v, dtype=float) for v in (narrow, wide, means, baseline_means)
    ]
    if (
        narrow.shape != (8,)
        or wide.shape != (8,)
        or means.shape != (8, 35, 2)
        or baseline_means.shape != (35, 2)
        or min(baseline_narrow, baseline_wide) <= 0
        or not all(np.isfinite(v).all() for v in (narrow, wide, means, baseline_means))
        or np.any(baseline_means <= 0)
    ):
        raise ValueError("all eight central differences and finite positive baseline required")
    gn = (narrow[::2] - narrow[1::2]) / (2 * FD_STEP * baseline_narrow)
    gw = (wide[::2] - wide[1::2]) / (2 * FD_STEP * baseline_wide)
    gm = ((means[::2] - means[1::2]) / (2 * FD_STEP * baseline_means)).reshape(4, 70).T
    matrix = np.zeros((142, 5))
    matrix[:2, :4] = BOX * np.array([gn, gw])
    matrix[:2, 4] = 1
    matrix[2:72, :4] = BOX * gm
    matrix[72:, :4] = -BOX * gm
    rhs = np.r_[0.0, 0.0, np.full(140, 0.01)]
    bounds = [[-1.0, 1.0]] * 4 + [[0.0, None]]
    objective = [0.0, 0.0, 0.0, 0.0, -1.0]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = linprog(
            objective, A_ub=matrix, b_ub=rhs, bounds=bounds, method="highs", options={"threads": 1}
        )
    record = dict(
        narrow_gradient=gn.tolist(),
        wide_gradient=gw.tolist(),
        mean_gradient=gm.tolist(),
        matrix=matrix.tolist(),
        rhs=rhs.tolist(),
        bounds=bounds,
        objective=objective,
        status=int(result.status),
        success=bool(result.success),
        message=result.message,
        warnings=[str(w.message) for w in caught],
    )
    if result.success:
        record.update(
            solution=result.x.tolist(),
            fun=float(result.fun),
            inequality_marginals=result.ineqlin.marginals.tolist(),
            lower_marginals=result.lower.marginals.tolist(),
            upper_marginals=result.upper.marginals.tolist(),
            proposed_x=(BOX * result.x[:4]).tolist(),
        )
    return record


def dual_certificate(model):
    a, b, c, x, y, lo, hi = [
        np.asarray(model[k], dtype=float)
        for k in (
            "matrix",
            "rhs",
            "objective",
            "solution",
            "inequality_marginals",
            "lower_marginals",
            "upper_marginals",
        )
    ]
    if (
        a.shape != (142, 5)
        or b.shape != (142,)
        or c.shape != (5,)
        or x.shape != (5,)
        or y.shape != (142,)
        or lo.shape != (5,)
        or hi.shape != (5,)
        or not all(np.isfinite(v).all() for v in (a, b, c, x, y, lo, hi))
    ):
        raise ValueError("complete finite primal/dual LP data")
    lower = np.array([-1.0] * 4 + [0.0])
    residual = b - a @ x
    errors = dict(
        primal=max(0.0, float(-residual.min()), float(np.max(lower - x)), float(np.max(x[:4] - 1))),
        dual_sign=max(0.0, float(y.max()), float(-lo.min()), float(hi.max()), abs(float(hi[-1]))),
        stationarity=float(np.max(abs(c - a.T @ y - lo - hi))),
        objective=abs(float(c @ x) - model["fun"]),
        duality_gap=abs(float(c @ x - b @ y - lower @ lo - hi[:4].sum())),
        complementary=max(
            float(np.max(abs(y * residual))),
            float(np.max(abs(lo * (x - lower)))),
            float(np.max(abs(hi[:4] * (1 - x[:4])))),
        ),
    )
    return dict(errors=errors, passed=bool(max(errors.values()) <= 1e-8))
