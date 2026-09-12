"""One-sided tetrahedron separation witnesses and independent interior witnesses.

No separating axis found means unresolved, never a declaration of overlap.
Floating-point safety padding is not directed interval arithmetic.
"""

from itertools import combinations

import numpy as np

EDGES = np.array(list(combinations(range(4), 2)))
FACES = np.array(list(combinations(range(4), 3)))


def validated(tetrahedron):
    points = np.asarray(tetrahedron, dtype=float)
    if points.shape != (4, 3) or not np.isfinite(points).all():
        raise ValueError("four finite3D tetrahedron vertices required")
    extent = float(np.max(np.ptp(points, axis=0)))
    determinant = np.linalg.det((points[1:] - points[0]).T)
    if extent == 0 or not np.isfinite(determinant) or abs(determinant) <= 1e-14 * extent**3:
        raise ValueError("nondegenerate tetrahedron required")
    return points


def separation_witness(first, second, *, relative_tolerance=1e-10):
    a, b = validated(first), validated(second)
    if not np.isfinite(relative_tolerance) or relative_tolerance < 0:
        raise ValueError("finite nonnegative safety tolerance required")
    origin = a[0].copy()
    a, b = a - origin, b - origin

    def faces(tet):
        triangles = tet[FACES]
        return np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])

    ea, eb = a[EDGES[:, 1]] - a[EDGES[:, 0]], b[EDGES[:, 1]] - b[EDGES[:, 0]]
    cross_edges = np.cross(ea[:, None], eb[None]).reshape(-1, 3)
    axes = np.vstack((np.eye(3), faces(a), faces(b), cross_edges))
    norms = np.linalg.norm(axes, axis=1)
    good = np.isfinite(norms) & (norms > 0)
    axes = axes[good] / norms[good, None]
    projections_a, projections_b = axes @ a.T, axes @ b.T
    gaps = np.maximum(projections_b.min(axis=1) - projections_a.max(axis=1),
                      projections_a.min(axis=1) - projections_b.max(axis=1))
    index = int(np.argmax(gaps))
    scale = max(1, float(np.max(abs(np.vstack((a, b))))))
    # Include both translation/subtraction and projection roundoff in the pad.
    pad = relative_tolerance * scale + 64 * np.finfo(float).eps * max(
        scale, float(np.max(abs(origin))))
    lower = float(gaps[index] - pad)
    return dict(status="separated" if lower > 0 else "unresolved", origin=origin.tolist(),
                axis=axes[index].tolist(), raw_projection_gap=float(gaps[index]),
                safety_pad=pad, separation_lower=lower, axes_tested=len(axes),
                directed_interval_certificate=False)


def interior_witness(first, second, *, barycentric_margin=1e-10):
    """Maximize the minimum barycentric weight, then separately solve for weights."""
    from scipy.optimize import linprog

    a, b = validated(first), validated(second)
    if not np.isfinite(barycentric_margin) or barycentric_margin <= 0:
        raise ValueError("positive finite interior margin required")
    origin = a[0].copy()
    a, b = a - origin, b - origin
    gradients, offsets = [], []
    for tet in (a, b):
        inverse = np.linalg.inv((tet[1:] - tet[0]).T)
        derivatives = np.vstack((-inverse.sum(axis=0), inverse))
        constant = np.r_[1.0, np.zeros(3)] - derivatives @ tet[0]
        gradients.append(derivatives)
        offsets.append(constant)
    result = linprog([0, 0, 0, -1], A_ub=np.column_stack((-np.vstack(gradients), np.ones(8))),
                     b_ub=np.concatenate(offsets), bounds=[(None, None)] * 4, method="highs",
                     options=dict(primal_feasibility_tolerance=1e-9,
                                  dual_feasibility_tolerance=1e-9))
    report = dict(status="unresolved", solver_status=int(result.status),
                  solver_success=bool(result.success), solver_message=str(result.message),
                  origin=origin.tolist(), barycentric_margin=barycentric_margin)
    if result.success and result.x is not None and np.isfinite(result.x).all():
        point, margin = result.x[:3], float(result.x[3])
        # Deliberately do not reuse the inverse affine maps used to formulate the LP.
        weights = np.array([np.linalg.solve(np.vstack((tet.T, np.ones(4))), np.r_[point, 1])
                            for tet in (a, b)])
        residual = max(float(np.max(abs(weights[i] @ tet - point)))
                       for i, tet in enumerate((a, b)))
        scale = max(1, float(np.max(abs(np.vstack((a, b))))))
        verified = (np.isfinite(weights).all() and weights.min() > barycentric_margin
                    and np.max(abs(weights.sum(axis=1) - 1)) <= 1e-12
                    and residual <= 1e-12 * scale)
        report.update(status="positive_interior_witness" if verified else "unresolved",
                      point_relative_to_origin=point.tolist(), lp_margin=margin,
                      independently_solved_weights=weights.tolist(),
                      reconstruction_residual=residual)
    return report
