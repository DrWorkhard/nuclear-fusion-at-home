"""Exploratory boundary-metric crosswalk; not an acceptance-profile replacement."""

from numbers import Real

import numpy as np


def _vectors(values):
    if not isinstance(values, np.ndarray):
        objects = np.asarray(values, dtype=object)
        if any(not isinstance(v, Real) or isinstance(v, (bool, np.bool_)) for v in objects.flat):
            raise ValueError("real numeric vectors required; booleans are not coordinates")
    array = np.asarray(values)
    if array.dtype.kind not in "iuf" or np.ma.isMaskedArray(values):
        raise ValueError("real numeric vectors required")
    array = np.asarray(array, dtype=float)
    if array.ndim < 2 or array.shape[-1] != 3 or not array.size:
        raise ValueError("nonempty (..., 3) vector arrays required")
    if not np.isfinite(array).all():
        raise ValueError("finite field and normal vectors required")
    return array


def boundary_metrics(B, normals):
    """Compute unclipped metrics on a uniform parameter grid.

    Normals are surface-Jacobian vectors, not unit normals. Raw flux and local
    flux use parameter means, without an extra parameter-domain extent factor.
    Current/normal signs are allowed; zero field or zero Jacobian is not.
    """
    B, normals = _vectors(B), _vectors(normals)
    if B.shape != normals.shape:
        raise ValueError("matched field and normal shapes required")
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        area, magnitude = np.linalg.norm(normals, axis=-1), np.linalg.norm(B, axis=-1)
        total_area = area.sum()
        if (not np.isfinite(area).all() or not np.isfinite(magnitude).all()
                or not np.isfinite(total_area) or np.any(area <= 0)
                or np.any(magnitude <= 0)):
            raise ValueError("finite positive field magnitudes and area Jacobians required")
        bn = np.sum(B * (normals / area[..., None]), axis=-1)
        weights, ratio = area / total_area, np.abs(bn) / magnitude
        bn2 = bn**2
        result = dict(
            raw_quadratic_flux=0.5 * np.mean(area * bn2),
            parameter_abs_bn_over_mean_b=np.mean(np.abs(bn)) / np.mean(magnitude),
            area_mean_abs_ratio=np.sum(weights * ratio),
            normal_rms=np.sqrt(np.sum(weights * ratio**2)),
            normal_max=np.max(ratio),
            mean_area_jacobian=np.mean(area),
            area_mean_b=np.sum(weights * magnitude),
            parameter_mean_b=np.mean(magnitude),
            min_b=np.min(magnitude),
            area_bn_rms=np.sqrt(np.sum(weights * bn2)),
            normalized_global_flux=0.5 * np.sum(weights * bn2)
            / np.sum(weights * magnitude**2),
            local_flux=0.5 * np.mean(area * ratio**2),
        )
    if not all(np.isfinite(v) for v in result.values()):
        raise ValueError("nonfinite derived boundary metric")
    return {key: float(value) for key, value in result.items()}
