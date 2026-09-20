"""Field-free prescribed perturbations and bounded direct geometric observations.

The continuous certificate is not imported. All candidate/seed curves are
evaluated from their complete named coefficients. KD queries retain every point
and pair; no dense curve/plasma distance matrix or magnetic evaluator is used.
"""

import copy
import math

import numpy as np
from scipy.spatial import cKDTree

from fusion_baselines.clear_coil_geometry_audit import validate_snapshot

TARGETS = ("reference", "selected")
RADII = (1e-5, 1e-4, 1e-3, 0.03)
WORK_KINDS = ("fourier", "cp", "cc")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def real(value, shape=None):
    array = np.asarray(value)
    require(array.dtype.kind in "iuf" and np.isfinite(array).all(), "finite real arrays required")
    require(shape is None or array.shape == shape, "exact numerical shape required")
    return np.array(array, dtype=float, order="C", copy=True)


def levels():
    return [
        dict(ncoil=n, offset=shift) for n, shift in ((256, 0), (512, 0), (1024, 0), (1024, 0.5))
    ]


def state_plan():
    states = [dict(kind="seed", direction_index=None, radius=0.0, sign=0)]
    states += [
        dict(kind="probe", direction_index=i, radius=radius, sign=sign)
        for i in range(3)
        for radius in RADII
        for sign in (1, -1)
    ]
    states.append(dict(kind="seed-repeat", direction_index=None, radius=0.0, sign=0))
    return [dict(index=i, state_id=f"state-{i:02d}", **state) for i, state in enumerate(states)]


def directions(snapshot):
    validate_snapshot(snapshot)
    shape = (snapshot["nbase"], 3, 2 * snapshot["order"] + 1)
    modes = np.tile(np.r_[0, np.repeat(np.arange(1, snapshot["order"] + 1), 2)], (shape[0], 3, 1))
    k = np.arange(np.prod(shape)).reshape(shape) + 1
    vectors = [f(k) / (1 + modes**2) ** 2 for f in (np.sin, np.cos)]
    high = np.zeros(shape)
    high[0, 2, 2 * snapshot["order"] - 1] = 1
    vectors.append(high)
    result = []
    for vector in vectors:
        amplitudes = np.hypot(vector[..., 1::2], vector[..., 2::2])
        value = np.linalg.norm(abs(vector[..., 0]) + amplitudes.sum(axis=-1), axis=1).max()
        require(np.isfinite(value) and value > 0, "nonzero finite unpadded direction norm")
        result.append(np.array(vector / value, order="C", copy=True))
    return np.stack(result)


def candidate(snapshot, prescribed_directions, state):
    plan = state_plan()
    require(
        type(state.get("index")) is int
        and 0 <= state["index"] < len(plan)
        and state == plan[state["index"]]
        and all(type(state[key]) is type(value) for key, value in plan[state["index"]].items()),
        "exact registered state descriptor required",
    )
    shape = (snapshot["nbase"], 3, 2 * snapshot["order"] + 1)
    seed = real(snapshot["base_coefficients"], shape)
    vectors = real(prescribed_directions, (3, *shape))
    if state["direction_index"] is None:
        return seed
    return seed + state["sign"] * state["radius"] * vectors[state["direction_index"]]


def surface_points(data, nphi=256, ntheta=256):
    require(
        type(data.get("nfp")) is int and data["nfp"] == 2 and data.get("lasym", False) is False,
        "symmetric original nfp2 surface required",
    )
    require(all(type(n) is int and n >= 4 for n in (nphi, ntheta)), "resolved angular grids")
    phi, theta = np.meshgrid(
        2 * np.pi * np.arange(nphi) / nphi, 2 * np.pi * np.arange(ntheta) / ntheta, indexing="ij"
    )
    coordinates = []
    for key, function in (("rbc", np.cos), ("zbs", np.sin)):
        require(isinstance(data.get(key), list) and data[key], "complete Fourier surface modes")
        value, seen = np.zeros_like(phi), set()
        for row in data[key]:
            require(
                set(row) == {"m", "n", "value"}
                and type(row["m"]) is type(row["n"]) is int
                and row["m"] >= 0
                and (row["m"], row["n"]) not in seen,
                "unique named real surface modes required",
            )
            coefficient = real(row["value"], ())
            seen.add((row["m"], row["n"]))
            value += coefficient * function(row["m"] * theta - row["n"] * data["nfp"] * phi)
        coordinates.append(value)
    radius, height = coordinates
    require(np.isfinite(coordinates).all() and np.all(radius > 0), "finite positive-R surface")
    return np.stack((radius * np.cos(phi), radius * np.sin(phi), height), axis=-1).reshape(-1, 3)


def fourier(coefficients, parameters):
    c, t = real(coefficients), real(parameters)
    require(
        c.ndim == 3 and c.shape[1] == 3 and c.shape[2] % 2 == 1 and t.ndim == 1 and len(t) > 0,
        "complete physical Fourier arrays and nodes",
    )
    order = (c.shape[2] - 1) // 2
    omega = 2 * np.pi * np.arange(1, order + 1)
    angle = omega[:, None] * t[None, :]
    sine, cosine = np.sin(angle), np.cos(angle)
    a, b = c[:, :, 1::2], c[:, :, 2::2]
    position = (
        c[:, None, :, 0] + np.einsum("pcm,mn->pnc", a, sine) + np.einsum("pcm,mn->pnc", b, cosine)
    )
    tangent = np.einsum("pcm,mn->pnc", a * omega, cosine) - np.einsum(
        "pcm,mn->pnc", b * omega, sine
    )
    second = -np.einsum("pcm,mn->pnc", a * omega**2, sine) - np.einsum(
        "pcm,mn->pnc", b * omega**2, cosine
    )
    require(np.isfinite([position, tangent, second]).all(), "finite direct Fourier samples")
    return position, tangent, second


def empty_work():
    return {
        kind: dict(attempted=0, completed=0, points_attempted=0, points_completed=0)
        for kind in WORK_KINDS
    }


def grid_budget(nphysical, ncoil):
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


class Sampler:
    """Private copied seed/targets, exact per-grid work caps and observed counts."""

    def __init__(self, snapshot, targets, check=None):
        validate_snapshot(snapshot)
        require(set(targets) == set(TARGETS), "both fixed target point sets required")
        self._snapshot = copy.deepcopy(snapshot)
        n, m = snapshot["nbase"], snapshot["order"]
        self._shape = (n, 3, 2 * m + 1)
        base = real(snapshot["base_coefficients"], self._shape)
        physical, ideal, normals = [], [], []
        self._matrices = []
        for row in snapshot["physical"]:
            matrix = real(row["matrix"], (3, 3)).T
            signs = np.array([-1.0, -1.0, 1.0]) if row["period"] else np.ones(3)
            if row["flip"]:
                signs *= [1.0, -1.0, -1.0]
            exact = np.diag(signs)
            i = row["base_index"]
            phi = (i + 0.5) * np.pi / (2 * n)
            self._matrices.append((i, matrix))
            physical.append(matrix @ base[i])
            ideal.append(exact @ base[i])
            normals.append(exact @ np.array([-math.sin(phi), math.cos(phi), 0.0]))
        self._seed, self._ideal, self._normals = map(np.asarray, (physical, ideal, normals))
        self._targets = {}
        for target, values in targets.items():
            points = real(values)
            require(
                points.ndim == 2 and points.shape[1] == 3 and len(points), "Cartesian target points"
            )
            points.setflags(write=False)
            self._targets[target] = points
        self._trees = {key: cKDTree(value, copy_data=True) for key, value in self._targets.items()}
        self._check = check or (lambda: None)
        self._work = empty_work()
        self._start = self._budget = None

    def work(self):
        return copy.deepcopy(self._work)

    def _call(self, kind, point_count, operation):
        self._check()
        work, start, budget = self._work[kind], self._start[kind], self._budget[kind]
        if (
            work["attempted"] - start["attempted"] >= budget["attempted"]
            or work["points_attempted"] - start["points_attempted"] + point_count
            > budget["points_attempted"]
        ):
            raise RuntimeError("registered direct sampling work budget exhausted before dispatch")
        work["attempted"] += 1
        work["points_attempted"] += point_count
        result = operation()
        work["completed"] += 1
        work["points_completed"] += point_count
        return result

    def sample(self, coefficients, level):
        require(
            level in levels()
            and type(level.get("ncoil")) is int
            and type(level.get("offset")) in (int, float),
            "registered direct curve level",
        )
        c = real(coefficients, self._shape)
        t = (np.arange(level["ncoil"]) + level["offset"]) / level["ncoil"]
        count, ncoil = len(self._seed), len(t)
        self._start, self._budget = self.work(), grid_budget(count, ncoil)
        actual = np.stack([matrix @ c[i] for i, matrix in self._matrices])
        try:
            current = self._call("fourier", count * ncoil, lambda: fourier(actual, t))
            seed = self._call("fourier", count * ncoil, lambda: fourier(self._seed, t))
            ideal = self._call("fourier", count * ncoil, lambda: fourier(self._ideal, t))
            delta = np.stack(
                [
                    np.maximum(np.linalg.norm(a - b, axis=-1), np.linalg.norm(a - d, axis=-1))
                    for a, b, d in zip(current, seed, ideal, strict=True)
                ],
                axis=-1,
            )
            p, tangent, second = current
            speed = np.linalg.norm(tangent, axis=-1)
            cross = np.cross(tangent, second)
            with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
                curvature = np.divide(
                    np.linalg.norm(cross, axis=-1),
                    speed**3,
                    out=np.zeros_like(speed),
                    where=speed > 0,
                )
            available = (speed > 0) & np.isfinite(curvature)
            curvature[~available] = 0.0
            raw = dict(
                parameters=t,
                normals=self._normals.copy(),
                delta_norms=delta,
                speed=speed,
                seed_speed=np.linalg.norm(ideal[1], axis=-1),
                seed_acceleration=np.linalg.norm(ideal[2], axis=-1),
                curvature=curvature,
                curvature_available=available,
                projection=np.einsum("pnc,pc->pn", cross, self._normals),
                lengths=speed.mean(axis=1),
                seed_lengths=np.linalg.norm(seed[1], axis=-1).mean(axis=1),
            )
            for target in TARGETS:
                distances, indices = self._call(
                    "cp",
                    count * ncoil,
                    lambda target=target: self._trees[target].query(
                        p.reshape(-1, 3), k=1, eps=0, workers=1
                    ),
                )
                raw[f"cp_{target}_distances"] = distances.reshape(count, ncoil)
                raw[f"cp_{target}_indices"] = indices.reshape(count, ncoil)
            trees = [cKDTree(row, copy_data=True) for row in p]
            pairs, minima, witnesses = [], [], []
            for i in range(count):
                for j in range(i + 1, count):
                    distances, indices = self._call(
                        "cc",
                        ncoil,
                        lambda i=i, j=j: trees[j].query(p[i], k=1, eps=0, workers=1),
                    )
                    first = int(np.argmin(distances))
                    pairs.append((i, j))
                    minima.append(float(distances[first]))
                    witnesses.append((first, int(indices[first])))
            raw.update(
                pairs=np.asarray(pairs, dtype=np.int64),
                pair_distances=np.asarray(minima),
                pair_witnesses=np.asarray(witnesses, dtype=np.int64),
            )
            require(
                all(np.isfinite(value).all() for value in raw.values()),
                "finite saved direct observations",
            )
            return raw
        finally:
            self._start = self._budget = None
