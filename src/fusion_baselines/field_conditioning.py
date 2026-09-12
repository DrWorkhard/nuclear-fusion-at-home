"""Spectra and current-subspace projections of a fixed linearized field model."""

import numpy as np


def spectrum(matrix):
    matrix = np.asarray(matrix, dtype=float)
    if (
        matrix.ndim != 2
        or matrix.shape[0] < matrix.shape[1]
        or matrix.shape[1] == 0
        or not np.isfinite(matrix).all()
    ):
        raise ValueError("finite nonempty tall field matrix required")
    singular = np.linalg.svd(matrix, compute_uv=False)
    rank = int(np.count_nonzero(singular > 1e-12 * singular[0]))
    condition = float(singular[0] / singular[-1]) if singular[-1] > 0 else None
    if condition is not None and not np.isfinite(condition):
        condition = None
    return dict(
        singular_values=singular,
        rank=rank,
        condition=condition,
        columns=matrix.shape[1],
        rcond=1e-12,
    )


def conditioning(z, matrix, current_columns, steps, *, flux_scale=1e-6):
    z, matrix, columns, steps = (np.asarray(v) for v in (z, matrix, current_columns, steps))
    if (
        matrix.ndim != 2
        or matrix.shape[0] < matrix.shape[1]
        or matrix.shape[1] < 4
        or z.shape != (matrix.shape[0],)
        or columns.shape != (3,)
        or columns.dtype.kind not in "iu"
        or len(set(columns.tolist())) != 3
        or np.any((columns < 0) | (columns >= matrix.shape[1]))
        or steps.shape != (3, matrix.shape[1])
        or not all(np.isfinite(v).all() for v in (z, matrix, steps))
        or not np.isscalar(flux_scale)
        or not np.isfinite(flux_scale)
        or flux_scale <= 0
    ):
        raise ValueError("finite matching field, three current columns and three steps required")
    if np.any(steps[:, columns] != 0):
        raise ValueError("only geometric directions allowed in frozen current-coupling diagnosis")
    geometry = np.array([i for i in range(matrix.shape[1]) if i not in set(columns)], dtype=int)
    a, dg = matrix[:, columns], matrix[:, geometry]
    spectra = dict(
        full=spectrum(matrix / np.sqrt(flux_scale)),
        geometry=spectrum(dg / np.sqrt(flux_scale)),
        current=spectrum(a),
    )
    current = spectra["current"]
    qualified = (
        current["rank"] == 3 and current["condition"] is not None and current["condition"] <= 1e10
    )
    result = dict(
        status="unqualified_current_subspace",
        current_projection_qualified=False,
        geometry_columns=geometry,
        current_columns=columns.copy(),
        spectra=spectra,
        projections=[],
        work=dict(svd_calls=3, qr_calls=0, step_projections=0),
    )
    if not qualified:
        return result
    q, r = np.linalg.qr(a, mode="reduced")
    result["work"]["qr_calls"] += 1
    orthogonality = float(np.max(abs(q.T @ q - np.eye(3))))
    if not np.isfinite(orthogonality):
        raise ValueError("finite current-subspace orthogonality required")
    result.update(Q=q, R=r, orthogonality_error=orthogonality)
    if orthogonality > 1e-12:
        return result
    projected_geometry = dg - q @ (q.T @ dg)
    result["projected_geometry"] = projected_geometry
    spectra["projected_geometry"] = spectrum(projected_geometry / np.sqrt(flux_scale))
    result["work"]["svd_calls"] += 1
    for step in steps:
        tangent = matrix @ step
        energy = float(tangent @ tangent)
        component = q.T @ tangent
        linear = z + tangent
        projected = linear - q @ (q.T @ linear)
        record = dict(
            tangent=tangent,
            current_components=component,
            projected_residual=projected,
            current_tangent_energy_fraction=float(component @ component / energy)
            if energy > 0
            else None,
            projected_linear_residual_norm=float(np.linalg.norm(projected)),
            projected_linear_raw_flux=float(projected @ projected / 2),
        )
        if not all(np.isfinite(value).all() for value in record.values() if value is not None):
            raise ValueError("nonfinite current-subspace projection")
        result["projections"].append(record)
        result["work"]["step_projections"] += 1
    result.update(status="completed", current_projection_qualified=True)
    return result
