"""Independent numerical primitives for the clear-coil field-start study.

No producer, native geometry, Wout reader or file-I/O is imported. Source hashes
and execution accounting belong to the later overall auditor. Mathematical
reports contain only strict JSON values; raw target arrays remain NumPy arrays.
"""

import copy
import json

import numpy as np
from scipy.spatial import cKDTree

from fusion_baselines import clear_coil_geometry_audit as clear_geometry
from fusion_baselines import coupled_coil_audit as frozen


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite(value):
    array = np.asarray(value)
    require(array.dtype.kind in "iuf", "real numerical data without coercion required")
    require(array.size > 0 and np.isfinite(array).all(), "nonempty finite numerical data")
    return array.astype(float, copy=False)


def scalar(value):
    array = finite(value)
    require(array.shape == (), "scalar numerical value required")
    return float(array)


def json_value(value):
    """Lossless scalar normalization, never implicit complex/string coercion."""
    if isinstance(value, np.ndarray):
        return json_value(value.tolist())
    if isinstance(value, np.generic):
        converted = value.item()
        require(not isinstance(converted, np.generic), "unsupported extended NumPy scalar")
        return json_value(converted)
    if isinstance(value, dict):
        require(all(type(k) is str for k in value), "JSON string keys required")
        return {k: json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(v) for v in value]
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float and np.isfinite(value):
        return value
    raise ValueError("nonfinite or unsupported JSON value")


def close(actual, expected, label, rtol=5e-10, atol=1e-12):
    actual, expected = finite(actual), finite(expected)
    require(actual.shape == expected.shape, f"{label}: shape mismatch")
    error = float(abs(actual - expected).max())
    scale = float(abs(expected).max())
    require(error <= atol or error <= rtol * scale, f"{label}: independent mismatch")
    return error


def physical_cases():
    return [
        dict(
            label=f"{target}-n{n}",
            target=target,
            nbase=n,
            order=order,
            seed_label=f"n{n}-shape-d100mm",
        )
        for target in ("reference", "selected")
        for n, order in ((6, 5), (8, 7))
    ]


def cases():
    return [
        dict(case, label=f"{case['label']}-{method}", method=method)
        for case in physical_cases()
        for method in ("N", "V")
    ]


def levels():
    return [
        dict(index=i, nphi=b, ntheta=b, ncoil=c, ninner=n, offset=offset)
        for i, (b, c, n, offset) in enumerate(
            (
                (64, 256, 32, 0),
                (128, 256, 32, 0),
                (128, 512, 32, 0),
                (128, 512, 32, 0.5),
                (64, 256, 64, 0),
                (64, 512, 64, 0),
            )
        )
    ]


def validate_level(level):
    require(
        isinstance(level, dict)
        and any(
            set(level) == set(expected)
            and all(type(level[k]) is type(v) and level[k] == v for k, v in expected.items())
            for expected in levels()
        ),
        "one of six exact typed diagnostic levels",
    )
    return level


def archived_target(archives64, ninner):
    """Reconstruct from three supplied qualified archives; never read a Wout.

    Each row is {s: .25/.5/.75, n: 64, arrays: {phi,theta,radius,height,
    bt,bp,et,ep,native,...}}. Caller separately binds the immutable references.
    """
    require(type(ninner) is int and ninner in (32, 64), "registered32/64 interior grid")
    require(
        isinstance(archives64, list) and len(archives64) == 3,
        "three qualified64 radial archives required",
    )
    phi, theta = np.meshgrid(
        np.pi * np.arange(64) / 64, 2 * np.pi * np.arange(64) / 64, indexing="ij"
    )
    points, fields, complete = [], [], []
    for row, radius_label in zip(archives64, (0.25, 0.5, 0.75), strict=True):
        require(
            type(row["n"]) is int and row["n"] == 64 and scalar(row["s"]) == radius_label,
            "ordered exact radial and archive grid identity",
        )
        raw = {
            key: finite(row["arrays"][key])
            for key in ("phi", "theta", "radius", "height", "bt", "bp", "et", "ep", "native")
        }
        require(
            all(raw[k].shape == (64, 64) for k in ("phi", "theta", "radius", "height", "bt", "bp"))
            and all(raw[k].shape == (64, 64, 3) for k in ("et", "ep", "native"))
            and np.all(raw["radius"] > 0),
            "qualified archive array shapes and positive R",
        )
        close(raw["phi"], phi, "VMEC toroidal coordinates", rtol=0, atol=5e-12)
        close(raw["theta"], theta, "VMEC poloidal coordinates", rtol=0, atol=5e-12)
        magnetic = raw["bt"][..., None] * raw["et"] + raw["bp"][..., None] * raw["ep"]
        close(raw["native"], magnetic, "archived Cartesian target")
        xyz = np.stack(
            (raw["radius"] * np.cos(raw["phi"]), raw["radius"] * np.sin(raw["phi"]), raw["height"]),
            axis=-1,
        )
        stride = 64 // ninner
        points.append(xyz[::stride, ::stride].reshape(-1, 3))
        fields.append(magnetic[::stride, ::stride].reshape(-1, 3))
        complete.append(magnetic.reshape(-1, 3))
    b2 = float(np.mean(np.sum(np.concatenate(complete) ** 2, axis=1)))
    require(np.isfinite(b2) and b2 > 0, "positive fixed64 target B2 required")
    return dict(
        inner_points=np.concatenate(points),
        inner_target=np.concatenate(fields),
        B2_scale=b2,
        ninner=ninner,
        radii=[0.25, 0.5, 0.75],
        source_resolution=64,
    )


def validate_snapshot(snapshot):
    # The older helper's finite conversion predates strict dtype admission.
    finite(snapshot["base_coefficients"])
    for key in ("scale", "unit_flux", "target_flux", "B2_scale"):
        scalar(snapshot[key])
    for row in snapshot["physical"]:
        finite(row["matrix"])
        scalar(row["current"])
    frozen.validate_snapshot(snapshot)


def boundary_input(data):
    require(isinstance(data, dict), "explicit boundary dictionary; no implicit file reads")
    require(type(data.get("nfp")) is int and data["nfp"] == 2, "registered nfp2 target")
    for key in ("rbc", "zbs"):
        for row in data[key]:
            scalar(row["value"])
    frozen._boundary_input(data)
    return data


def seed_identity(snapshot, geometry, target_sources):
    """Exact seed/source mapping, not an assertion that an external audit passed."""
    validate_snapshot(snapshot)
    clear_geometry.validate_snapshot(geometry)
    expected_case = next(
        case
        for case in clear_geometry.cases()
        if case["label"] == f"n{geometry['nbase']}-shape-d100mm"
    )
    require(
        geometry["case"] == expected_case
        and all(type(geometry["case"][k]) is type(v) for k, v in expected_case.items()),
        "only the preselected shaped100mm seed is registered",
    )
    require(snapshot["seed_geometry"] == geometry, "original geometry-only seed document")
    require(
        snapshot["sources"] == target_sources and target_sources in geometry["sources"].values(),
        "field target must belong to both-target seed construction",
    )
    for key in ("nfp", "nbase", "order", "names", "base_coefficients"):
        require(snapshot[key] == geometry[key], f"exact seed {key}")
    require(
        [{k: v for k, v in row.items() if k != "current"} for row in snapshot["physical"]]
        == geometry["physical"],
        "physical copies preserved without invented seed currents",
    )
    return True


def distance_penalty(left, right, left_weight, right_weight, threshold, tree=None):
    """Independent pointwise complete ball sum and global sampled minimum.

    No dense pair matrix and no finite neighbour cap. Only the broadphase is
    outward padded; the actual hinge has the unmodified physical threshold.
    """
    left, right, left_weight, right_weight = map(finite, (left, right, left_weight, right_weight))
    d0 = scalar(threshold)
    require(
        left.ndim == right.ndim == 2
        and left.shape[1] == right.shape[1] == 3
        and left_weight.shape == (len(left),)
        and right_weight.shape == (len(right),)
        and np.all(left_weight > 0)
        and np.all(right_weight > 0)
        and d0 > 0,
        "nonempty positions and positive speed/area weights",
    )
    tree = cKDTree(right) if tree is None else tree
    require(np.array_equal(tree.data, right), "tree must bind exactly the right cloud")
    nearest = finite(tree.query(left, workers=1)[0])
    minimum = float(nearest.min())
    require(minimum > 0, "coincident curve/curve or curve/surface quadrature nodes")
    pad = float(128 * np.finfo(float).eps * max(1, abs(left).max(), abs(right).max(), d0))
    contributions = []
    for position, weight in zip(left, left_weight, strict=True):
        neighbors = sorted(tree.query_ball_point(position, d0 + pad, eps=0, workers=1))
        if neighbors:
            radius = np.linalg.norm(right[neighbors] - position, axis=1)
            require(np.isfinite(radius).all() and np.all(radius > 0), "positive pair radii")
            contributions.append(
                float(weight * np.sum(right_weight[neighbors] * np.maximum(d0 - radius, 0) ** 2))
            )
    return dict(
        value=float(sum(contributions) / (len(left) * len(right))),
        minimum=minimum,
        broadphase_pad=pad,
    )


def geometry_penalties(snapshot, input_data, ncoil=256):
    require(type(ncoil) is int and ncoil in (256, 512), "registered coil quadrature required")
    validate_snapshot(snapshot)
    boundary_input(input_data)
    curves = frozen.physical_curves(snapshot, ncoil)
    positions, tangents, second = [finite(curves[k]) for k in ("positions", "tangents", "second")]
    speed = np.linalg.norm(tangents, axis=-1)
    require(np.all(speed > 0), "regular filament speed required")
    curvature = np.linalg.norm(np.cross(tangents, second), axis=-1) / speed**3
    nbase = snapshot["nbase"]
    lengths = speed[:nbase].mean(axis=1)
    length = float(0.5 * np.sum(np.maximum(lengths - 3.5, 0) ** 2))
    bending = float(
        0.5 * np.sum(np.mean(np.maximum(curvature[:nbase] - 10, 0) ** 2 * speed[:nbase], axis=1))
    )
    trees = [cKDTree(p) for p in positions]
    cc = [
        distance_penalty(positions[i], positions[j], speed[i], speed[j], 0.06, trees[j])
        for i in range(len(positions))
        for j in range(i + 1, len(positions))
    ]
    surface = frozen.boundary(input_data, 128, 128, full_torus=True)
    plasma = surface["points"].reshape(-1, 3)
    area = np.linalg.norm(surface["normal"], axis=-1).ravel()
    tree = cKDTree(plasma)
    cp = [
        distance_penalty(p, plasma, v, area, 0.08, tree)
        for p, v in zip(positions, speed, strict=True)
    ]
    cc_value, cp_value = [float(sum(row["value"] for row in group)) for group in (cc, cp)]
    return json_value(
        dict(
            length=length,
            curvature=bending,
            cc=cc_value,
            cs=cp_value,
            total=float(length + 1e-4 * bending + 1000 * (cc_value + cp_value)),
            lengths=lengths,
            kappa_max=curvature[:nbase].max(axis=1),
            coil_distance=min(row["minimum"] for row in cc),
            surface_distance=min(row["minimum"] for row in cp),
            ncoil=ncoil,
            geometry_nphi=128,
            geometry_ntheta=128,
            full_torus=True,
        )
    )


def composed_metrics(snapshot, input_data, arrays, target, method, level=None):
    """Reconstruct complete discrete J/metrics from supplied immutable raw data.

    Does not replace direct Biot-Savart checks or flux/refinement acceptance.
    The original construction snapshot also supplies frozen diagnostic currents.
    """
    validate_snapshot(snapshot)
    boundary_input(input_data)
    require(method in ("N", "V"), "registered N/V method")
    level = levels()[0] if level is None else level
    validate_level(level)
    require(
        snapshot["B2_scale"] == target["B2_scale"] and target["ninner"] == level["ninner"],
        "fixed archived64 normalization and matching interior resolution",
    )
    raw = {key: finite(value) for key, value in arrays.items()}
    surface = frozen.boundary(
        input_data, level["nphi"], level["ntheta"], shift=level["offset"] == 0.5
    )
    for key, expected in (
        ("boundary_points", surface["points"].reshape(-1, 3)),
        ("boundary_normals", surface["unitnormal"].reshape(-1, 3)),
        ("boundary_weights", surface["weights"].ravel()),
        ("inner_points", target["inner_points"]),
        ("inner_target", target["inner_target"]),
    ):
        close(raw[key], expected, key, rtol=0, atol=5e-12)
    loop_points, loop_tangents = frozen.loop(input_data, 256)
    for key, expected in (("loop_points", loop_points), ("loop_tangents", loop_tangents)):
        close(raw[key], expected, key, rtol=0, atol=5e-12)
    curves = frozen.physical_curves(snapshot, level["ncoil"])
    for key, expected in (
        ("coil_positions", curves["positions"]),
        ("coil_tangents", curves["tangents"]),
        ("coil_currents", curves["currents"]),
    ):
        close(raw[key], expected, key, rtol=5e-10, atol=1e-12)
    require(raw["loop_A"].shape == loop_tangents.shape, "complete loop potential")
    field = frozen.metrics(
        raw["boundary_B"], raw["boundary_normals"], raw["boundary_weights"], target["B2_scale"]
    )
    field.update(frozen.inner_metrics(raw["inner_B"], target["inner_target"], target["B2_scale"]))
    geometry = geometry_penalties(snapshot, input_data, level["ncoil"])
    scale = scalar(snapshot["scale"])
    flux = float(np.mean(np.sum(raw["loop_A"] * loop_tangents, axis=1)))
    field.update(
        scale=scale,
        B2_scale=target["B2_scale"],
        target_flux=snapshot["target_flux"],
        flux=flux,
        unit_flux=float(flux / scale),
        current=float(1e5 * scale),
        boundary_B_rms=float(
            np.sqrt(np.sum(raw["boundary_weights"] * np.sum(raw["boundary_B"] ** 2, axis=1)))
        ),
        geometry_penalty=geometry["total"],
        geometry=geometry,
        J=float(field["JN"] + (0.05 * field["JV"] if method == "V" else 0) + geometry["total"]),
    )
    for key in ("lengths", "kappa_max", "coil_distance", "surface_distance"):
        field[key] = geometry[key]
    return json_value(field)


def directions(size):
    require(type(size) is int and size > 0, "positive canonical dimension")
    k = np.arange(1, size + 1, dtype=float)
    return [v / np.linalg.norm(v) for v in (np.sin(k), np.cos(k))]


def qualification_points(seed):
    seed = finite(seed)
    require(seed.ndim == 1, "one-dimensional canonical seed")
    return (
        [seed.copy()]
        + [
            seed + sign * step * d
            for d in directions(len(seed))
            for step in (1e-5, 5e-6)
            for sign in (1, -1)
        ]
        + [seed.copy()]
    )


def derivative_checks(rows, seed, own_values):
    expected = qualification_points(seed)
    require(
        len(rows) == 10
        and all(
            r.get("status") == "completed" and np.array_equal(finite(r["x"]), x)
            for r, x in zip(rows, expected, strict=True)
        ),
        "all ten ordered complete seed/probe/repeat bundles",
    )
    values = finite([r["J"] for r in rows])
    gradients = finite([r["gradient"] for r in rows])
    own = finite(own_values)
    require(
        values.shape == own.shape == (10,) and gradients.shape == (10, len(seed)),
        "complete scalar objectives and full gradients",
    )
    close(values, own, "all independently composed objectives")
    checks = []
    for k, direction in enumerate(directions(len(seed))):
        analytic = float(gradients[0] @ direction)
        for j, step in enumerate((1e-5, 5e-6)):
            index = 1 + 4 * k + 2 * j
            for label, data in (("recorded", values), ("independent", own)):
                fd = float((data[index] - data[index + 1]) / (2 * step))
                error = abs(fd - analytic)
                relative = error / max(abs(fd), abs(analytic), 1e-30)
                checks.append(
                    dict(
                        direction=k,
                        step=step,
                        objective=label,
                        analytic=analytic,
                        finite_difference=fd,
                        absolute_error=error,
                        relative_error=relative,
                        passed=bool(error <= 1e-8 or relative <= 2e-4),
                    )
                )
    repeat = bool(
        values[0] == values[-1]
        and own[0] == own[-1]
        and np.array_equal(gradients[0], gradients[-1])
    )
    return json_value(
        dict(
            checks=checks,
            exact_repeat=repeat,
            passed=bool(repeat and all(row["passed"] for row in checks)),
        )
    )


def physical_identity(normal, vector):
    """Exact N/V seed equivalence; their J and full gradient may differ."""
    required = {
        "boundary_points",
        "boundary_normals",
        "boundary_weights",
        "boundary_B",
        "boundary_A",
        "inner_points",
        "inner_target",
        "inner_B",
        "inner_A",
        "loop_points",
        "loop_tangents",
        "loop_A",
        "loop_B",
        "coil_positions",
        "coil_tangents",
        "coil_currents",
    }
    snapshots = []
    for row, method in ((normal, "N"), (vector, "V")):
        require(
            row["status"] == "completed" and row["snapshot"]["method"] == method,
            "ordered completed N/V seed states",
        )
        validate_snapshot(row["snapshot"])
        snap = copy.deepcopy(row["snapshot"])
        snap.pop("method")
        snapshots.append(snap)
        require(required <= set(row["arrays"]), "all physical raw arrays required for N/V identity")
        for value in row["arrays"].values():
            finite(value)
    require(
        snapshots[0] == snapshots[1], "same complete physical snapshot, source and normalization"
    )
    require(
        set(normal["arrays"]) == set(vector["arrays"])
        and all(
            np.array_equal(normal["arrays"][key], vector["arrays"][key]) for key in normal["arrays"]
        ),
        "exact N/V physical arrays",
    )
    metric_keys = {
        "JN",
        "JV",
        "scale",
        "B2_scale",
        "unit_flux",
        "target_flux",
        "flux",
        "current",
        "normal_rms",
        "normal_max",
        "vector_rms",
        "boundary_B_rms",
        "lengths",
        "kappa_max",
        "coil_distance",
        "surface_distance",
        "geometry_penalty",
        "frozen_scale",
    }
    for row in (normal, vector):
        require(
            metric_keys <= set(row["metrics"]) and row["metrics"]["frozen_scale"] is False,
            "complete actual seed metrics, without diagnostic renormalization",
        )
        for key in metric_keys - {"frozen_scale"}:
            finite(row["metrics"][key])
    a, b = [{k: v for k, v in row["metrics"].items() if k != "J"} for row in (normal, vector)]
    require(json_value(a) == json_value(b), "exact N/V physical metrics excluding objective")
    return dict(
        passed=True,
        compared_arrays=sorted(required),
        search_allowed=False,
        transfer_pass=False,
        step4_pass=False,
    )


def refinement_checks(rows):
    require(len(rows) == 6, "all six fixed diagnostic states")
    for row, level in zip(rows, levels(), strict=True):
        validate_level(row["level"])
        require(
            row["status"] == "completed" and row["level"] == level, "ordered fixed diagnostic grids"
        )
        for key in ("normal_rms", "vector_rms"):
            require(scalar(row["metrics"][key]) >= 0, "nonnegative finite diagnostic metric")
    checks = []
    for key, first, second in (
        ("normal_rms", 0, 1),
        ("normal_rms", 1, 2),
        ("normal_rms", 2, 3),
        ("vector_rms", 0, 4),
        ("vector_rms", 4, 5),
    ):
        coarse, fine = [scalar(rows[i]["metrics"][key]) for i in (first, second)]
        checks.append(
            dict(
                metric=key,
                coarse_level=first,
                fine_level=second,
                coarse=coarse,
                fine=fine,
                absolute_error=abs(fine - coarse),
                passed=frozen.refinement_pass(coarse, fine),
            )
        )
    result = json_value(
        dict(
            checks=checks,
            passed=all(row["passed"] for row in checks),
            search_allowed=False,
            transfer_pass=False,
            step4_pass=False,
        )
    )
    json.dumps(result, allow_nan=False)
    return result
