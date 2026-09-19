"""Geometry-only, preregistered exterior modular-coil initialization.

Construction uses native surfaces and support-function LPs. No magnetic fields,
currents, equilibrium solves, physical admission, or independent audit here.
"""

import math
import warnings

import numpy as np
from scipy.optimize import linprog

MARGIN = 1e-9
OPTIONS = dict(time_limit=30.0, primal_feasibility_tolerance=1e-10,
               dual_feasibility_tolerance=1e-10, threads=1, parallel=False)


def finite(value):
    if np.asarray(value).dtype.kind not in "iuf":
        raise ValueError("real numeric geometry values required, without coercion")
    result = np.asarray(value, dtype=float)
    if not np.isfinite(result).all():
        raise ValueError("finite geometry values required")
    return result


def integer(value, minimum=1):
    if type(value) is not int or value < minimum:
        raise ValueError("integer geometry dimension required")
    return value


def cases():
    return [dict(label=f"n{nbase}-{method}-d{round(1000*d)}mm", nbase=nbase,
                 order=order, method=method, d=d, K=1 if method == "circle" else order-1,
                 r_floor=float(.06/(2*np.sin(np.pi/(4*nbase)))+.025))
            for nbase, order in ((6, 5), (8, 7))
            for method in ("circle", "shape") for d in (.10, .14, .18)]


def modes(data, key):
    if (type(data.get("nfp")) is not int or data["nfp"] != 2
            or data.get("lasym", False) is not False
            or data.get("rbs") not in (None, []) or data.get("zbc") not in (None, [])):
        raise ValueError("symmetric nfp2 surface required")
    integer(data.get("mpol"), 2)
    integer(data.get("ntor"), 0)
    rows = []
    for row in data[key]:
        m, n = row["m"], row["n"]
        integer(m, 0)
        if type(n) is not int or m >= data["mpol"] or abs(n) > data["ntor"]:
            raise ValueError("explicit in-range Fourier surface modes required")
        value = float(finite(row["value"]))
        rows.append((m, n, value))
    if len({(m, n) for m, n, _ in rows}) != len(rows):
        raise ValueError("duplicate Fourier surface modes")
    return rows


def derivative_bounds(data):
    r, z = modes(data, "rbc"), modes(data, "zbs")
    r0 = sum(abs(v) for _, _, v in r)
    rt = 2*np.pi*sum(abs(m*v) for m, _, v in r)
    rp = 2*np.pi*data["nfp"]*sum(abs(n*v) for _, n, v in r)
    zt = 2*np.pi*sum(abs(m*v) for m, _, v in z)
    zp = 2*np.pi*data["nfp"]*sum(abs(n*v) for _, n, v in z)
    return dict(theta=float(np.hypot(rt, zt)),
                phi=float(np.sqrt(rp**2+(2*np.pi*r0)**2+zp**2)),
                radius_theta=float(rt), radius_phi=float(rp))


def surface(data, nphi=256, ntheta=256, offset=0):
    """Native full-torus geometry and continuous covering bounds; no field calls."""
    from simsopt.geo import SurfaceRZFourier

    integer(nphi, 4)
    integer(ntheta, 4)
    if offset not in (0, .5):
        raise ValueError("registered unshifted or half-shifted surface grid required")
    r, z = modes(data, "rbc"), modes(data, "zbs")
    phi = (np.arange(nphi)+offset)/nphi
    native = SurfaceRZFourier(nfp=2, stellsym=True, mpol=data["mpol"]-1,
                             ntor=data["ntor"], quadpoints_phi=phi,
                             quadpoints_theta=(np.arange(ntheta)+offset)/ntheta)
    native.local_full_x = np.zeros_like(native.local_full_x)
    for rows, setter in ((r, native.set_rc), (z, native.set_zs)):
        for m, n, value in rows:
            if value != 0:
                setter(m, n, value)
    native.local_full_x = native.get_dofs()
    native.fix_all()
    points = finite(native.gamma()).copy()
    bounds = derivative_bounds(data)
    pad = float(128*np.finfo(float).eps*max(1.0, float(abs(points).max())))
    cover = bounds["phi"]/(2*nphi)+bounds["theta"]/(2*ntheta)+pad
    signed_radius = (points[..., 0]*np.cos(2*np.pi*phi[:, None])
                     + points[..., 1]*np.sin(2*np.pi*phi[:, None]))
    radius_lower = (float(signed_radius.min())-bounds["radius_phi"]/(2*nphi)
                    - bounds["radius_theta"]/(2*ntheta)-pad)
    if radius_lower <= 0:
        raise ValueError("continuous positive plasma cylindrical radius not certified")
    return dict(points=points, bounds=bounds, cover=float(cover), pad=pad,
                radius_lower=float(radius_lower), nphi=nphi, ntheta=ntheta,
                offset=offset, full_torus=True)


def origin(inputs, phi):
    """Mean of both analytic m=0 section centers, without geometric target fitting."""
    phi = float(finite(phi))
    if not isinstance(inputs, (tuple, list)) or not inputs:
        raise ValueError("nonempty ordered surface input list required")
    return np.mean([[sum(v*np.cos(-n*data["nfp"]*phi)
                        for m, n, v in modes(data, "rbc") if m == 0),
                     sum(v*np.sin(-n*data["nfp"]*phi)
                         for m, n, v in modes(data, "zbs") if m == 0)]
                    for data in inputs], axis=0)


def envelope(surface_rows, phi, d, r_floor, center):
    """Exact plane intersections of conservative covering spheres, in fixed order."""
    phi, d, r_floor = map(float, finite([phi, d, r_floor]))
    center = finite(center)
    if d <= 0 or r_floor <= 0 or center.shape != (2,) or not surface_rows:
        raise ValueError("positive distances, two-dimensional center and surfaces required")
    er = np.array([np.cos(phi), np.sin(phi), 0.0])
    ep = np.array([-np.sin(phi), np.cos(phi), 0.0])
    centers, radii, targets, indices, expansions, pads = [], [], [], [], [], []
    for target, row in enumerate(surface_rows):
        points = finite(row["points"]).reshape(-1, 3)
        cover = float(finite(row["cover"]))
        radius_lower = finite(row["radius_lower"])
        if (radius_lower.shape != () or cover <= 0 or row.get("full_torus") is not True
                or radius_lower <= 0):
            raise ValueError("qualified continuous full-torus surface coverage required")
        expanded = d+cover
        eta = float(1e-12*max(1.0, np.linalg.norm(points, axis=1).max(),
                            expanded, np.linalg.norm(center)))
        radial, normal = points @ er, points @ ep
        keep = (abs(normal) <= expanded+eta) & (radial+expanded+2*eta >= r_floor)
        ids = np.flatnonzero(keep)
        centers.append(np.column_stack((radial[ids], points[ids, 2]))-center)
        contracted_normal = np.maximum(abs(normal[ids])-eta, 0.0)
        discriminant = ((expanded+eta-contracted_normal)
                        * (expanded+eta+contracted_normal))
        radii.append(np.sqrt(np.maximum(0.0, discriminant))+eta)
        targets.append(np.full(len(ids), target, dtype=int))
        indices.append(ids)
        expansions.append(expanded)
        pads.append(eta)
    if not sum(map(len, radii)):
        raise ValueError("empty retained safety envelope")
    return dict(centers=np.concatenate(centers), radii=np.concatenate(radii),
                target_index=np.concatenate(targets), grid_index=np.concatenate(indices),
                expansions=np.array(expansions), pads=np.array(pads),
                center=center.copy(), phi=phi,
                d=d, r_floor=r_floor)


def support_basis(K, angles):
    integer(K)
    alpha = finite(angles)
    if alpha.ndim != 1 or not len(alpha):
        raise ValueError("one-dimensional normal-angle grid required")
    result = np.ones((len(alpha), 2*K+1))
    for m in range(1, K+1):
        result[:, 2*m-1] = np.sin(m*alpha)
        result[:, 2*m] = np.cos(m*alpha)
    return result


def disk_support(centers, radii, angles):
    centers, radii, angles = map(finite, (centers, radii, angles))
    if (centers.shape != (len(radii), 2) or not len(radii)
            or radii.ndim != 1 or np.any(radii < 0) or angles.ndim != 1):
        raise ValueError("finite matched nonempty disk centers/radii required")
    normals = np.column_stack((np.cos(angles), np.sin(angles)))
    result = np.full(len(angles), -np.inf)
    for first in range(0, len(centers), 1024):
        block = centers[first:first+1024] @ normals.T + radii[first:first+1024, None]
        result = np.maximum(result, block.max(axis=0))
    return result


def problem(disks, K, center_r, r_floor, nangle=1024):
    integer(K)
    integer(nangle, 8)
    if nangle <= 2*K or K > 6:
        raise ValueError("resolved support order at most six required")
    center_r, r_floor = map(float, finite([center_r, r_floor]))
    if r_floor <= 0:
        raise ValueError("positive cylindrical coil radius floor required")
    centers, radii = finite(disks["centers"]), finite(disks["radii"])
    angles = 2*np.pi*np.arange(nangle)/nangle
    basis = support_basis(K, angles)
    weights = np.repeat(np.arange(1, K+1), 2)
    second = np.concatenate(([1.0], 1.0-weights**2))
    delta = np.pi/nangle
    envelope_support = disk_support(centers, radii, angles)
    ls = float(np.linalg.norm(centers, axis=1).max())
    ncoeff, nvars = 2*K+1, 4*K+1
    rows, rhs = [], []
    inclusion = np.zeros((nangle, nvars))
    inclusion[:, :ncoeff] = -basis
    inclusion[:, ncoeff:] = delta*weights
    rows.append(inclusion)
    rhs.append(-envelope_support-delta*ls-MARGIN)
    curvature = np.zeros((nangle, nvars))
    curvature[:, :ncoeff] = -basis*second
    curvature[:, ncoeff:] = delta*weights*abs(1-weights**2)
    rows.append(curvature)
    rhs.append(np.full(nangle, -.10-MARGIN))
    radial = np.zeros((1, nvars))
    radial[0, 0] = 1.0
    radial[0, 2:2*K+1:2] = (-1.0)**np.arange(1, K+1)
    rows.append(radial)
    rhs.append(np.array([center_r-r_floor-MARGIN]))
    absolute = np.zeros((4*K, nvars))
    for k in range(2*K):
        absolute[2*k, 1+k] = 1
        absolute[2*k+1, 1+k] = -1
        absolute[2*k:2*k+2, ncoeff+k] = -1
    rows.append(absolute)
    rhs.append(np.zeros(4*K))
    c = np.zeros(nvars)
    c[0] = 2*np.pi
    return dict(c=c, A=np.vstack(rows), b=np.concatenate(rhs),
                lower=np.concatenate(([0.0], np.full(2*K, -.5), np.zeros(2*K))),
                upper=np.concatenate(([1.5], np.full(4*K, .5))),
                angles=angles, support=envelope_support, support_lipschitz=ls,
                K=K, nangle=nangle, center_r=center_r, r_floor=r_floor)


def solve(model):
    arrays = {k: finite(model[k]) for k in ("c", "A", "b", "lower", "upper")}
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        result = linprog(arrays["c"], A_ub=arrays["A"], b_ub=arrays["b"],
                         bounds=list(zip(arrays["lower"], arrays["upper"], strict=True)),
                         method="highs-ds", options=OPTIONS.copy())
    warning_rows = [dict(category=row.category.__name__, message=str(row.message))
                    for row in recorded]
    # Persist AND re-emit the upstream forwarding notice, never hide warnings.
    for row in recorded:
        warnings.warn_explicit(str(row.message), row.category, row.filename, row.lineno)
    answer = dict(success=bool(result.success), status=int(result.status),
                  message=str(result.message), nit=int(result.nit),
                  objective=float(result.fun) if result.fun is not None else None,
                  method="highs-ds", options=OPTIONS.copy(), warnings=warning_rows)
    for key, value in (("x", result.x), ("slack", result.ineqlin.residual),
                       ("inequality_marginals", result.ineqlin.marginals),
                       ("lower_marginals", result.lower.marginals),
                       ("upper_marginals", result.upper.marginals)):
        answer[key] = None if value is None else finite(value).tolist()
    return answer


def export_coefficients(h, center, phi, order):
    """Analytic complex convolution; no sampling, least-squares fit or truncation.

    R+iZ = c + (h+i h') exp(i alpha), alpha=-2pi*t. Native local array order is
    c0,s1,c1,... on each Cartesian axis, including the native clockwise orientation.
    """
    h, center = finite(h), finite(center)
    integer(order)
    phi = float(finite(phi))
    if h.ndim != 1 or len(h) < 3 or len(h) % 2 != 1 or center.shape != (2,):
        raise ValueError("odd Fourier support array and planar center required")
    K = (len(h)-1)//2
    if K+1 > order:
        raise ValueError("support export cannot truncate Cartesian Fourier harmonics")
    spectrum = {0: complex(h[0])}
    for k in range(1, K+1):
        spectrum[k] = (h[2*k]-1j*h[2*k-1])/2
        spectrum[-k] = spectrum[k].conjugate()
    q = {-(k+1): (1-k)*value for k, value in spectrum.items()}
    q[0] = q.get(0, 0)+complex(*center)
    rz = np.zeros((2, 2*order+1))
    rz[:, 0] = (q.get(0, 0).real, q.get(0, 0).imag)
    for k in range(1, order+1):
        cosine = q.get(k, 0)+q.get(-k, 0)
        sine = 1j*(q.get(k, 0)-q.get(-k, 0))
        rz[:, 2*k] = (cosine.real, cosine.imag)
        rz[:, 2*k-1] = (sine.real, sine.imag)
    return np.stack((math.cos(phi)*rz[0], math.sin(phi)*rz[0], rz[1]))
