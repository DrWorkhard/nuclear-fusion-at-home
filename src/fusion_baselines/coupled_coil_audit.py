"""Independent NumPy/SciPy reconstruction for the registered coupled-coil pilot.

No producer/native field or geometry code is imported. Derivatives use unit-period
parameters throughout. Conservative geometric bounds include explicit floating
point pads, not directed interval arithmetic or a complete self-intersection proof.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.spatial import cKDTree


def _integer(value, minimum=1):
    if type(value) is not int or value < minimum:
        raise ValueError("integer dimension required")
    return value


def _finite(value):
    answer = np.asarray(value, dtype=float)
    if not np.isfinite(answer).all():
        raise ValueError("nonfinite numerical data")
    return answer


def _scalar(value):
    answer = _finite(value)
    if answer.shape != ():
        raise ValueError("finite scalar required")
    return float(answer)


def parameter_names(nbase, order):
    return [
        f"coil[{i}]/{axis}{term}({mode})"
        for i in range(nbase)
        for axis in "xyz"
        for term, mode in [("c", 0)]
        + [(kind, k) for k in range(1, order + 1) for kind in ("s", "c")]
    ]


def validate_snapshot(snapshot):
    """Fail closed on mislabelled DOFs, absent copies or changed current signs."""
    if (
        not isinstance(snapshot, dict)
        or type(snapshot.get("schema_version")) is not int
        or snapshot["schema_version"] != 1
    ):
        raise ValueError("snapshot schema_version 1 required")
    nbase = _integer(snapshot.get("nbase"))
    order = _integer(snapshot.get("order"))
    if (
        type(snapshot.get("nfp")) is not int
        or snapshot["nfp"] != 2
        or (nbase, order) not in ((6, 5), (8, 7))
    ):
        raise ValueError("registered nfp2 six/order5 or eight/order7 class required")
    if snapshot.get("names") != parameter_names(nbase, order):
        raise ValueError("explicit canonical physical parameter mapping required")
    coefficients = _finite(snapshot.get("base_coefficients"))
    if coefficients.shape != (nbase, 3, 2 * order + 1):
        raise ValueError("base Fourier shape mismatch")
    for key in ("scale", "B2_scale", "unit_flux", "target_flux"):
        _scalar(snapshot.get(key))
    if (
        snapshot["B2_scale"] <= 0
        or abs(snapshot["unit_flux"]) <= 1e-12
        or snapshot["target_flux"] == 0
        or snapshot["scale"] != snapshot["target_flux"] / snapshot["unit_flux"]
    ):
        raise ValueError("positive field scale and exact nonzero flux normalization required")
    physical = snapshot.get("physical")
    if not isinstance(physical, list) or len(physical) != 4 * nbase:
        raise ValueError("every physical coil copy required")
    for period in range(2):
        angle = 2 * np.pi * period / 2
        c, s = np.cos(angle), np.sin(angle)
        rotation = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
        for flip in (False, True):
            matrix = rotation.T @ (np.diag([1.0, -1.0, -1.0]) if flip else np.eye(3))
            for base in range(nbase):
                row = physical[(2 * period + int(flip)) * nbase + base]
                if (
                    not isinstance(row, dict)
                    or type(row.get("base_index")) is not int
                    or row["base_index"] != base
                    or type(row.get("period")) is not int
                    or row["period"] != period
                    or type(row.get("flip")) is not bool
                    or row["flip"] != flip
                ):
                    raise ValueError("period/flip/base physical ordering mismatch")
                actual = _finite(row.get("matrix"))
                current = _scalar(row.get("current"))
                if (
                    actual.shape != (3, 3)
                    or not np.array_equal(actual, matrix)
                    or np.shape(current) != ()
                    or not np.isfinite(current)
                    or current != 100000.0 * snapshot["scale"] * (-1 if flip else 1)
                ):
                    raise ValueError("physical rotation/reflection/current mismatch")


def fourier_curves(coefficients, count):
    """Coordinates and first three derivatives of c0,s1,c1,... curves."""
    count = _integer(count, 4)
    coefficients = _finite(coefficients)
    if coefficients.ndim != 3 or coefficients.shape[1] != 3:
        raise ValueError("(curves,3,odd coefficients) required")
    width = coefficients.shape[-1]
    if not len(coefficients) or width < 3 or width % 2 != 1:
        raise ValueError("nonconstant Fourier curves required")
    order = (width - 1) // 2
    t = np.arange(count) / count
    values = []
    for derivative in range(4):
        basis = np.zeros((count, width))
        if derivative == 0:
            basis[:, 0] = 1.0
        for k in range(1, order + 1):
            phase = 2 * np.pi * k * t + derivative * np.pi / 2
            multiplier = (2 * np.pi * k) ** derivative
            basis[:, 2 * k - 1] = multiplier * np.sin(phase)
            basis[:, 2 * k] = multiplier * np.cos(phase)
        values.append(np.einsum("pac,nc->pna", coefficients, basis))
    return dict(zip(("positions", "tangents", "second", "third"), values, strict=True))


def physical_curves(snapshot, ncoil=128):
    validate_snapshot(snapshot)
    base = np.asarray(snapshot["base_coefficients"], dtype=float)
    coefficients = np.array(
        [np.asarray(row["matrix"]).T @ base[row["base_index"]] for row in snapshot["physical"]]
    )
    answer = fourier_curves(coefficients, ncoil)
    answer["currents"] = np.array([row["current"] for row in snapshot["physical"]])
    answer["coefficients"] = coefficients
    if np.any(np.linalg.norm(answer["tangents"], axis=-1) == 0):
        raise ValueError("zero-speed filament")
    return answer


def filament_field_and_potential(points, positions, tangents, currents, chunk_size=128):
    """Direct periodic sums in SI, with a bounded point/source working array."""
    points, positions, tangents, currents = map(_finite, (points, positions, tangents, currents))
    _integer(chunk_size)
    if (
        points.ndim != 2
        or points.shape[1] != 3
        or not len(points)
        or positions.ndim != 3
        or positions.shape[-1] != 3
        or not all(positions.shape[:2])
        or tangents.shape != positions.shape
        or currents.shape != (len(positions),)
    ):
        raise ValueError("nonempty matched point and filament arrays required")
    magnetic, potential = np.zeros_like(points), np.zeros_like(points)
    for first in range(0, len(points), chunk_size):
        last = min(len(points), first + chunk_size)
        for p, velocity, current in zip(positions, tangents, currents, strict=True):
            delta = points[first:last, None, :] - p[None, :, :]
            radius = np.linalg.norm(delta, axis=-1)
            if np.any(radius == 0):
                raise ValueError("field point coincides with filament quadrature node")
            magnetic[first:last] += (
                1e-7
                * current
                * np.mean(np.cross(velocity[None, :, :], delta) / radius[..., None] ** 3, axis=1)
            )
            potential[first:last] += (
                1e-7 * current * np.mean(velocity[None, :, :] / radius[..., None], axis=1)
            )
    if not np.isfinite(magnetic).all() or not np.isfinite(potential).all():
        raise ValueError("nonfinite direct field/potential")
    return magnetic, potential


def _boundary_input(input_json):
    document = (
        json.loads(Path(input_json).read_text())
        if isinstance(input_json, (str, Path))
        else input_json
    )
    if not isinstance(document, dict) or document.get("lasym") is not False:
        raise ValueError("stellarator-symmetric input dictionary required")
    nfp = _integer(document.get("nfp"))
    mpol, ntor = _integer(document.get("mpol")), _integer(document.get("ntor"), 0)
    coefficients = {}
    for key in ("rbc", "zbs"):
        rows = document.get(key)
        if not isinstance(rows, list) or not rows:
            raise ValueError("complete explicit boundary Fourier list required")
        modes = []
        for row in rows:
            if (
                not isinstance(row, dict)
                or type(row.get("m")) is not int
                or type(row.get("n")) is not int
                or not 0 <= row["m"] < mpol
                or abs(row["n"]) > ntor
                or np.shape(row.get("value")) != ()
                or not np.isfinite(row.get("value"))
            ):
                raise ValueError("invalid boundary mode")
            modes.append((row["m"], row["n"], float(row["value"])))
        if len({(m, n) for m, n, _ in modes}) != len(modes):
            raise ValueError("duplicate boundary mode")
        coefficients[key] = np.asarray(modes)
    for key in ("rbs", "zbc"):
        if document.get(key) not in (None, []):
            raise ValueError("asymmetric boundary coefficients are unsupported")
    return document, nfp, coefficients


def _rz(input_json, theta, phi):
    _, nfp, coefficients = _boundary_input(input_json)
    theta, phi = np.broadcast_arrays(_finite(theta), _finite(phi))
    values = {}
    for key, modes in coefficients.items():
        m, n, amplitudes = modes.T
        phase = theta[..., None] * m - phi[..., None] * n * nfp
        cosine, sine = np.cos(phase), np.sin(phase)
        if key == "rbc":
            value = cosine @ amplitudes
            dt = sine @ (-m * amplitudes * 2 * np.pi)
            dp = sine @ (n * nfp * amplitudes * 2 * np.pi)
        else:
            value = sine @ amplitudes
            dt = cosine @ (m * amplitudes * 2 * np.pi)
            dp = cosine @ (-n * nfp * amplitudes * 2 * np.pi)
        values[key] = (value, dt, dp)
    radius, rt, rp = values["rbc"]
    z, zt, zp = values["zbs"]
    if np.any(radius <= 0):
        raise ValueError("nonpositive cylindrical boundary radius")
    c, s = np.cos(phi), np.sin(phi)
    points = np.stack((radius * c, radius * s, z), axis=-1)
    dtheta = np.stack((rt * c, rt * s, zt), axis=-1)
    dphi = np.stack((rp * c - 2 * np.pi * radius * s, rp * s + 2 * np.pi * radius * c, zp), axis=-1)
    return points, dtheta, dphi


def boundary(input_json, nphi, ntheta, full_torus=False, shift=False):
    _integer(nphi, 2)
    _integer(ntheta, 4)
    _, nfp, _ = _boundary_input(input_json)
    offset = 0.5 if shift else 0.0
    phi, theta = np.meshgrid(
        2 * np.pi * (np.arange(nphi) + offset) / (nphi * (1 if full_torus else nfp)),
        2 * np.pi * (np.arange(ntheta) + offset) / ntheta,
        indexing="ij",
    )
    points, dt, dp = _rz(input_json, theta, phi)
    normal = np.cross(dp, dt)
    weight = np.linalg.norm(normal, axis=-1)
    if np.any(weight <= 0) or not np.isfinite(weight).all():
        raise ValueError("degenerate boundary surface")
    return dict(
        points=points,
        dtheta=dt,
        dphi=dp,
        normal=normal,
        unitnormal=normal / weight[..., None],
        weights=weight / weight.sum(),
        theta=theta,
        phi=phi,
    )


def loop(input_json, ntheta):
    _integer(ntheta, 4)
    points, tangent, _ = _rz(input_json, 2 * np.pi * np.arange(ntheta) / ntheta, 0.0)
    return points, tangent


def fan_area(input_json, nrho, ntheta):
    """Signed fan quadrature: sum(B * weighted_normals), not mean, is flux."""
    _integer(nrho, 2)
    points, tangent = loop(input_json, ntheta)
    reference, _ = loop(input_json, 1024)
    center = reference.mean(axis=0)
    radial = points - center
    jacobian = np.cross(radial, tangent)
    sign = jacobian[:, 1]
    if (
        np.any(sign == 0)
        or np.any(sign * sign[0] <= 0)
        or center[0] <= 0
        or np.any(jacobian[:, (0, 2)] != 0)
    ):
        raise ValueError("fan must have a constant nonzero signed Jacobian and R>0")
    nodes, weights = leggauss(nrho)
    rho, weights = (nodes + 1) / 2, weights / 2
    quadrature = center + rho[:, None, None] * radial[None, :, :]
    normals = weights[:, None, None] * rho[:, None, None] * jacobian[None, :, :] / ntheta
    if np.any(quadrature[..., 0] <= 0):
        raise ValueError("nonpositive fan radius")
    return quadrature.reshape(-1, 3), normals.reshape(-1, 3)


def metrics(B, normal, weights, B2_scale):
    B, normal, weights = map(_finite, (B, normal, weights))
    if (
        B.shape != normal.shape
        or B.shape[-1:] != (3,)
        or not B.size
        or weights.shape != B.shape[:-1]
        or np.any(weights <= 0)
        or not np.isfinite(B2_scale)
        or B2_scale <= 0
    ):
        raise ValueError("matched fields, normals, positive area weights and field scale required")
    magnitudes = np.linalg.norm(B, axis=-1)
    normal_size = np.linalg.norm(normal, axis=-1)
    if np.any(magnitudes <= 0) or np.any(normal_size <= 0):
        raise ValueError("zero magnetic field or normal")
    bn = np.sum(B * normal / normal_size[..., None], axis=-1)
    w = weights / weights.sum()
    relative = abs(bn) / magnitudes
    return dict(
        JN=float(0.5 * np.sum(w * bn**2) / B2_scale),
        normal_rms=float(np.sqrt(np.sum(w * relative**2))),
        normal_max=float(relative.max()),
        mean_B=float(np.sum(w * magnitudes)),
        raw_bn_rms=float(np.sqrt(np.sum(w * bn**2))),
        raw_bn_max=float(abs(bn).max()),
    )


def inner_metrics(B, target_B, B2_scale):
    B, target_B = map(_finite, (B, target_B))
    if (
        B.shape != target_B.shape
        or B.shape[-1:] != (3,)
        or not B.size
        or not np.isfinite(B2_scale)
        or B2_scale <= 0
    ):
        raise ValueError("matched nonempty vector fields and positive field scale required")
    value = float(np.mean(np.sum((B - target_B) ** 2, axis=-1)) / B2_scale)
    return dict(JV=0.5 * value, vector_rms=float(np.sqrt(value)))


def _curve_measures(curves):
    speed = np.linalg.norm(curves["tangents"], axis=-1)
    if np.any(speed <= 0):
        raise ValueError("degenerate zero-speed curve")
    curvature = np.linalg.norm(np.cross(curves["tangents"], curves["second"]), axis=-1) / speed**3
    return speed, curvature


def _distance_penalty(left, right, speed_left, speed_right, threshold, right_tree=None):
    tree = cKDTree(right) if right_tree is None else right_tree
    pairs = tree.query_ball_point(left, threshold, workers=1)
    total = 0.0
    for i, neighbors in enumerate(pairs):
        if neighbors:
            distance = np.linalg.norm(right[neighbors] - left[i], axis=-1)
            total += speed_left[i] * np.sum(
                np.maximum(threshold - distance, 0) ** 2 * speed_right[neighbors]
            )
    return float(total / (len(left) * len(right)))


def geometry_penalties(snapshot, input_json, ncoil=128):
    """Independent raw native-formula penalties, including all physical pairs."""
    curves = physical_curves(snapshot, ncoil)
    speed, curvature = _curve_measures(curves)
    base_speed, base_curvature = speed[: snapshot["nbase"]], curvature[: snapshot["nbase"]]
    lengths = base_speed.mean(axis=1)
    length = float(0.5 * np.sum(np.maximum(lengths - 3.5, 0) ** 2))
    bending = float(
        0.5 * np.sum(np.mean(np.maximum(base_curvature - 10, 0) ** 2 * base_speed, axis=1))
    )
    positions = curves["positions"]
    trees = [cKDTree(p) for p in positions]
    cc = sum(
        _distance_penalty(positions[i], positions[j], speed[i], speed[j], 0.06, trees[j])
        for i in range(len(positions))
        for j in range(i + 1, len(positions))
    )
    surface = boundary(input_json, 64, 32, full_torus=True)
    target = surface["points"].reshape(-1, 3)
    area = np.linalg.norm(surface["normal"], axis=-1).ravel()
    tree = cKDTree(target)
    cs = sum(
        _distance_penalty(p, target, v, area, 0.08, tree)
        for p, v in zip(positions, speed, strict=True)
    )
    return dict(
        length=length,
        curvature=bending,
        cc=cc,
        cs=cs,
        total=float(length + 1e-4 * bending + 1000 * (cc + cs)),
    )


def derivative_suprema(coefficients):
    """Triangle-inequality bounds on norm of derivatives 1,2,3, in unit t."""
    coefficients = _finite(coefficients)
    if coefficients.ndim != 3 or coefficients.shape[1] != 3 or coefficients.shape[2] % 2 != 1:
        raise ValueError("Fourier coefficient tensor required")
    frequency = 2 * np.pi * np.arange(1, coefficients.shape[2] // 2 + 1)
    amplitudes = np.hypot(coefficients[..., 1::2], coefficients[..., 2::2])
    return np.stack(
        [np.linalg.norm(np.sum(amplitudes * frequency**k, axis=-1), axis=-1) for k in (1, 2, 3)],
        axis=-1,
    )


def surface_derivative_bounds(input_json):
    _, nfp, coefficients = _boundary_input(input_json)
    r, z = coefficients["rbc"], coefficients["zbs"]
    rb = np.sum(abs(r[:, 2]))
    rt, rp = [2 * np.pi * np.sum(abs(r[:, i] * r[:, 2])) for i in (0, 1)]
    zt, zp = [2 * np.pi * np.sum(abs(z[:, i] * z[:, 2])) for i in (0, 1)]
    return dict(
        theta=float(np.hypot(rt, zt)),
        phi=float(np.sqrt((nfp * rp) ** 2 + (2 * np.pi * rb) ** 2 + (nfp * zp) ** 2)),
    )


def geometry_certificates(snapshot, input_json, ncoil=1024, nphi=256, ntheta=256):
    """Conservative continuous bounds; sampled self-nearness is explicitly partial."""
    curves = physical_curves(snapshot, ncoil)
    speed, curvature = _curve_measures(curves)
    positions = curves["positions"]
    sup = derivative_suprema(curves["coefficients"])
    scale = max(1.0, float(np.max(abs(positions))))
    pad = 128 * np.finfo(float).eps * scale
    minimum_speed = speed.min(axis=1) - sup[:, 1] / (2 * ncoil) - pad
    cover = sup[:, 0] / (2 * ncoil) + pad
    if np.any(minimum_speed <= 0):
        raise ValueError("strictly positive speed not certified between curve nodes")
    curvature_lipschitz = sup[:, 2] / minimum_speed**2 + 3 * sup[:, 1] ** 2 / minimum_speed**3
    length_upper = speed.mean(axis=1) + sup[:, 1] / (4 * ncoil) + pad
    curvature_upper = curvature.max(axis=1) + curvature_lipschitz / (2 * ncoil) + pad
    trees = [cKDTree(p) for p in positions]
    pairs = []
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            distance = float(trees[j].query(positions[i], workers=1)[0].min())
            pairs.append(
                dict(
                    i=i, j=j, sampled=distance, lower=max(0.0, distance - cover[i] - cover[j] - pad)
                )
            )
    surface = boundary(input_json, nphi, ntheta, full_torus=True)
    target = surface["points"].reshape(-1, 3)
    surface_sup = surface_derivative_bounds(input_json)
    surface_cover = surface_sup["phi"] / (2 * nphi) + surface_sup["theta"] / (2 * ntheta) + pad
    surface_tree = cKDTree(target)
    plasma = []
    for i, p in enumerate(positions):
        distance = float(surface_tree.query(p, workers=1)[0].min())
        plasma.append(
            dict(i=i, sampled=distance, lower=max(0.0, distance - cover[i] - surface_cover - pad))
        )
    # A full proof of self-disjointness is deliberately not claimed. Nonlocal
    # means periodic index distance >=ceil(N/20), recorded independently of scale.
    exclusion = max(2, int(np.ceil(ncoil / 20)))
    self_rows = []
    for i, p in enumerate(positions):
        nearest = np.inf
        # Trigonometric evaluation of an exact crossing may leave O(eps)
        # differences rather than bit-identical coordinates. Reject such
        # numerical coincidences conservatively; do not claim a full proof.
        nearest_other = float(trees[i].query(p, k=2, workers=1)[0][:, 1].min())
        exact = nearest_other <= pad
        indices = np.arange(ncoil)
        for first in range(0, ncoil, 128):
            source = indices[first : first + 128]
            separation = abs(source[:, None] - indices[None, :])
            separation = np.minimum(separation, ncoil - separation)
            distances = np.linalg.norm(p[source, None, :] - p[None, :, :], axis=-1)
            eligible = separation >= exclusion
            if np.any(eligible):
                nearest = min(nearest, float(distances[eligible].min()))
        if exact:
            raise ValueError("detected coincident non-endpoint filament positions within roundoff")
        self_rows.append(
            dict(
                i=i,
                index_exclusion=exclusion,
                sampled_nonlocal_minimum=nearest,
                sampled_nonself_minimum=nearest_other,
                coincidence_tolerance=pad,
                exact_repeated_node=exact,
                complete_self_proof=False,
            )
        )
    answer = dict(
        ncoil=ncoil,
        nphi=nphi,
        ntheta=ntheta,
        full_torus=True,
        floating_pad=pad,
        interval_arithmetic=False,
        length_sampled=speed.mean(axis=1).tolist(),
        length_upper=length_upper.tolist(),
        curvature_sampled=curvature.max(axis=1).tolist(),
        curvature_upper=curvature_upper.tolist(),
        speed_lower=minimum_speed.tolist(),
        derivative_suprema=sup.tolist(),
        curve_cover=cover.tolist(),
        surface_derivative_bounds=surface_sup,
        surface_cover=float(surface_cover),
        coil_pairs=pairs,
        plasma_distances=plasma,
        coil_lower=min(row["lower"] for row in pairs),
        plasma_lower=min(row["lower"] for row in plasma),
        self_nearness=self_rows,
    )
    answer["geometry_pass"] = bool(
        np.all(length_upper <= 3.5)
        and np.all(curvature_upper <= 12)
        and answer["coil_lower"] >= 0.06
        and answer["plasma_lower"] >= 0.08
    )
    return answer


def refinement_pass(coarse, fine):
    return bool(
        np.isfinite(coarse)
        and np.isfinite(fine)
        and coarse >= 0
        and fine >= 0
        and (abs(fine - coarse) <= 0.01 * coarse or abs(fine - coarse) <= 1e-7)
    )


def entry_gates(
    snapshot, boundary_metrics, inner_values, flux_checks, geometry, refinements, independent_checks
):
    """Small fail-closed aggregate; caller must separately audit grid/source identity.

    Four boundary metrics, three inner metrics, six signed Stokes checks (two
    radial x three angular resolutions), five exact refinement comparisons.
    flux_checks rows supply relative_error (to target), stokes_error, and
    angular_error. No producer booleans alone are accepted for physical metrics.
    """
    validate_snapshot(snapshot)
    valid_counts = (
        len(boundary_metrics) == 4
        and len(inner_values) == 3
        and len(flux_checks) == 6
        and len(refinements) == 5
        and len(independent_checks) > 0
    )

    def finite_below(rows, key, upper):
        return all(key in row and np.isfinite(row[key]) and 0 <= row[key] <= upper for row in rows)

    nphysical = len(snapshot["physical"])
    geometry_pass = False
    try:
        length, curvature, speed = [
            _finite(geometry[key]) for key in ("length_upper", "curvature_upper", "speed_lower")
        ]
        pairs, plasma = geometry["coil_pairs"], geometry["plasma_distances"]
        labels = [(row["i"], row["j"]) for row in pairs]
        expected = [(i, j) for i in range(nphysical) for j in range(i + 1, nphysical)]
        geometry_pass = bool(
            geometry.get("ncoil") == 1024
            and geometry.get("nphi") == 256
            and geometry.get("ntheta") == 256
            and geometry.get("full_torus") is True
            and length.shape == curvature.shape == speed.shape == (nphysical,)
            and np.all((length > 0) & (length <= 3.5))
            and np.all((curvature >= 0) & (curvature <= 12))
            and np.all(speed > 0)
            and labels == expected
            and [row["i"] for row in plasma] == list(range(nphysical))
            and all(np.isfinite(row["lower"]) and row["lower"] >= 0.06 for row in pairs)
            and all(np.isfinite(row["lower"]) and row["lower"] >= 0.08 for row in plasma)
            and len(geometry["self_nearness"]) == nphysical
            and all(
                row["i"] == i
                and row["exact_repeated_node"] is False
                and np.isfinite(row["sampled_nonlocal_minimum"])
                and row["sampled_nonlocal_minimum"] > 0
                for i, row in enumerate(geometry["self_nearness"])
            )
        )
    except (KeyError, TypeError, ValueError):
        geometry_pass = False

    checks = dict(
        complete=valid_counts,
        normal_rms=finite_below(boundary_metrics, "normal_rms", 1e-4),
        normal_max=finite_below(boundary_metrics, "normal_max", 1e-3),
        vector=finite_below(inner_values, "vector_rms", 1e-2),
        flux=all(
            finite_below(flux_checks, k, 1e-6)
            for k in ("relative_error", "stokes_error", "angular_error")
        ),
        current=all(abs(row["current"]) <= 500000 for row in snapshot["physical"]),
        geometry=geometry_pass,
        refinement=all(
            isinstance(pair, (list, tuple)) and len(pair) == 2 and refinement_pass(*pair)
            for pair in refinements
        ),
        independent=all(flag is True for flag in independent_checks),
    )
    return dict(
        checks=checks, entry_pass=bool(all(checks.values())), transfer_pass=False, step4_pass=False
    )
