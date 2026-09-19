"""Independent geometry/LP certification for exterior planar coil initialization.

Only NumPy/SciPy geometry is used. No producer, native surface, field, current or
equilibrium evaluator is imported. Ordinary floating-point pads are not interval
arithmetic. All returned certificate scalars are native Python JSON values.
"""

import math

import numpy as np
from scipy.spatial import cKDTree


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite(value):
    require(np.asarray(value).dtype.kind in "iuf", "real numerical data without coercion required")
    result = np.asarray(value, dtype=float)
    require(np.isfinite(result).all(), "finite geometry data required")
    return result


def integer(value, minimum=1):
    require(type(value) is int and value >= minimum, "positive integer dimension required")
    return value


def compare(actual, expected, label, exact=False):
    actual, expected = np.asarray(actual), np.asarray(expected)
    require(actual.dtype.kind in "biuf" and expected.dtype.kind in "biuf", f"{label}: real dtype")
    require(actual.shape == expected.shape, f"{label}: shape mismatch")
    require(np.isfinite(actual).all() and np.isfinite(expected).all(), f"{label}: nonfinite")
    require(
        np.array_equal(actual, expected) if exact else np.all(abs(actual - expected) <= 5e-12),
        f"{label}: independent raw reconstruction differs",
    )


def cases():
    result = []
    for n, order in ((6, 5), (8, 7)):
        for method in ("circle", "shape"):
            for d in (0.10, 0.14, 0.18):
                result.append(
                    dict(
                        label=f"n{n}-{method}-d{round(1000 * d)}mm",
                        nbase=n,
                        order=order,
                        method=method,
                        d=d,
                        K=1 if method == "circle" else order - 1,
                        r_floor=float(0.06 / (2 * np.sin(np.pi / (4 * n))) + 0.025),
                    )
                )
    return result


def modes(data, key):
    require(
        data.get("nfp") == 2 and type(data["nfp"]) is int and data.get("lasym", False) is False,
        "symmetric nfp2 boundary required",
    )
    integer(data.get("mpol"), 2)
    integer(data.get("ntor"), 0)
    require(
        data.get("rbs") in (None, []) and data.get("zbc") in (None, []),
        "no hidden asymmetric modes",
    )
    result = []
    for row in data[key]:
        m, n = row["m"], row["n"]
        require(
            type(m) is int and type(n) is int and 0 <= m < data["mpol"] and abs(n) <= data["ntor"],
            "explicit in-range boundary Fourier modes",
        )
        value = finite(row["value"])
        require(value.shape == (), "scalar Fourier amplitude required")
        result.append((m, n, float(value)))
    require(
        result and len({(m, n) for m, n, _ in result}) == len(result),
        "nonempty unique Fourier mode list",
    )
    return result


def derivative_bounds(data):
    r, z = modes(data, "rbc"), modes(data, "zbs")
    sr = sum(abs(v) for _, _, v in r)
    rt = 2 * np.pi * sum(abs(m * v) for m, _, v in r)
    rp = 4 * np.pi * sum(abs(n * v) for _, n, v in r)
    zt = 2 * np.pi * sum(abs(m * v) for m, _, v in z)
    zp = 4 * np.pi * sum(abs(n * v) for _, n, v in z)
    return dict(
        theta=float(np.hypot(rt, zt)),
        phi=float(np.sqrt(rp * rp + zp * zp + (2 * np.pi * sr) ** 2)),
        radius_theta=float(rt),
        radius_phi=float(rp),
    )


def surface(data, nphi=256, ntheta=256, offset=0):
    integer(nphi, 4)
    integer(ntheta, 4)
    require(offset in (0, 0.5), "registered shifted/unshifted surface grid")
    phi = 2 * np.pi * (np.arange(nphi) + offset) / nphi
    theta = 2 * np.pi * (np.arange(ntheta) + offset) / ntheta
    radius, height = np.zeros((nphi, ntheta)), np.zeros((nphi, ntheta))
    for m, n, value in modes(data, "rbc"):
        radius += value * np.cos(m * theta[None, :] - 2 * n * phi[:, None])
    for m, n, value in modes(data, "zbs"):
        height += value * np.sin(m * theta[None, :] - 2 * n * phi[:, None])
    points = np.stack(
        (radius * np.cos(phi[:, None]), radius * np.sin(phi[:, None]), height), axis=-1
    )
    bounds = derivative_bounds(data)
    pad = float(128 * np.finfo(float).eps * max(1.0, float(abs(points).max())))
    cover = bounds["phi"] / (2 * nphi) + bounds["theta"] / (2 * ntheta) + pad
    radius_lower = (
        float(radius.min())
        - bounds["radius_phi"] / (2 * nphi)
        - bounds["radius_theta"] / (2 * ntheta)
        - pad
    )
    require(radius_lower > 0, "continuous positive plasma radius must be certified")
    return dict(
        points=points,
        bounds=bounds,
        pad=pad,
        cover=float(cover),
        radius_lower=float(radius_lower),
        nphi=nphi,
        ntheta=ntheta,
        offset=offset,
        full_torus=True,
    )


def origin(inputs, phi):
    phi = float(finite(phi))
    require(isinstance(inputs, (tuple, list)) and len(inputs) > 0, "ordered inputs required")
    centers = []
    for data in inputs:
        radius = sum(v * np.cos(2 * n * phi) for m, n, v in modes(data, "rbc") if m == 0)
        height = -sum(v * np.sin(2 * n * phi) for m, n, v in modes(data, "zbs") if m == 0)
        centers.append([radius, height])
    return np.asarray(centers).mean(axis=0)


def envelope(surface_rows, phi, d, r_floor, center):
    phi, d, r_floor = map(float, finite([phi, d, r_floor]))
    center = finite(center)
    require(
        center.shape == (2,) and d > 0 and r_floor > 0 and len(surface_rows) > 0,
        "positive safeguards and two-dimensional origin required",
    )
    centers, radii, targets, indices, expansions, pads = [], [], [], [], [], []
    cosine, sine = np.cos(phi), np.sin(phi)
    for target, row in enumerate(surface_rows):
        p = finite(row["points"]).reshape(-1, 3)
        cover = float(finite(row["cover"]))
        require(
            cover > 0 and row["full_torus"] is True and float(finite(row["radius_lower"])) > 0,
            "qualified continuous full-torus input required",
        )
        expanded = d + cover
        eta = float(
            1e-12 * max(1.0, np.linalg.norm(p, axis=1).max(), expanded, np.linalg.norm(center))
        )
        radial = p[:, 0] * cosine + p[:, 1] * sine
        transverse = -p[:, 0] * sine + p[:, 1] * cosine
        retained = np.flatnonzero(
            (abs(transverse) <= expanded + eta) & (radial + expanded + 2 * eta >= r_floor)
        )
        normal_lower = np.maximum(abs(transverse[retained]) - eta, 0.0)
        squared = (expanded + eta - normal_lower) * (expanded + eta + normal_lower)
        centers.append(np.stack((radial[retained], p[retained, 2]), axis=1) - center)
        radii.append(np.sqrt(np.maximum(squared, 0.0)) + eta)
        indices.append(retained)
        targets.append(np.full(len(retained), target, dtype=int))
        expansions.append(expanded)
        pads.append(eta)
    require(sum(len(v) for v in radii) > 0, "empty retained safety envelope")
    return dict(
        centers=np.concatenate(centers),
        radii=np.concatenate(radii),
        target_index=np.concatenate(targets),
        grid_index=np.concatenate(indices),
        expansions=np.asarray(expansions),
        pads=np.asarray(pads),
        center=center.copy(),
        phi=phi,
        d=d,
        r_floor=r_floor,
    )


def support_basis(K, angles):
    integer(K)
    angles = finite(angles)
    require(angles.ndim == 1 and len(angles) > 0, "normal-angle vector required")
    return np.column_stack(
        [np.ones(len(angles))] + [f(m * angles) for m in range(1, K + 1) for f in (np.sin, np.cos)]
    )


def disk_support(centers, radii, angles):
    centers, radii, angles = map(finite, (centers, radii, angles))
    require(
        radii.ndim == 1
        and len(radii) > 0
        and centers.shape == (len(radii), 2)
        and np.all(radii >= 0)
        and angles.ndim == 1
        and len(angles) > 0,
        "matched nonempty positive disks and angle grid",
    )
    output = np.full(len(angles), -np.inf)
    c, s = np.cos(angles), np.sin(angles)
    for first in range(0, len(radii), 1024):
        block = centers[first : first + 1024]
        values = block[:, 0, None] * c + block[:, 1, None] * s + radii[first : first + 1024, None]
        output = np.maximum(output, values.max(axis=0))
    return output


def problem(disks, K, center_r, r_floor, nangle=1024):
    integer(K)
    integer(nangle, 8)
    center_r, r_floor = map(float, finite([center_r, r_floor]))
    require(K <= 6 and nangle > 2 * K and r_floor > 0, "resolved registered support LP")
    angles = np.arange(nangle) * 2 * np.pi / nangle
    basis = support_basis(K, angles)
    frequencies = np.repeat(np.arange(1, K + 1), 2)
    rho_factors = np.r_[1.0, 1 - frequencies**2]
    support = disk_support(disks["centers"], disks["radii"], angles)
    ls = float(np.linalg.norm(disks["centers"], axis=1).max())
    delta, nh, nv = np.pi / nangle, 2 * K + 1, 4 * K + 1
    a = np.zeros((2 * nangle + 1 + 4 * K, nv))
    b = np.zeros(len(a))
    a[:nangle, :nh] = -basis
    a[:nangle, nh:] = delta * frequencies
    b[:nangle] = -(support + delta * ls + 1e-9)
    a[nangle : 2 * nangle, :nh] = -basis * rho_factors
    a[nangle : 2 * nangle, nh:] = delta * frequencies * abs(1 - frequencies**2)
    b[nangle : 2 * nangle] = -0.10 - 1e-9
    a[2 * nangle, 0] = 1
    a[2 * nangle, 2:nh:2] = [(-1) ** m for m in range(1, K + 1)]
    b[2 * nangle] = center_r - r_floor - 1e-9
    for j in range(2 * K):
        a[2 * nangle + 1 + 2 * j, 1 + j] = 1
        a[2 * nangle + 2 + 2 * j, 1 + j] = -1
        a[2 * nangle + 1 + 2 * j : 2 * nangle + 3 + 2 * j, nh + j] = -1
    objective = np.zeros(nv)
    objective[0] = 2 * np.pi
    return dict(
        c=objective,
        A=a,
        b=b,
        lower=np.r_[0.0, np.full(2 * K, -0.5), np.zeros(2 * K)],
        upper=np.r_[1.5, np.full(4 * K, 0.5)],
        angles=angles,
        support=support,
        support_lipschitz=ls,
        K=K,
        nangle=nangle,
        center_r=center_r,
        r_floor=r_floor,
    )


def solver_identity(solution):
    require(
        solution.get("method") == "highs-ds"
        and solution.get("options")
        == dict(
            time_limit=30.0,
            primal_feasibility_tolerance=1e-10,
            dual_feasibility_tolerance=1e-10,
            threads=1,
            parallel=False,
        ),
        "registered single-thread LP method and options",
    )
    expected = dict(
        category="OptimizeWarning",
        message=(
            "Unrecognized options detected: {'threads': 1, 'parallel': False}. "
            "These will be passed to HiGHS verbatim."
        ),
    )
    require(
        solution.get("warnings") == [expected], "exact preserved HiGHS option forwarding notice"
    )


def dual_certificate(model, solution):
    """Unscaled original-LP certificate; no claim of infeasibility without a witness."""
    solver_identity(solution)
    if solution.get("success") is not True or solution.get("status") != 0:
        return dict(solved=False, passed=False, infeasibility_proven=False)
    c, a, b, lo, hi = [finite(model[k]) for k in ("c", "A", "b", "lower", "upper")]
    x, y, yl, yu, slack = [
        finite(solution[k])
        for k in ("x", "inequality_marginals", "lower_marginals", "upper_marginals", "slack")
    ]
    require(
        a.shape == (len(b), len(c))
        and x.shape == lo.shape == hi.shape == c.shape
        and yl.shape == yu.shape == c.shape
        and y.shape == slack.shape == b.shape,
        "complete primal/dual arrays",
    )
    residual = b - a @ x
    primal = max(0.0, float((-residual).max()), float((lo - x).max()), float((x - hi).max()))
    objective = float(c @ x)
    dual_objective = float(b @ y + lo @ yl + hi @ yu)
    errors = dict(
        primal=primal,
        dual_sign=max(0.0, float(y.max()), float((-yl).max()), float(yu.max())),
        stationarity=float(abs(c - a.T @ y - yl - yu).max()),
        complementarity=max(
            float(abs(y * residual).max()),
            float(abs(yl * (x - lo)).max()),
            float(abs(yu * (hi - x)).max()),
        ),
        primal_dual_gap=abs(objective - dual_objective),
        reported_objective=abs(float(finite(solution["objective"])) - objective),
        reported_slack=float(abs(slack - residual).max()),
    )
    passed = errors["primal"] <= 1e-10 and all(
        value <= (5e-12 if key in ("reported_objective", "reported_slack") else 1e-8)
        for key, value in errors.items()
        if key != "primal"
    )
    return dict(
        solved=True,
        errors=errors,
        objective=objective,
        dual_objective=dual_objective,
        passed=bool(passed),
        infeasibility_proven=False,
    )


def continuous_certificate(model, h, disks, center, r_floor):
    h, center = finite(h), finite(center)
    K, n = model["K"], model["nangle"]
    require(
        h.shape == (2 * K + 1,) and center.shape == (2,), "complete support coefficients and origin"
    )
    basis = support_basis(K, model["angles"])
    frequency = np.repeat(np.arange(1, K + 1), 2)
    lh = float(frequency @ abs(h[1:]))
    lrho = float((frequency * abs(1 - frequency**2)) @ abs(h[1:]))
    support = disk_support(disks["centers"], disks["radii"], model["angles"])
    ls = float(np.linalg.norm(disks["centers"], axis=1).max())
    pad = float(128 * np.finfo(float).eps * max(1.0, abs(h).sum(), abs(center).max(), ls))
    enclosure = float((basis @ h - support).min() - np.pi / n * (lh + ls) - pad)
    rho_lower = float((basis @ (h * np.r_[1, 1 - frequency**2])).min() - np.pi / n * lrho - pad)
    radial = float(center[0] - h[0] - sum((-1) ** m * h[2 * m] for m in range(1, K + 1)) - pad)
    length = float(2 * np.pi * h[0])
    length_upper = float(length + 2 * np.pi * pad)
    curvature = float(1 / rho_lower) if rho_lower > 0 else None
    support_pass = enclosure >= 0 and rho_lower >= 0.10 and radial >= r_floor
    return dict(
        enclosure_lower=enclosure,
        rho_lower=rho_lower,
        radial_lower=radial,
        length=length,
        length_upper=length_upper,
        curvature_upper=curvature,
        L_h=lh,
        L_rho=lrho,
        L_S=ls,
        floating_pad=pad,
        interval_arithmetic=False,
        support_pass=bool(support_pass),
        length_pass=bool(0 < length and length_upper <= 3.5),
        curvature_pass=bool(curvature is not None and curvature <= 12),
        planar_self_disjoint=bool(rho_lower > 0),
    )


def export_certificate(ideal, h, expected, actual, r_floor, safety_distance):
    """Transfer the ideal support proof to the actual serialized Fourier curve.

    A 5e-12 raw reconstruction screen is not itself a physical error budget.
    Position and two derivative error bounds explicitly consume gate margins.
    Tiny nonplanar roundoff is allowed only with a simple convex projection.
    """
    h, expected, actual = finite(h), finite(expected), finite(actual)
    require(
        expected.shape == actual.shape and expected.shape[0] == 3,
        "complete matching Cartesian Fourier curves",
    )
    compare(actual, expected, "exported certificate curve")
    order = (expected.shape[1] - 1) // 2
    pad = float(
        128 * np.finfo(float).eps * max(1.0, abs(expected).sum(), abs(actual).sum(), abs(h).sum())
    )
    delta = abs(actual - expected) + pad
    amplitudes = np.hypot(delta[:, 1::2], delta[:, 2::2])
    frequency = 2 * np.pi * np.arange(1, order + 1)
    errors = [float(np.linalg.norm(delta[:, 0] + amplitudes.sum(axis=1)) + pad)]
    errors += [float(np.linalg.norm((amplitudes * frequency**r).sum(axis=1)) + pad) for r in (1, 2)]
    e0, e1, e2 = errors
    mfreq = np.repeat(np.arange(1, (len(h) - 1) // 2 + 1), 2)
    rho_upper = float(h[0] + abs(1 - mfreq**2) @ abs(h[1:]) + pad)
    vmin = float(2 * np.pi * ideal["rho_lower"])
    vmax = float(2 * np.pi * max(0.0, rho_upper))
    amax = float((2 * np.pi) ** 2 * np.hypot(rho_upper, ideal["L_rho"] + pad))
    cross_error = float(e1 * amax + vmax * e2 + e1 * e2 + pad)
    speed_lower = float(vmin - e1)
    curvature = None
    if speed_lower > 0 and ideal["curvature_upper"] is not None:
        curvature = float(
            ideal["curvature_upper"] * (vmin / speed_lower) ** 3
            + cross_error / speed_lower**3
            + pad
        )
    signed_cross_lower = float(
        (2 * np.pi) ** 3 * max(0.0, ideal["rho_lower"]) ** 2 - cross_error - pad
    )
    projection_simple = speed_lower > 0 and signed_cross_lower > 0
    length_upper = float(ideal["length_upper"] + e1 + pad)
    radial_lower = float(ideal["radial_lower"] - e0 - pad)
    enclosure_lower = float(ideal["enclosure_lower"] - e0 - pad)
    plasma_lower = float(safety_distance - e0 - pad)
    return dict(
        position_error=e0,
        first_derivative_error=e1,
        second_derivative_error=e2,
        coefficient_rounding_pad=pad,
        speed_lower=speed_lower,
        signed_projection_cross_lower=signed_cross_lower,
        controlled_projection_self_disjoint=bool(projection_simple),
        length_upper=length_upper,
        curvature_upper=curvature,
        radial_lower=radial_lower,
        enclosure_lower=enclosure_lower,
        analytic_plasma_lower=plasma_lower,
        support_pass=bool(
            ideal["support_pass"]
            and enclosure_lower >= 0
            and radial_lower >= r_floor
            and projection_simple
        ),
        length_pass=bool(ideal["length_pass"] and length_upper <= 3.5),
        curvature_pass=bool(curvature is not None and curvature <= 12),
        plasma_pass=bool(ideal["support_pass"] and plasma_lower >= 0.08),
        interval_arithmetic=False,
    )


def export_coefficients(h, center, phi, order):
    """Real product-to-sum reconstruction, separate from producer's complex convolution."""
    h, center = finite(h), finite(center)
    integer(order)
    phi = float(finite(phi))
    require(
        h.ndim == 1 and len(h) >= 3 and len(h) % 2 == 1 and center.shape == (2,),
        "complete odd support coefficients and planar center",
    )
    K = (len(h) - 1) // 2
    require(K + 1 <= order, "no support Fourier truncation")
    rz = np.zeros((2, 2 * order + 1))
    rz[:, 0] = center
    rz[0, 2], rz[1, 1] = h[0], -h[0]
    for m in range(1, K + 1):
        b, a = h[2 * m - 1 : 2 * m + 1]
        if m == 1:
            rz[:, 0] += [a, b]
        else:
            k = m - 1
            rz[0, 2 * k] += a * (m + 1) / 2
            rz[0, 2 * k - 1] -= b * (m + 1) / 2
            rz[1, 2 * k - 1] += a * (m + 1) / 2
            rz[1, 2 * k] += b * (m + 1) / 2
        k = m + 1
        rz[0, 2 * k] += a * (1 - m) / 2
        rz[0, 2 * k - 1] -= b * (1 - m) / 2
        rz[1, 2 * k - 1] -= a * (1 - m) / 2
        rz[1, 2 * k] += b * (m - 1) / 2
    return np.stack((math.cos(phi) * rz[0], math.sin(phi) * rz[0], rz[1]))


def parameter_names(nbase, order):
    return [
        f"coil[{i}]/{axis}{kind}({m})"
        for i in range(nbase)
        for axis in "xyz"
        for kind, m in [("c", 0)] + [(k, j) for j in range(1, order + 1) for k in ("s", "c")]
    ]


def physical_rows(nbase):
    rows = []
    for period in range(2):
        c, s = np.cos(np.pi * period), np.sin(np.pi * period)
        rotation = np.array([[c, s, 0.0], [-s, c, 0.0], [0.0, 0.0, 1.0]])
        for flip in (False, True):
            matrix = rotation @ np.diag([1.0, -1.0, -1.0]) if flip else rotation
            rows.extend(
                dict(base_index=i, period=period, flip=flip, matrix=matrix.tolist())
                for i in range(nbase)
            )
    return rows


def validate_snapshot(snapshot):
    require(
        set(snapshot)
        == {
            "schema_version",
            "kind",
            "nfp",
            "nbase",
            "order",
            "names",
            "base_coefficients",
            "physical",
            "case",
            "sources",
            "parameter_orientation",
        },
        "geometry-only snapshot keys",
    )
    require(
        snapshot["schema_version"] == 1
        and type(snapshot["schema_version"]) is int
        and snapshot["kind"] == "geometry-only"
        and snapshot["nfp"] == 2
        and type(snapshot["nfp"]) is int,
        "geometry-only nfp2 schema1",
    )
    n, order = snapshot["nbase"], snapshot["order"]
    require(
        type(n) is int and type(order) is int and (n, order) in ((6, 5), (8, 7)),
        "registered coil class",
    )
    require(snapshot["names"] == parameter_names(n, order), "canonical physical names")
    require(
        snapshot["case"] in cases()
        and snapshot["case"]["nbase"] == n
        and snapshot["case"]["order"] == order
        and snapshot["parameter_orientation"] == "alpha=-2*pi*t"
        and set(snapshot["sources"]) == {"reference", "selected"},
        "registered geometry case, source labels and clockwise parameter orientation",
    )
    coefficient = finite(snapshot["base_coefficients"])
    require(coefficient.shape == (n, 3, 2 * order + 1), "complete canonical Fourier geometry")
    expected = physical_rows(n)
    require(len(snapshot["physical"]) == len(expected), "all physical copies required")
    for actual, row in zip(snapshot["physical"], expected, strict=True):
        require(
            set(actual) == set(row)
            and type(actual["flip"]) is bool
            and type(actual["period"]) is int
            and type(actual["base_index"]) is int,
            "typed geometry mapping without currents",
        )
        require(actual == row, "exact physical rotation/reflection mapping")


def physical_curves(snapshot, ncoil=1024):
    validate_snapshot(snapshot)
    integer(ncoil, 4)
    order = snapshot["order"]
    t = 2 * np.pi * np.arange(ncoil) / ncoil
    base = finite(snapshot["base_coefficients"])
    coefficients = np.asarray(
        [np.asarray(row["matrix"]).T @ base[row["base_index"]] for row in snapshot["physical"]]
    )
    results = []
    for derivative in (0, 1, 2):
        out = np.zeros((len(coefficients), ncoil, 3))
        if derivative == 0:
            out += coefficients[:, :, 0, None].transpose(0, 2, 1)
        for k in range(1, order + 1):
            phase = k * t + derivative * np.pi / 2
            out += (2 * np.pi * k) ** derivative * (
                coefficients[:, None, :, 2 * k - 1] * np.sin(phase)[None, :, None]
                + coefficients[:, None, :, 2 * k] * np.cos(phase)[None, :, None]
            )
        results.append(out)
    speed = np.linalg.norm(results[1], axis=-1)
    require(np.all(speed > 0), "no stationary filament")
    amplitudes = np.hypot(coefficients[..., 1::2], coefficients[..., 2::2])
    vmax = np.linalg.norm(
        np.sum(amplitudes * (2 * np.pi * np.arange(1, order + 1)), axis=-1), axis=-1
    )
    return dict(
        positions=results[0],
        tangents=results[1],
        second=results[2],
        speed=speed,
        speed_upper=vmax,
        coefficients=coefficients,
    )


def distance_certificate(snapshot, target, ncoil=1024):
    curves = physical_curves(snapshot, ncoil)
    p = curves["positions"]
    require(
        target["full_torus"] is True
        and float(finite(target["radius_lower"])) > 0
        and float(finite(target["cover"])) > 0,
        "certified full-torus target covering",
    )
    plasma = finite(target["points"]).reshape(-1, 3)
    pad = float(128 * np.finfo(float).eps * max(1.0, abs(p).max(), abs(plasma).max()))
    cover = curves["speed_upper"] / (2 * ncoil) + pad
    trees = [cKDTree(row) for row in p]
    pairs = []
    for i in range(len(p)):
        for j in range(i + 1, len(p)):
            sampled = float(trees[j].query(p[i], workers=1)[0].min())
            pairs.append(
                dict(
                    i=i,
                    j=j,
                    sampled=sampled,
                    lower=float(max(0.0, sampled - cover[i] - cover[j] - pad)),
                )
            )
    tree = cKDTree(plasma)
    distances = []
    for i, row in enumerate(p):
        sampled = float(tree.query(row, workers=1)[0].min())
        distances.append(
            dict(
                i=i,
                sampled=sampled,
                lower=float(max(0.0, sampled - cover[i] - target["cover"] - pad)),
            )
        )
    speed = curves["speed"]
    curvature = np.linalg.norm(np.cross(curves["tangents"], curves["second"]), axis=-1) / speed**3
    return dict(
        ncoil=ncoil,
        nphi=target["nphi"],
        ntheta=target["ntheta"],
        offset=target["offset"],
        full_torus=True,
        curve_cover=cover.tolist(),
        surface_cover=float(target["cover"]),
        floating_pad=pad,
        interval_arithmetic=False,
        coil_pairs=pairs,
        plasma_distances=distances,
        lengths_sampled=speed.mean(axis=1).tolist(),
        curvature_sampled=curvature.max(axis=1).tolist(),
        sampled_length_pass=bool(np.all(speed.mean(axis=1) <= 3.5)),
        sampled_curvature_pass=bool(np.all(curvature <= 12)),
        coil_pass=bool(all(row["lower"] >= 0.06 for row in pairs)),
        plasma_pass=bool(all(row["lower"] >= 0.08 for row in distances)),
    )
