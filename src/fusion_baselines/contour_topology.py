"""Restricted, sampled two-root contour winding screen on a periodic surface."""

from pathlib import Path

import netCDF4
import numpy as np

from fusion_baselines.vmec_trace import _fourier, _interpolate


def surface_field(wout: Path, surface: float, ntheta: int, nzeta: int):
    """Sample symmetric VMEC |B| on [0,2pi)^2 in theta and zeta=nfp*phi."""
    if ntheta < 4 or nzeta < 4:
        raise ValueError("surface grid requires at least four points per direction")
    with netCDF4.Dataset(wout) as dataset:

        def read(name):
            value = np.ma.asarray(dataset[name][...], dtype=float).filled(np.nan)
            if not np.all(np.isfinite(value)):
                raise ValueError(f"nonfinite VMEC variable: {name}")
            return value

        if read("lasym__logical__").item() != 0:
            raise ValueError("only symmetric wouts are supported")
        ns, nfp = int(read("ns").item()), int(read("nfp").item())
        if ns < 3 or nfp < 1:
            raise ValueError("invalid VMEC grid")
        full = np.linspace(0, 1, ns)
        b = _interpolate((full[:-1] + full[1:]) / 2, read("bmnc")[1:], surface)
        m, n = read("xm_nyq"), read("xn_nyq")
    theta, zeta = np.meshgrid(
        np.arange(ntheta) * (2 * np.pi / ntheta),
        np.arange(nzeta) * (2 * np.pi / nzeta),
        indexing="ij",
    )
    field = _fourier(theta, zeta / nfp, m, n, b)
    if not np.all(np.isfinite(field)) or np.any(field <= 0):
        raise ValueError("nonfinite or nonpositive surface field")
    return field


def _periodic_delta(value):
    return (value + np.pi) % (2 * np.pi) - np.pi


def two_root_winding(field, bounce_field: float):
    """Classify only two simple root graphs; other classes fail closed.

    Axis zero is uniform theta, axis one uniform zeta; no repeated endpoints.
    This is a finite-grid screen and cannot certify absence of subgrid contours.
    """
    field = np.asarray(field, dtype=float)
    if field.ndim != 2 or min(field.shape) < 4:
        raise ValueError("expected a periodic 2D grid with >=4 points per direction")
    if not np.all(np.isfinite(field)) or np.any(field <= 0):
        raise ValueError("field must be finite and positive")
    if not np.isfinite(bounce_field) or bounce_field <= 0:
        raise ValueError("bounce field must be finite and positive")
    q = field - bounce_field
    scale = max(1.0, abs(bounce_field), float(np.max(np.abs(field))))
    margin = float(np.min(np.abs(q))) / scale
    result = {"pass": False, "vertex_margin_normalized": margin}
    if margin <= 1e-12:
        return dict(result, classification="unresolved_vertex_or_tangency")
    crosses = (q > 0) != (np.roll(q, -1, axis=1) > 0)
    counts = np.sum(crosses, axis=1)
    result.update(root_count_min=int(counts.min()), root_count_max=int(counts.max()))
    if np.any(counts != 2):
        return dict(result, classification="unsupported_root_count")
    roots = []
    dzeta = 2 * np.pi / field.shape[1]
    for row, mask in zip(q, crosses, strict=True):
        index = np.flatnonzero(mask)
        next_index = (index + 1) % len(row)
        fraction = -row[index] / (row[next_index] - row[index])
        roots.append(np.sort(((index + fraction) * dzeta) % (2 * np.pi)))
    previous = roots[0]
    accumulated = np.zeros(2)
    maximum_step = 0.0
    for index in range(1, len(roots) + 1):
        current = roots[index % len(roots)]
        direct = _periodic_delta(current - previous)
        swapped = _periodic_delta(current[::-1] - previous)
        costs = np.array([direct @ direct, swapped @ swapped])
        if abs(costs[0] - costs[1]) <= 1e-10:
            return dict(result, classification="ambiguous_branch_assignment")
        swap = costs[1] < costs[0]
        delta = swapped if swap else direct
        maximum_step = max(maximum_step, float(np.max(np.abs(delta))))
        if maximum_step >= np.pi / 4:
            return dict(result, classification="unresolved_large_branch_step")
        if index == len(roots) and swap:
            return dict(result, classification="nonidentity_closure_permutation")
        accumulated += delta
        previous = current[::-1] if swap else current
    winding = accumulated / (2 * np.pi)
    integer = np.rint(winding).astype(int)
    result.update(
        toroidal_period_winding=integer.tolist(),
        winding_roundoff_max=float(np.max(np.abs(winding - integer))),
        maximum_branch_step=maximum_step,
    )
    if result["winding_roundoff_max"] > 1e-8:
        return dict(result, classification="unresolved_noninteger_winding")
    passed = bool(np.all(integer == 0))
    return dict(
        result,
        **{"pass": passed},
        classification="two_poloidal_graphs" if passed else "nonzero_toroidal_winding",
    )
