"""Independent projection and barycentric witness verification, not a collision search."""

import numpy as np


def geometry(first, second):
    a, b = np.asarray(first, dtype=float), np.asarray(second, dtype=float)
    if a.shape != (4, 3) or b.shape != (4, 3) or not np.isfinite([a, b]).all():
        raise ValueError("finite original tetrahedral vertices required")
    origin = a[0].copy()
    return a-origin, b-origin, origin


def audit_separation(first, second, witness):
    a, b, origin = geometry(first, second)
    axis = np.asarray(witness["axis"])
    if (axis.shape != (3,) or not np.isfinite(axis).all()
            or abs(float(np.dot(axis, axis))-1) > 2e-12
            or not np.array_equal(witness["origin"], origin)):
        raise ValueError("normalized finite axis and fixed original origin required")
    def project(tet):
        return np.array([float(p[0]*axis[0]+p[1]*axis[1]+p[2]*axis[2]) for p in tet])
    pa, pb = project(a), project(b)
    gap = float(max(pb.min()-pa.max(), pa.min()-pb.max()))
    scale = max(1, float(abs(a).max()), float(abs(b).max()))
    pad = 1e-10*scale + 64*np.finfo(float).eps*max(scale, float(abs(origin).max()))
    claimed = np.array([witness[k] for k in (
        "raw_projection_gap", "safety_pad", "separation_lower")])
    if not np.isfinite(claimed).all():
        raise ValueError("finite separation arithmetic required")
    arithmetic = (witness["safety_pad"] == pad
                  and abs(gap-witness["raw_projection_gap"]) <= 1e-12*scale
                  and witness["separation_lower"] == witness["raw_projection_gap"]-pad
                  and witness["directed_interval_certificate"] is False)
    if witness["status"] == "separated":
        valid = arithmetic and gap > pad and witness["separation_lower"] > 0
    elif witness["status"] == "unresolved":
        valid = arithmetic and witness["separation_lower"] <= 0
    else:
        valid = False
    return dict(valid=bool(valid), independent_gap=gap, required_padding=pad,
                separation_verified=bool(valid and witness["status"] == "separated"))


def audit_interior(first, second, witness):
    a, b, origin = geometry(first, second)
    if (not np.array_equal(witness["origin"], origin)
            or witness["barycentric_margin"] != 1e-10):
        raise ValueError("fixed barycentric margin and original translation required")
    if "independently_solved_weights" not in witness:
        return dict(valid=witness["status"] == "unresolved" and not witness["solver_success"],
                    positive_interior_verified=False)
    weights = np.asarray(witness["independently_solved_weights"])
    point = np.asarray(witness["point_relative_to_origin"])
    if (weights.shape != (2, 4) or point.shape != (3,) or not np.isfinite(weights).all()
            or not np.isfinite(point).all()):
        raise ValueError("finite explicit common-point barycentric arrays required")
    reconstructions = np.array([sum((weights[k, i]*tet[i] for i in range(4)), np.zeros(3))
                                for k, tet in enumerate((a, b))])
    residual = float(abs(reconstructions-point).max())
    scale = max(1, float(abs(a).max()), float(abs(b).max()))
    positive = bool(weights.min() > 1e-10 and abs(weights.sum(axis=1)-1).max() <= 1e-12
                    and residual <= 1e-12*scale)
    valid = (witness["solver_success"] and witness["status"] == (
        "positive_interior_witness" if positive else "unresolved")
        and abs(residual-witness["reconstruction_residual"]) <= 1e-12*scale)
    return dict(valid=bool(valid), positive_interior_verified=positive,
                independent_reconstruction_residual=residual)
