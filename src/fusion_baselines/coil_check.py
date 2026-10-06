"""Frozen reference401/selected401 targets and shared checks, separate from fitting."""

import hashlib
import json
import re
from pathlib import Path

import numpy as np

from fusion_baselines import coupled_coil_audit as independent
from fusion_baselines.clear_coil_field_audit import archived_target
from fusion_baselines.coil_fit import Recorder as RunRecorder
from fusion_public.data import load_case, validate_candidate

ROOT = Path(__file__).resolve().parents[2]
TARGET = "evidence/plasma-design-v2/reference-input-401.json"
INDEX = "evidence/plasma-balanced-v1/validation.json"
WOUT = "artifacts/plasma-design-v2/reference-fine/wout.nc"

FIXED = {
    TARGET: "57394ef682f3c6399faa03012abc02da2eb1ce40703a4f99640ece3d07e5691f",
    INDEX: "84eff962b74ca5124147e12b4e30927a29b44f31c849333b0ae17c79a382d50c",
    WOUT: "83dc45b911a1e8290c3e97c7e28d4de28fcff6021b93d55df2f91d6dd3751c5e",
}
LEVELS = ((32, 256), (64, 256), (64, 512))
B2, TARGET_FLUX = 1.6293829620247962, -0.03141592653589793
MAX_BYTES = 128*1024**2
TARGETS = {
    "reference401": dict(input=TARGET, input_sha256=FIXED[TARGET],
                         wout_sha256=FIXED[WOUT], B2=B2, flux=TARGET_FLUX),
    "selected401": dict(
        input="evidence/plasma-balanced-v1/selected-input-401.json",
        input_sha256="6bec3483eaced499bafe7ee94b16aa960d219ec1fec86cc0690012f8ebdb033e",
        wout_sha256="8cd6bebfc29963f80645acf25e1a3db194e4db381365b17a89b9844554f51b52",
        B2=1.6313464444829588, flux=TARGET_FLUX),
}


def target_spec(target_id):
    need(target_id in TARGETS, "registered target required")
    return TARGETS[target_id]



def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_json(path):
    need(Path(path).stat().st_size <= MAX_BYTES, "bounded metadata required")
    return json.loads(Path(path).read_text(encoding="utf-8"))


def bind(path, expected, sources):
    path = Path(path).resolve()
    need(
        isinstance(expected, str) and re.fullmatch("[0-9a-f]{64}", expected),
        "explicit lowercase SHA256 required",
    )
    need(digest(path) == expected, f"source identity changed: {path}")
    need(str(path) not in sources or sources[str(path)] == expected, "conflicting source identity")
    sources[str(path)] = expected
    return path


def snapshot_identity(snapshot, target_id="reference401"):
    independent.validate_snapshot(snapshot)
    spec = target_spec(target_id)
    need(snapshot.get("target_id", "reference401") == target_id, "snapshot target mismatch")
    need(
        snapshot["nbase"] == 6 and snapshot["order"] in (5, 8)
        and snapshot["B2_scale"] == spec["B2"]
        and snapshot["target_flux"] == spec["flux"],
        "fixed target normalization and six order-five/eight coils required",
    )
    need(np.isfinite(snapshot["seed_unit_flux"]) and snapshot["seed_unit_flux"] != 0,
         "finite seed flux orientation required")


def candidate_snapshot(candidate, data, nodes=256, target_id="reference401"):
    """Native snapshot of a public six-coil candidate, normalized to the target flux.

    The unit flux uses the fitter's own loop and 1e5 A base current, so a converted
    candidate enters fitting and checks exactly like a native seed.
    """
    validate_candidate(candidate)
    spec = target_spec(target_id)
    need(data == read_json(bind(ROOT/spec["input"], spec["input_sha256"], {})),
         "candidate conversion requires the exact target input")

    from simsopt.field import BiotSavart, Current, coils_via_symmetries
    from simsopt.geo import CurveXYZFourier

    from fusion_baselines.coil_fit import loop_geometry

    names = independent.parameter_names(6, 5)
    curves = []
    for coefficients in candidate["base_coefficients"]:
        curve = CurveXYZFourier(nodes, 5)
        curve.local_full_x = np.asarray(coefficients, dtype=float).ravel()
        curves.append(curve)
    field = BiotSavart(coils_via_symmetries(curves, [Current(1e5) for _ in curves], 2, True))
    points, tangents = loop_geometry(data, nodes)
    field.set_points(points)
    unit_flux = float(np.mean(np.sum(field.A()*tangents, axis=1)))
    need(np.isfinite(unit_flux) and abs(unit_flux) > 1e-12, "nonzero unit-current flux required")
    scale = spec["flux"]/unit_flux
    physical = []
    for period in range(2):
        c, s = np.cos(np.pi*period), np.sin(np.pi*period)
        rotation = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
        for flip in (False, True):
            matrix = rotation.T @ (np.diag([1.0, -1.0, -1.0]) if flip else np.eye(3))
            physical.extend(dict(base_index=i, period=period, flip=flip, matrix=matrix.tolist(),
                                 current=1e5*scale*(-1 if flip else 1)) for i in range(6))
    snapshot = dict(schema_version=1, nfp=2, nbase=6, order=5, names=names,
                    base_coefficients=np.asarray(candidate["base_coefficients"]).tolist(),
                    physical=physical, scale=scale, B2_scale=spec["B2"], unit_flux=unit_flux,
                    target_id=target_id, target_flux=spec["flux"], seed_unit_flux=unit_flux,
                    construction=dict(source="public candidate", nloop=nodes, ncoil=nodes))
    snapshot_identity(snapshot, target_id)
    return snapshot


def portable_intake(wout, guard=lambda: None, target_id="reference401"):
    """Reconstructed target accepted as consistent with reference401, not dense identity."""
    from fusion_baselines import wout_target

    sources = {}
    spec = target_spec(target_id)
    bind(ROOT/spec["input"], spec["input_sha256"], sources)
    data = read_json(ROOT/spec["input"])
    need(data["phiedge"] == -spec["flux"], "exact source-bound target flux required")
    # The improved target has no public sample packet: require the archived Wout
    # identity rather than silently trusting only its boundary or a new normalization.
    if target_id == "selected401":
        bind(wout, spec["wout_sha256"], sources)
    guard()
    archives, sha256 = wout_target.archives(wout, data)
    sources[str(Path(wout).resolve())] = sha256
    guard()
    targets = {n: archived_target(archives, n) for n in (32, 64)}
    errors = {}
    if target_id == "reference401":
        starter, _ = load_case()
        errors = wout_target.starter_errors(targets[32], starter)
        need(max(errors.values()) <= 1e-8,
             f"Wout does not reproduce the public starter: {errors}")
    measured = {n: t["B2_scale"] for n, t in targets.items()}
    need(all(abs(b2/spec["B2"] - 1) <= 1e-9 for b2 in measured.values()),
         "target B2 differs from frozen")
    for target in targets.values():
        target["B2_scale"] = spec["B2"]  # Frozen before fitting, not measured from candidates.
        target["target_id"] = target_id
    portable = dict(target_id=target_id,
                    check="consistency with public starter" if target_id == "reference401"
                    else "archived selected401 Wout identity and input consistency",
                    dense_identity_verified=False,
                    archived_wout_identity=sha256 == spec["wout_sha256"],
                    input_sha256=spec["input_sha256"], B2_scale=spec["B2"],
                    target_flux=spec["flux"], wout_sha256=sha256,
                    starter_errors=errors, measured_B2=measured[64])
    return data, targets, sources, portable


def intake(guard=lambda: None):
    sources = {}
    for path, expected in FIXED.items():
        guard()
        bind(ROOT / path, expected, sources)
    data = {p: read_json(ROOT / p) for p in FIXED if p.endswith(".json")}
    need(data[TARGET]["phiedge"] == -TARGET_FLUX, "exact source-bound target flux required")
    index = data[INDEX]
    states = [s for s in index["states"] if s["label"] == "reference-401"]
    need(
        index["status"] == "completed"
        and index["all_phases_completed"] is True
        and len(states) == 1
        and states[0]["errors"] == [],
        "qualified reference401 archive index",
    )
    state = states[0]
    need(
        state["wout"] == dict(path=str((ROOT / WOUT).resolve()), sha256=FIXED[WOUT]),
        "exact reference401 Wout pairing",
    )
    need(
        [(f["s"], f["n"]) for f in state["fields"]]
        == [(s, n) for s in (0.25, 0.5, 0.75) for n in (64, 128)],
        "complete qualified field grids",
    )
    archives = []
    for row in state["fields"]:
        need(
            set(row["checks"])
            == {"cartesian", "magnitude", "missing_2pi", "poloidal", "toroidal", "wrong_sign"}
            and all(v is True for v in row["checks"].values()),
            "qualified vector-target checks",
        )
        guard()
        path = bind(row["arrays"]["path"], row["arrays"]["sha256"], sources)
        if row["n"] == 64:
            with np.load(path, allow_pickle=False) as raw:
                archives.append(
                    dict(s=row["s"], n=64, arrays={k: raw[k].copy() for k in raw.files})
                )
        guard()
    targets = {n: archived_target(archives, n) for n in (32, 64)}
    need(all(t["B2_scale"] == B2 for t in targets.values()), "fixed archived64 B2 identity")
    return data[TARGET], targets, sources


def error(actual, expected):
    a, b = np.asarray(actual), np.asarray(expected)
    need(
        a.shape == b.shape and a.shape[-1:] == (3,) and a.size and np.isfinite([a, b]).all(),
        "matched finite vector arrays required",
    )
    value = float(
        np.max(np.linalg.norm(a - b, axis=-1) / np.maximum(1.0, np.linalg.norm(b, axis=-1)))
    )
    need(np.isfinite(value), "finite comparison required")
    return value


def native_coils(snapshot, nodes, target_id="reference401"):
    from simsopt.field import Current, coils_via_symmetries
    from simsopt.geo import CurveXYZFourier

    snapshot_identity(snapshot, target_id)
    own = independent.physical_curves(snapshot, nodes)
    curves, currents = [], []
    width = 3*(2*snapshot['order']+1)
    for i, coefficients in enumerate(snapshot["base_coefficients"]):
        curve = CurveXYZFourier(nodes, snapshot['order'])
        need(
            [f"coil[{i}]/{name}" for name in curve.local_full_dof_names]
            == snapshot["names"][width * i : width * (i + 1)],
            "native named coordinate identity",
        )
        curve.local_full_x = np.asarray(coefficients).ravel().copy()
        curve.fix_all()
        current = Current(1e5 * snapshot["scale"])
        current.fix_all()
        curves.append(curve)
        currents.append(current)
    coils = coils_via_symmetries(curves, currents, 2, True)
    checks = dict(
        position=error([c.curve.gamma() for c in coils], own["positions"]),
        tangent=error([c.curve.gammadash() for c in coils], own["tangents"]),
    )
    need(
        np.array_equal([c.current.get_value() for c in coils], own["currents"])
        and max(checks.values()) <= 1e-12,
        "native 24-coil geometry/current mapping",
    )
    return coils, own, checks


def field_metrics(B, target, A, tangents, snapshot, ninner, target_id="reference401"):
    snapshot_identity(snapshot, target_id)
    spec = target_spec(target_id)
    B, target, A, tangents = map(np.asarray, (B, target, A, tangents))
    need(
        type(ninner) is int
        and ninner in (32, 64)
        and B.shape == (3 * ninner * ninner, 3)
        and target.shape == B.shape
        and A.shape == tangents.shape
        and A.ndim == 2
        and A.shape[1] == 3
        and len(A) in (256, 512)
        and all(np.isfinite(x).all() for x in (B, target, A, tangents)),
        "complete finite three-surface fields and loop required",
    )
    with np.errstate(over="ignore", invalid="ignore"):
        magnitude = np.linalg.norm(B, axis=1)
        target_magnitude = np.linalg.norm(target, axis=1)
        need(np.all(target_magnitude > 0), "nonzero target field required")
        flux = float(np.mean(np.sum(A * tangents, axis=1)))
        result = dict(
            independent.inner_metrics(B, target, spec["B2"]),
            surface_vector_rms=[
                independent.inner_metrics(a, b, spec["B2"])["vector_rms"]
                for a, b in zip(B.reshape(3, -1, 3), target.reshape(3, -1, 3), strict=True)
            ],
            field_rms=float(np.sqrt(np.mean(magnitude**2))),
            mean_b=float(magnitude.mean()),
            min_b=float(magnitude.min()),
            target_field_rms=float(np.sqrt(np.mean(target_magnitude**2))),
            measured_flux=flux,
            flux_relative_error=abs(flux / spec["flux"] - 1),
            base_current=1e5 * snapshot["scale"],
            B2_scale=spec["B2"],
            frozen_scale=snapshot["scale"],
        )
        result["field_rms_over_target"] = result["field_rms"] / result["target_field_rms"]
    need(
        all(np.isfinite(v).all() for v in result.values()), "finite derived field metrics required"
    )
    result.update(
        inner_limit_met=result["vector_rms"] <= 0.01,
        flux_limit_met=result["flux_relative_error"] <= 1e-6,
        current_limit_met=abs(result["base_current"]) <= 500000,
        zero_field_sampled=bool(np.any(magnitude == 0)),
        fine_renormalization_applied=False,
    )
    return result


class Recorder(RunRecorder):
    def __init__(self, output, deadline, storage=None):
        super().__init__(output, deadline, storage)
        self.counts = {k: dict(attempted=0, completed=0) for k in ("B", "A", "independent_BA")}
        self.points = {k: dict(attempted=0, completed=0) for k in self.counts}

    def save(self, name, value):
        payload = (
            value
            if isinstance(value, bytes)
            else (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
        )
        if self.bytes + len(payload) > MAX_BYTES:
            raise OSError("128 MiB shared output ceiling including temporary publication")
        super().save(name, payload)

    def write(self, name, value):
        self.guard()
        self.save(name, value)
        self.guard()

    def request(self, name, count, function, *args):
        self.guard()
        self.points[name]["attempted"] += count
        before = self.counts[name]["completed"]
        try:
            return self.call(name, function, *args)
        finally:
            if self.counts[name]["completed"] > before:
                self.points[name]["completed"] += count


def screen_level(snapshot, data, target, ninner, nodes, record):
    from simsopt.field import BiotSavart

    target_id = target.get("target_id", "reference401")
    spec = target_spec(target_id)
    snapshot_identity(snapshot, target_id)
    need(
        (ninner, nodes) in LEVELS and target["ninner"] == ninner
        and target["B2_scale"] == spec["B2"],
        "one registered interior/coil grid required",
    )
    record.guard()
    coils, own, checks = native_coils(snapshot, nodes, target_id)
    record.guard()
    field = BiotSavart(coils)

    def sample(name, points):
        blocks = []
        for first in range(0, len(points), 128):
            record.guard()
            block = np.ascontiguousarray(points[first : first + 128])
            field.set_points(block)
            value = np.asarray(record.request(name, len(block), getattr(field, name))).copy()
            need(value.shape == block.shape and np.isfinite(value).all(), "finite native block")
            blocks.append(value)
        return np.concatenate(blocks)

    points, target_B = target["inner_points"], target["inner_target"]
    need(
        np.shape(points) == np.shape(target_B) == (3 * ninner * ninner, 3)
        and np.isfinite([points, target_B]).all(),
        "complete archived interior coordinates",
    )
    lp, tangent = independent.loop(data, nodes)
    B, A = sample("B", points), sample("A", lp)
    bi = np.linspace(0, len(points) - 1, 64, dtype=int)
    ai = np.linspace(0, nodes - 1, 64, dtype=int)
    direct_B, _ = record.request(
        "independent_BA",
        64,
        independent.filament_field_and_potential,
        points[bi],
        own["positions"],
        own["tangents"],
        own["currents"],
    )
    _, direct_A = record.request(
        "independent_BA",
        64,
        independent.filament_field_and_potential,
        lp[ai],
        own["positions"],
        own["tangents"],
        own["currents"],
    )
    checks.update(B=error(B[bi], direct_B), A=error(A[ai], direct_A))
    arrays = dict(
        inner_points=points,
        inner_target=target_B,
        inner_B=B,
        loop_points=lp,
        loop_tangent=tangent,
        loop_A=A,
        positions=own["positions"],
        tangents=own["tangents"],
        currents=own["currents"],
        B_indices=bi,
        A_indices=ai,
        independent_B=direct_B,
        independent_A=direct_A,
    )
    metrics = field_metrics(B, target_B, A, tangent, snapshot, ninner, target_id)
    record.guard()
    return dict(
        ninner=ninner,
        ncoil=nodes,
        metrics=metrics,
        checks=checks,
        checks_pass=max(checks.values()) <= 1e-12,
        physical_admission=False,
    ), arrays


def refinements(rows):
    need([(r["ninner"], r["ncoil"]) for r in rows] == list(LEVELS), "three ordered levels required")
    result = []
    for first, second, label in ((0, 1, "interior-grid"), (1, 2, "coil-quadrature")):
        a, b = (rows[i]["metrics"]["vector_rms"] for i in (first, second))
        need(
            np.isfinite([a, b]).all() and a >= 0 and b >= 0, "finite nonnegative refinement values"
        )
        change = abs(b - a)
        result.append(
            dict(
                kind=label,
                coarse=a,
                fine=b,
                absolute_change=change,
                relative_change=change / a if a > 0 else None,
            )
        )
    return result


def geometry(snapshot, data, guard):
    from fusion_baselines.clear_coil_field_audit import json_value
    from fusion_baselines.coupled_coil_audit import geometry_certificates
    from fusion_baselines.curvature_bounds import classify_enclosure, curvature_enclosure

    levels = []
    for nc, ns, nk in ((1024, 512, 1024), (2048, 1024, 4096)):
        guard()
        g = geometry_certificates(snapshot, data, nc, ns, ns)
        guard()
        curvature = [curvature_enclosure(c, nk) for c in snapshot["base_coefficients"]]
        states = [classify_enclosure(c, 12) for c in curvature]
        passed = (max(g["length_upper"]) <= 3.5 and g["coil_lower"] >= .06
                  and g["plasma_lower"] >= .08 and all(s == "pass" for s in states))
        witness = (any(s == "fail" for s in states)
                   or min(p["sampled"] for p in g["coil_pairs"]) < .06
                   or min(p["sampled"] for p in g["plasma_distances"]) < .08)
        levels.append(dict(ncoil=nc, nsurface=ns, ncurvature=nk, geometry=g,
                           curvature=curvature, status="pass" if passed else
                           "fail" if witness else "unresolved"))
        guard()
        if passed or witness:
            break
    return json_value(dict(status=levels[-1]["status"], levels=levels, interval_arithmetic=False,
                           complete_self_disjointness=False, physical_admission=False))
