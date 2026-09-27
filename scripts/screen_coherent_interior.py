"""Five frozen magnetic snapshots on archived reference401 interior grids; no search."""

import argparse
import hashlib
import importlib
import io
import json
import os
import re
import shutil
import time
from pathlib import Path

import explore_coherent_coils as paired
import numpy as np

from fusion_baselines import coupled_coil_audit as independent
from fusion_baselines.clear_coil_field_audit import archived_target
from fusion_baselines.provenance import git_state

ROOT = Path(__file__).resolve().parents[1]
TARGET = "evidence/plasma-design-v2/reference-input-401.json"
INDEX = "evidence/plasma-balanced-v1/validation.json"
WOUT = "artifacts/plasma-design-v2/reference-fine/wout.nc"
ORIGINAL = (
    "artifacts/clear-coil-field-start-v1/reference-n6/operations/qualification-N-00-snapshot.json"
)
SHAPE52 = paired.SNAPSHOT
COHERENT = "artifacts/coherent-coils-v2/run/coherent/selected-snapshot.json"
COHERENT_RESULT = "artifacts/coherent-coils-v2/run/result.json"
COHERENT_TRIAL = "artifacts/coherent-coils-v2/run/coherent/trial-598.json"
FIXED = {
    TARGET: "57394ef682f3c6399faa03012abc02da2eb1ce40703a4f99640ece3d07e5691f",
    INDEX: "84eff962b74ca5124147e12b4e30927a29b44f31c849333b0ae17c79a382d50c",
    WOUT: "83dc45b911a1e8290c3e97c7e28d4de28fcff6021b93d55df2f91d6dd3751c5e",
    ORIGINAL: "4c29c1f7afb67f290bd3c7c2ec23829e5f386e7e8c299f8d40a0e0f4e2f03830",
    SHAPE52: "2492d83ad3392069be5bfe8ae35b2e98ca0419916517e96065e017bcf15417e9",
    paired.TRIAL: "954e8b63bbb8fc2fb3b3215c8f70c88b0f576796b43fa7e57d991bd45d66e961",
    COHERENT: "e05ed6c3b497aa332c3ebfac1f1b9d5d63ec82fc6196f7bbd4ff8d238597176b",
    COHERENT_RESULT: "328ccd9727e406a72b50016aa03d93f4ac4b0e57f7f57a11686050d7c088cf2b",
    COHERENT_TRIAL: "59dee3d83fcc3dbeeca04de839adde9f8bdad0fa72311ae1169d3949209983d4",
}
LEVELS = ((32, 256), (64, 256), (64, 512))
LABELS = ("original-shape", "shape52", "coherent598", "restart-control", "restart-expanded-low")
B2, TARGET_FLUX = 1.6293829620247962, -np.pi / 100
SECONDS, MAX_BYTES = 180, 128 * 1024**2


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


def snapshot_identity(snapshot, trial=None):
    independent.validate_snapshot(snapshot)
    need(
        (snapshot["nbase"], snapshot["order"]) == (6, 5)
        and snapshot["B2_scale"] == B2
        and snapshot["target_flux"] == TARGET_FLUX,
        "fixed reference normalization and six order-five coils required",
    )
    if trial is not None:
        need(
            trial["status"] == "completed"
            and trial["role"] in ("search", "startup-seed")
            and type(trial["index"]) is int
            and trial["index"] >= 0
            and np.array_equal(np.ravel(snapshot["base_coefficients"]), trial["x"])
            and all(snapshot[k] == trial["metrics"][k] for k in ("scale", "unit_flux"))
            and trial["metrics"]["current"] == 1e5 * snapshot["scale"],
            "exact selected geometry/current/trial association required",
        )


def selected_snapshot(report, folder, arm_name, sources, *, width):
    need(
        report.get("completed") is True
        and report.get("sources_unchanged") is True
        and report["sources_before"] == report["sources_after"],
        "complete source-stable search required; no skipped failed arms",
    )
    for path, expected in report["sources_before"].items():
        bind(path, expected, sources)
    need(
        report["sources_before"].get(str((ROOT / TARGET).resolve())) == FIXED[TARGET],
        "search must target the exact reference401 input",
    )
    arms = [r for r in report["arms"] if r["arm"] == arm_name]
    need(len(arms) == 1, "one explicitly named selected arm required")
    arm = arms[0]
    need(
        arm.get("startup_pass") is True
        and not arm.get("execution_error")
        and arm["status"]["reason"] in ("budget", "solver-return")
        and len(arm["fine"]) == 2,
        "successful startup and both frozen fine rows required",
    )
    chosen = arm["fine_selected"]
    need(type(chosen["index"]) is int and chosen["index"] >= 0, "selected integer index required")
    stem = Path(folder) / arm_name
    trial_path = stem / f"trial-{chosen['index']:0{width}}.json"
    bind(trial_path, digest(trial_path), sources)
    need(read_json(trial_path) == chosen, "saved selected trial differs from result")
    snapshot_path = stem / "selected-snapshot.json"
    bind(snapshot_path, digest(snapshot_path), sources)
    snapshot = read_json(snapshot_path)
    snapshot_identity(snapshot, chosen)
    need(
        arm["active_names"] == snapshot["names"] and arm["active_count"] == 198,
        "selected named physical coordinates required",
    )
    for shift, fine in zip((0.0, 0.5), arm["fine"], strict=True):
        path = stem / f"fine-{shift}.json"
        bind(path, digest(path), sources)
        need(
            read_json(path) == fine
            and fine["shift"] == shift
            and fine["n"] == 128
            and fine["nodes"] == 512
            and fine["checks_pass"] is True
            and fine["metrics"]["frozen_scale"] == snapshot["scale"]
            and fine["metrics"]["current"] == 1e5 * snapshot["scale"],
            "both associated fixed-current fine results required",
        )
        bind(stem / f"fine-{shift}.npz", fine["arrays_sha256"], sources)
    return snapshot, dict(
        snapshot=str(snapshot_path),
        selected_index=chosen["index"],
        fine_selection=arm["fine_selection"],
        geometry_admission="not_assessed_here",
    )


def intake(restart_result, restart_sha256, guard=lambda: None):
    sources = {}
    for path, expected in FIXED.items():
        guard()
        bind(ROOT / path, expected, sources)
    data = {p: read_json(ROOT / p) for p in FIXED if p.endswith(".json")}
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
    snapshots = [data[ORIGINAL], data[SHAPE52]]
    snapshot_identity(snapshots[0])
    need(
        snapshots[0]["sources"]
        == dict(
            input=dict(path=str((ROOT / TARGET).resolve()), sha256=FIXED[TARGET]),
            wout=state["wout"],
        ),
        "original magnetic seed target pairing",
    )
    snapshot_identity(snapshots[1], data[paired.TRIAL])
    need(data[paired.TRIAL]["index"] == 52, "frozen shape52 selection")
    coherent, association = selected_snapshot(
        data[COHERENT_RESULT], (ROOT / COHERENT_RESULT).parent, "coherent", sources, width=3
    )
    need(
        coherent == data[COHERENT]
        and association["selected_index"] == 598
        and read_json(ROOT / COHERENT_TRIAL) == data[COHERENT_RESULT]["arms"][1]["fine_selected"],
        "frozen coherent598 selection",
    )
    snapshots.append(coherent)
    associations = [
        dict(snapshot=str(ROOT / ORIGINAL)),
        dict(snapshot=str(ROOT / SHAPE52)),
        association,
    ]
    restart_path = bind(restart_result, restart_sha256, sources)
    restart = read_json(restart_path)
    need(
        restart["kind"] == "matched-absolute-box-coherent-restarts"
        and restart["seed_sha256"] == FIXED[COHERENT]
        and restart["center_sha256"] == FIXED[SHAPE52]
        and [a["arm"] for a in restart["arms"]] == ["control", "expanded-low"],
        "both prospectively named session7 arms required",
    )
    for arm in ("control", "expanded-low"):
        guard()
        snapshot, association = selected_snapshot(
            restart, restart_path.parent, arm, sources, width=4
        )
        snapshots.append(snapshot)
        associations.append(association)
    guard()
    return (
        data[TARGET],
        targets,
        [
            dict(label=label, snapshot=snapshot, association=association)
            for label, snapshot, association in zip(LABELS, snapshots, associations, strict=True)
        ],
        sources,
    )


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


def native_coils(snapshot, nodes):
    from simsopt.field import Current, coils_via_symmetries
    from simsopt.geo import CurveXYZFourier

    snapshot_identity(snapshot)
    own = independent.physical_curves(snapshot, nodes)
    curves, currents = [], []
    for i, coefficients in enumerate(snapshot["base_coefficients"]):
        curve = CurveXYZFourier(nodes, 5)
        need(
            [f"coil[{i}]/{name}" for name in curve.local_full_dof_names]
            == snapshot["names"][33 * i : 33 * (i + 1)],
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


def field_metrics(B, target, A, tangents, snapshot, ninner):
    snapshot_identity(snapshot)
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
            independent.inner_metrics(B, target, B2),
            surface_vector_rms=[
                independent.inner_metrics(a, b, B2)["vector_rms"]
                for a, b in zip(B.reshape(3, -1, 3), target.reshape(3, -1, 3), strict=True)
            ],
            field_rms=float(np.sqrt(np.mean(magnitude**2))),
            mean_b=float(magnitude.mean()),
            min_b=float(magnitude.min()),
            target_field_rms=float(np.sqrt(np.mean(target_magnitude**2))),
            measured_flux=flux,
            flux_relative_error=abs(flux / TARGET_FLUX - 1),
            base_current=1e5 * snapshot["scale"],
            B2_scale=B2,
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


class Recorder(paired.Recorder):
    def __init__(self, output, deadline):
        super().__init__(output, deadline)
        self.counts = {k: dict(attempted=0, completed=0) for k in ("B", "A", "independent_BA")}
        self.points = {k: dict(attempted=0, completed=0) for k in self.counts}

    def save(self, name, value):
        payload = (
            value
            if isinstance(value, bytes)
            else (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
        )
        if self.storage[0] + len(payload) > MAX_BYTES:
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

    need(
        (ninner, nodes) in LEVELS and target["ninner"] == ninner and target["B2_scale"] == B2,
        "one registered interior/coil grid required",
    )
    record.guard()
    coils, own, checks = native_coils(snapshot, nodes)
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
    metrics = field_metrics(B, target_B, A, tangent, snapshot, ninner)
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


def fingerprints(sources):
    result = dict(sources)
    modules = (
        "simsoptpp",
        "simsopt.field.biotsavart",
        "simsopt.field.coil",
        "simsopt.field.magneticfield",
        "simsopt.geo.curve",
        "simsopt.geo.curvexyzfourier",
        "simsopt._core.optimizable",
        "simsopt._core.util",
        "simsopt._core.derivative",
        "fusion_baselines.coupled_coil_audit",
        "fusion_baselines.clear_coil_field_audit",
        "fusion_baselines.provenance",
    )
    paths = [Path(importlib.import_module(name).__file__).resolve() for name in modules]
    paths += [
        Path(__file__).resolve(),
        ROOT / "tests/test_screen_coherent_interior.py",
        Path(paired.__file__),
        Path(paired.previous.__file__),
        Path(paired.previous.common.__file__),
    ]
    for path in paths:
        current = digest(path)
        need(
            str(path) not in result or result[str(path)] == current,
            "source bytes changed during intake",
        )
        result[str(path)] = current
    return result


def run(output, restart_result, restart_sha256):
    started = time.monotonic()
    need(
        all(
            os.environ.get(k) == "1"
            for k in (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS",
                "MKL_NUM_THREADS",
            )
        ),
        "one-thread environment required",
    )
    if shutil.disk_usage(ROOT).free < 3 * 1024**3:
        raise OSError("3 GiB starting reserve required")
    record = Recorder(output, started + SECONDS)
    report = dict(
        kind="fixed-coherent-interior-screen",
        completed=False,
        states=[],
        repository=git_state(ROOT),
        physical_admission=False,
        transfer_pass=False,
        optimizer_calls=0,
        vmec_calls=0,
        levels=LEVELS,
        labels=LABELS,
        limits=dict(seconds=SECONDS, output_bytes=MAX_BYTES),
        restart_result=dict(path=str(Path(restart_result).resolve()), sha256=restart_sha256),
    )
    try:
        data, targets, states, sources = intake(restart_result, restart_sha256, record.guard)
        report["sources_before"] = fingerprints(sources)
        record.write("inputs.json", report)
        for state in states:
            label, snapshot = state["label"], state["snapshot"]
            result = dict(
                label=label,
                association=state["association"],
                rows=[],
                geometry_admission="not_assessed_here",
                physical_admission=False,
            )
            report["states"].append(result)
            record.write(label + "-snapshot.json", snapshot)
            for level, (ninner, nodes) in enumerate(LEVELS):
                stem = f"{label}-{level}"
                record.active = dict(label=label, level=level)
                record.write(stem + "-attempt.json", dict(label=label, ninner=ninner, ncoil=nodes))
                row, arrays = screen_level(snapshot, data, targets[ninner], ninner, nodes, record)
                buffer = io.BytesIO()
                np.savez_compressed(buffer, **arrays)
                record.guard()
                payload = buffer.getvalue()
                record.write(stem + ".npz", payload)
                row["arrays"] = dict(
                    path=str(output / (stem + ".npz")),
                    sha256=hashlib.sha256(payload).hexdigest(),
                    bytes=len(payload),
                )
                record.write(stem + ".json", row)
                result["rows"].append(row)
                need(row["checks_pass"], "independent field/geometry identity failed")
            result["refinements"] = refinements(result["rows"])
        report["sources_after"] = {path: digest(path) for path in report["sources_before"]}
        report["sources_unchanged"] = report["sources_after"] == report["sources_before"]
        report["completed"] = report["sources_unchanged"] and len(report["states"]) == 5
        record.guard()
    except Exception as exc:
        report.update(completed=False, error=f"{type(exc).__name__}: {exc}")
    report.update(counts=record.counts, points=record.points, elapsed_s=time.monotonic() - started)
    code = paired.publish(record, report, started)
    print(json.dumps(dict(output=str(output), completed=report["completed"])))
    return code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--restart-result", required=True, type=Path)
    parser.add_argument("--restart-result-sha256", required=True)
    args = parser.parse_args()
    raise SystemExit(
        run(args.output.resolve(), args.restart_result.resolve(), args.restart_result_sha256)
    )
