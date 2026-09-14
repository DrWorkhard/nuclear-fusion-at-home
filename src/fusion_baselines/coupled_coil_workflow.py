"""Registered pilot bookkeeping, separate from coil physics and native ordering."""

import numpy as np


def cases():
    return [
        dict(label=f"{target}-n{nbase}-{method}", target=target,
             nbase=nbase, order=order, method=method)
        for target in ("reference", "selected")
        for nbase, order in ((6, 5), (8, 7))
        for method in ("N", "V")
    ]


def directions(size):
    if size <= 0:
        raise ValueError("positive canonical parameter dimension required")
    k = np.arange(1, size + 1, dtype=float)
    return [v / np.linalg.norm(v) for v in (np.sin(k), np.cos(k))]


def qualification_points(seed):
    seed = np.asarray(seed, dtype=float)
    if seed.ndim != 1 or not np.isfinite(seed).all() or not len(seed):
        raise ValueError("finite canonical seed required")
    return [seed.copy()] + [
        seed + sign * step * direction
        for direction in directions(len(seed))
        for step in (1e-5, 5e-6)
        for sign in (1, -1)
    ] + [seed.copy()]


def derivative_checks(rows, seed):
    expected = qualification_points(seed)
    if len(rows) != 10 or any(
        r.get("status") != "completed" or not np.array_equal(r["x"], x)
        for r, x in zip(rows, expected, strict=True)
    ):
        raise ValueError("all ten ordered qualification points required")
    values = np.asarray([r["J"] for r in rows], dtype=float)
    gradients = np.asarray([r["gradient"] for r in rows], dtype=float)
    if (gradients.shape != (10, len(seed)) or not np.isfinite(values).all()
            or not np.isfinite(gradients).all()):
        raise ValueError("finite scalar and full canonical gradients required")
    checks = []
    for k, direction in enumerate(directions(len(seed))):
        analytic = float(gradients[0] @ direction)
        for j, step in enumerate((1e-5, 5e-6)):
            i = 1 + 4 * k + 2 * j
            finite_difference = float((values[i] - values[i + 1]) / (2 * step))
            error = abs(finite_difference - analytic)
            relative = error / max(abs(finite_difference), abs(analytic), 1e-30)
            checks.append(dict(direction=k, step=step, analytic=analytic,
                               finite_difference=finite_difference, absolute_error=error,
                               relative_error=relative, passed=error <= 1e-8 or relative <= 2e-4))
    repeat = bool(values[0] == values[-1] and np.array_equal(gradients[0], gradients[-1]))
    return dict(checks=checks, exact_repeat=repeat,
                all_pass=repeat and all(c["passed"] for c in checks))


def choose_search(rows):
    """Only the actual search ledger is passed; errors are not fabricated values."""
    eligible = []
    for i, row in enumerate(rows):
        if row.get("status") != "completed":
            continue
        if not np.isfinite(row["J"]) or not np.isfinite(row["x"]).all():
            raise ValueError("completed nonfinite candidate forbidden")
        eligible.append(i)
    return min(eligible, key=lambda i: (rows[i]["J"], i)) if eligible else None


def refinement(coarse, fine):
    if not np.isfinite([coarse, fine]).all() or min(coarse, fine) < 0:
        raise ValueError("finite nonnegative refinement metrics required")
    delta = abs(fine - coarse)
    return dict(coarse=coarse, fine=fine, delta=delta,
                passed=delta <= max(0.01 * coarse, 1e-7))
