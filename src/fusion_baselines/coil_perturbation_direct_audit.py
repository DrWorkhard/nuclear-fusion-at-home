"""Independent field-free plans, Fourier samples and enclosure checks."""

import math

import numpy as np
from scipy.spatial import cKDTree

from fusion_baselines import clear_coil_geometry_audit as geometry
from fusion_baselines.coil_perturbation_audit import close, real, require

TARGETS = ("reference", "selected")


def levels():
    return [
        dict(ncoil=n, offset=offset) for n, offset in ((256, 0), (512, 0), (1024, 0), (1024, 0.5))
    ]


def plan():
    rows = [
        dict(index=0, state_id="state-00", kind="seed", direction_index=None, radius=0.0, sign=0)
    ]
    for direction in range(3):
        for radius in (1e-5, 1e-4, 1e-3, 0.03):
            for sign in (1, -1):
                index = len(rows)
                rows.append(
                    dict(
                        index=index,
                        state_id=f"state-{index:02d}",
                        kind="probe",
                        direction_index=direction,
                        radius=radius,
                        sign=sign,
                    )
                )
    rows.append(
        dict(
            index=25,
            state_id="state-25",
            kind="seed-repeat",
            direction_index=None,
            radius=0.0,
            sign=0,
        )
    )
    return rows


def directions(snapshot):
    geometry.validate_snapshot(snapshot)
    n, order = snapshot["nbase"], snapshot["order"]
    shape = (n, 3, 2 * order + 1)
    frequency = np.tile(np.r_[0, np.repeat(np.arange(1, order + 1), 2)], n * 3)
    index = np.arange(np.prod(shape)) + 1
    rows = [(trig(index) / (1 + frequency**2) ** 2).reshape(shape) for trig in (np.sin, np.cos)]
    high = np.zeros(shape)
    high[0, 2, 2 * order - 1] = 1.0
    rows.append(high)
    normalized = []
    for row in rows:
        amplitude = np.hypot(row[:, :, 1::2], row[:, :, 2::2])
        movement = np.linalg.norm(abs(row[:, :, 0]) + amplitude.sum(axis=-1), axis=1)
        scale = float(movement.max())
        require(scale > 0 and np.isfinite(scale), "nonzero deterministic direction")
        normalized.append(row / scale)
    return normalized


def candidate(snapshot, row, normalized=None):
    require(
        type(row) is dict
        and any(
            set(row) == set(expected)
            and all(type(row[k]) is type(v) and row[k] == v for k, v in expected.items())
            for expected in plan()
        ),
        "registered typed ordered probe descriptor",
    )
    seed = real(snapshot["base_coefficients"], "fixed original seed")
    if row["kind"] != "probe":
        return seed.copy()
    normalized = directions(snapshot) if normalized is None else normalized
    return seed + row["sign"] * row["radius"] * normalized[row["direction_index"]]


def fourier(coefficients, parameters):
    c = real(coefficients, "Cartesian Fourier coefficients")
    t = real(parameters, "unit-period parameters")
    require(
        c.ndim == 3 and c.shape[1] == 3 and c.shape[2] % 2 == 1,
        "complete physical Fourier coefficients",
    )
    require(t.ndim == 1 and len(t) >= 4, "nonempty unit-period sample grid")
    result = []
    for derivative in range(3):
        value = np.zeros((len(c), len(t), 3))
        if derivative == 0:
            value += c[:, None, :, 0]
        for mode in range(1, (c.shape[2] - 1) // 2 + 1):
            phase = 2 * math.pi * mode * t + derivative * math.pi / 2
            value += (2 * math.pi * mode) ** derivative * (
                np.sin(phase)[None, :, None] * c[:, None, :, 2 * mode - 1]
                + np.cos(phase)[None, :, None] * c[:, None, :, 2 * mode]
            )
        result.append(value)
    return result


def physical_coefficients(snapshot, coefficients, *, ideal=False):
    c = real(coefficients, "complete base coefficients")
    require(c.shape == np.shape(snapshot["base_coefficients"]), "complete named base shape")
    rows, normals = [], []
    for mapping in snapshot["physical"]:
        b = mapping["base_index"]
        sign = (-1.0) ** mapping["period"]
        qstar = np.diag(
            [sign, -sign if mapping["flip"] else sign, -1.0 if mapping["flip"] else 1.0]
        )
        q = qstar if ideal else np.array(mapping["matrix"]).T
        rows.append(q @ c[b])
        phi = (b + 0.5) * math.pi / (2 * snapshot["nbase"])
        normals.append(qstar @ [-math.sin(phi), math.cos(phi), 0.0])
    return np.array(rows), np.array(normals)


def reconstruct(snapshot, coefficients, level):
    """Recompute all non-distance raw data from coefficients, never a certificate."""
    geometry.validate_snapshot(snapshot)
    n, offset = level["ncoil"], level["offset"]
    require(
        type(n) is int and n >= 4 and type(offset) in (int, float) and offset in (0, 0.5),
        "valid geometry sample grid",
    )
    parameters = (np.arange(n) + offset) / n
    c, normals = physical_coefficients(snapshot, coefficients)
    seed, _ = physical_coefficients(snapshot, snapshot["base_coefficients"])
    ideal, _ = physical_coefficients(snapshot, snapshot["base_coefficients"], ideal=True)
    current, original, exact = (fourier(row, parameters) for row in (c, seed, ideal))
    speed = np.linalg.norm(current[1], axis=-1)
    cross = np.cross(current[1], current[2])
    curvature = np.zeros(speed.shape)
    with np.errstate(divide="ignore", invalid="ignore", over="ignore", under="ignore"):
        np.divide(np.linalg.norm(cross, axis=-1), speed**3, out=curvature, where=speed > 0)
    mask = (speed > 0) & np.isfinite(curvature)
    curvature[~mask] = 0.0
    raw = dict(
        parameters=parameters,
        normals=normals,
        delta_norms=np.stack(
            [
                np.maximum(
                    np.linalg.norm(current[d] - original[d], axis=-1),
                    np.linalg.norm(current[d] - exact[d], axis=-1),
                )
                for d in range(3)
            ],
            axis=-1,
        ),
        speed=speed,
        seed_speed=np.linalg.norm(exact[1], axis=-1),
        seed_acceleration=np.linalg.norm(exact[2], axis=-1),
        curvature=curvature,
        curvature_available=mask,
        projection=np.einsum("pni,pi->pn", cross, normals),
        lengths=speed.mean(axis=1),
        seed_lengths=np.linalg.norm(original[1], axis=-1).mean(axis=1),
    )
    return raw, current[0]


def bounded_work(nphysical, ncoil):
    pairs = nphysical * (nphysical - 1) // 2
    return {
        key: dict(
            attempted=calls, completed=calls, points_attempted=points, points_completed=points
        )
        for key, calls, points in (
            ("fourier", 3, 3 * nphysical * ncoil),
            ("cp", 2, 2 * nphysical * ncoil),
            ("cc", pairs, pairs * ncoil),
        )
    }


def _integer_array(value, shape, label):
    a = np.asarray(value)
    require(a.dtype.kind in "iu" and a.shape == shape, f"{label}: exact integer shape")
    return a


def _enclosed_lower(values, lower, label, summary=None):
    values = real(values, label)
    tolerance = 0.0
    require(np.all(values >= lower), f"{label}: lower bound violated")
    if summary is not None:
        _record_enclosure(summary, label, values - lower, tolerance)


def _enclosed_upper(values, upper, label, summary=None):
    values = real(values, label)
    tolerance = 0.0
    require(np.all(values <= upper), f"{label}: upper bound violated")
    if summary is not None:
        _record_enclosure(summary, label, upper - values, tolerance)


def _record_enclosure(summary, label, margin, tolerance):
    record = summary.setdefault(
        label,
        dict(
            comparisons=0,
            minimum_margin=None,
            maximum_violation=0.0,
            maximum_comparison_tolerance=0.0,
        ),
    )
    minimum = float(np.min(margin))
    record["comparisons"] += int(np.size(margin))
    record["minimum_margin"] = (
        minimum if record["minimum_margin"] is None else min(minimum, record["minimum_margin"])
    )
    record["maximum_violation"] = max(record["maximum_violation"], -minimum)
    record["maximum_comparison_tolerance"] = max(
        record["maximum_comparison_tolerance"], float(tolerance)
    )


def audit_samples(snapshot, coefficients, certificate, level, recorded, surfaces):
    enclosures = {}

    def lower(values, bound, label):
        _enclosed_lower(values, bound, label, enclosures)

    def upper(values, bound, label):
        _enclosed_upper(values, bound, label, enclosures)

    expected, positions = reconstruct(snapshot, coefficients, level)
    count, n, _ = positions.shape
    pair_order = np.array([(i, j) for i in range(count) for j in range(i + 1, count)], dtype=int)
    require(
        len(certificate["curves"]) == count
        and len(certificate["pairs"]) == len(pair_order)
        and set(certificate["plasma"]) == set(TARGETS)
        and all(len(certificate["plasma"][t]) == count for t in TARGETS),
        "complete independent mathematical certificate",
    )
    required = set(expected) | {
        f"cp_{target}_{kind}" for target in TARGETS for kind in ("distances", "indices")
    }
    required |= {"pairs", "pair_distances", "pair_witnesses"}
    require(set(recorded) == required, "complete registered raw direct arrays")
    for key, actual in expected.items():
        if key == "curvature_available":
            saved = np.asarray(recorded[key])
            require(
                saved.dtype.kind == "b" and np.array_equal(saved, actual),
                "curvature availability is an exact boolean mask",
            )
        else:
            close(recorded[key], actual, f"direct {key}")
    require(set(surfaces) == set(TARGETS), "both immutable target surfaces")
    for target in TARGETS:
        plasma = real(surfaces[target], "fixed fulltorus plasma points").reshape(-1, 3)
        distances, _ = cKDTree(plasma).query(positions.reshape(-1, 3), workers=1, eps=0)
        distances = distances.reshape(count, n)
        indices = _integer_array(recorded[f"cp_{target}_indices"], (count, n), "CP witnesses")
        require(np.all((indices >= 0) & (indices < len(plasma))), "CP witness index ranges")
        witnesses = np.linalg.norm(positions - plasma[indices], axis=-1)
        close(recorded[f"cp_{target}_distances"], distances, "all CP minimum distances")
        close(witnesses, distances, "all CP witness distances including tied nearest indices")
        for row in certificate["plasma"][target]:
            i = row["index"]
            lower(distances[i], row["direct_lower"], "direct CP enclosure")
            lower(distances[i], row["analytic_lower"], "analytic CP enclosure")
    require(
        np.array_equal(
            _integer_array(recorded["pairs"], pair_order.shape, "all coil pairs"), pair_order
        ),
        "ordered complete coil pairs",
    )
    witnesses = _integer_array(recorded["pair_witnesses"], pair_order.shape, "pair witnesses")
    require(np.all((witnesses >= 0) & (witnesses < n)), "coil witness index ranges")
    values = real(recorded["pair_distances"], "pair minimum distances")
    require(values.shape == (len(pair_order),), "one minimum for each physical pair")
    trees = [cKDTree(p) for p in positions]
    for k, (i, j) in enumerate(pair_order):
        minimum = float(trees[j].query(positions[i], workers=1, eps=0)[0].min())
        a, b = witnesses[k]
        witness = float(np.linalg.norm(positions[i, a] - positions[j, b]))
        close(values[k], minimum, "coil pair global sampled minimum")
        close(witness, minimum, "coil minimum witness")
        bound = certificate["pairs"][k]
        require((bound["i"], bound["j"]) == (int(i), int(j)), "certificate pair identity")
        lower(minimum, bound["direct_lower"], "direct coil enclosure")
        lower(minimum, bound["analytic_lower"], "analytic coil enclosure")
    for i, row in enumerate(certificate["curves"]):
        require(row["index"] == i, "certificate physical curve identity")
        for d in range(3):
            upper(expected["delta_norms"][i, :, d], row[f"D{d}"], f"derivative change D{d}")
        upper(expected["seed_speed"][i], row["V0"], "seed speed supremum")
        upper(expected["seed_acceleration"][i], row["A0"], "seed acceleration supremum")
        lower(expected["speed"][i], row["v_lower"], "candidate speed")
        lower(expected["projection"][i], row["S_lower"], "oriented projection")
        if row["kappa_upper"] is not None:
            require(
                expected["curvature_available"][i].all(), "bounded curvature requires regularity"
            )
            upper(expected["curvature"][i], row["kappa_upper"], "candidate curvature")
        # A trapezoidal sample is not the continuous length. Only the same-grid
        # absolute change has an immediate pointwise D1 guarantee.
        upper(
            abs(expected["lengths"][i] - expected["seed_lengths"][i]),
            row["D1"],
            "same-grid length difference",
        )
    return dict(
        passed=True,
        nphysical=count,
        ncoil=n,
        offset=level["offset"],
        cp_distances_checked=2 * count * n,
        coil_pairs_checked=len(pair_order),
        work=bounded_work(count, n),
        enclosure_comparisons=enclosures,
        comparison_tolerance=dict(
            relative=5e-12,
            absolute=1e-12,
            rule="relative OR absolute",
            applies_to="stored versus independently reconstructed raw values",
            bound_enclosure_tolerance=0.0,
            physical_gates_relaxed=False,
        ),
    )
