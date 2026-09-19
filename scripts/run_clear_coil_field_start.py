"""Guarded source-bound clear-coil startup producer; independent admission is separate."""

import argparse
import copy
import gc
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import qualify_sparse_coil_surface as storage

from fusion_baselines.resource_guard import GIB, guarded_run, space_check

ROOT = Path(__file__).resolve().parents[1]
THREADS = storage.THREADS
WALL_SECONDS = 1800.0
SCOPE = dict(
    equilibrium_solves=0,
    search_calls=0,
    all_pass=False,
    startup_pass=False,
    physical_seed_pass=False,
    search_allowed=False,
    transfer_pass=False,
    step4_pass=False,
    independent_audit_pass=False,
)
save, ref, checked, read = storage.save, storage.ref, storage.checked, storage.read


def sources(root):
    from clear_coil_field_start_inputs import sources as bound_sources

    return bound_sources(root)


def checked_source(reference):
    from clear_coil_field_start_inputs import checked as bound_checked

    return bound_checked(reference)


def matrix():
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


def model_plan():
    base = dict(nphi=64, ntheta=64, ncoil=256, ninner=32, offset=0)
    return (
        [
            dict(
                id=f"qualification-{method}", kind="qualification", method=method, grid=base.copy()
            )
            for method in ("N", "V")
        ]
        + [
            dict(
                id=f"diagnostic-{level['index']}",
                kind="diagnostic",
                method="N",
                grid={key: value for key, value in level.items() if key != "index"},
                level=level,
            )
            for level in levels()
        ]
        + [
            dict(id=f"flux-{ncoil}", kind="flux", method="N", grid=dict(base, ncoil=ncoil))
            for ncoil in (256, 512)
        ]
    )


def operations(spec, seed):
    if spec["kind"] == "qualification":
        return [
            dict(
                operation_id=f"{spec['id']}-{i:02d}",
                model_id=spec["id"],
                kind="qualification",
                index=i,
                label=state["label"],
                method=spec["method"],
                x=state["x"],
            )
            for i, state in enumerate(storage.states(seed)[:10])
        ]
    if spec["kind"] == "diagnostic":
        return [
            dict(
                operation_id=spec["id"],
                model_id=spec["id"],
                kind="diagnostic",
                index=spec["level"]["index"],
                level=spec["level"],
                x=np.asarray(seed),
            )
        ]
    grids = [dict(form="line", ntheta=n) for n in (256, 512, 1024)] + [
        dict(form="area", nrho=r, ntheta=n) for r in (16, 32) for n in (256, 512, 1024)
    ]
    return [
        dict(
            operation_id=f"{spec['id']}-{grid['form']}-"
            + (f"{grid['nrho']}-" if grid["form"] == "area" else "")
            + str(grid["ntheta"]),
            model_id=spec["id"],
            kind="flux",
            index=i,
            ncoil=spec["grid"]["ncoil"],
            **grid,
        )
        for i, grid in enumerate(grids)
    ]


class ParentLost(RuntimeError):
    pass


class NativeBudgetExceeded(RuntimeError):
    pass


def deadline(started, now=None):
    elapsed = (time.monotonic() if now is None else now) - started
    if not np.isfinite(elapsed) or elapsed < 0:
        raise ValueError("finite forward worker clock required")
    if elapsed >= WALL_SECONDS:
        raise TimeoutError("registered 1800 s physical-cell budget exceeded")
    return float(elapsed)


class Guard:
    def __init__(self, output, parent_pid, started):
        self.output, self.parent_pid, self.started = output, parent_pid, started
        self.minimum_free_bytes = None

    def __call__(self):
        if type(self.parent_pid) is not int or os.getppid() != self.parent_pid:
            raise ParentLost("owned parent changed; no additional field work allowed")
        deadline(self.started)
        free = space_check(self.output, 2 * GIB)["free_bytes"]
        self.minimum_free_bytes = (
            free if self.minimum_free_bytes is None else min(self.minimum_free_bytes, free)
        )


class NativeLog:
    """Complete attempted/outcome history, plus the latest durable event."""

    def __init__(self, output, guard):
        self.path, self.inflight = output / "native-events.jsonl", output / "native-inflight.json"
        with self.path.open("x"):
            pass
        self.guard, self.operation_id, self.count, self.latest = guard, None, 0, {}
        self.denials = output / "native-denials.jsonl"
        self.admitted_total, self.admitted_models, self.admitted_operations = 0, {}, {}
        self.model_caps, self.operation_caps, self.operation_calls = {}, {}, {}
        for spec in model_plan():
            self.model_caps[spec["id"]] = {"qualification": 91, "diagnostic": 7, "flux": 19}[
                spec["kind"]
            ]
            self.operation_caps[f"init:{spec['id']}"] = (spec["id"], 1)
            self.operation_calls[f"init:{spec['id']}"] = [("loop", "A", 256)]
            boundary = spec["grid"]["nphi"] * spec["grid"]["ntheta"]
            interior = 3 * spec["grid"]["ninner"] ** 2
            for operation in operations(spec, np.zeros(1)):
                self.operation_caps[operation["operation_id"]] = (
                    spec["id"],
                    {"qualification": 9, "diagnostic": 6, "flux": 2}[spec["kind"]],
                )
                if spec["kind"] == "flux":
                    points = operation["ntheta"] * operation.get("nrho", 1)
                    quantities = ("A", "B") if operation["form"] == "line" else ("B", "A")
                    sequence = [("loop", quantity, points) for quantity in quantities]
                else:
                    sequence = [
                        ("boundary", "B", boundary),
                        ("inner", "B", interior),
                        ("loop", "A", 256),
                    ]
                    if spec["kind"] == "qualification":
                        sequence += [
                            ("boundary", "B_vjp", boundary),
                            ("inner", "B_vjp", interior),
                            ("loop", "A_vjp", 256),
                        ]
                    sequence += [
                        ("boundary", "A", boundary),
                        ("inner", "A", interior),
                        ("loop", "B", 256),
                    ]
                self.operation_calls[operation["operation_id"]] = sequence

    def callback(self, model_id):
        def receive(event):
            denied = None
            if event["status"] == "attempted":
                self.guard()
                contract = self.operation_caps.get(self.operation_id)
                if (
                    model_id not in self.model_caps
                    or contract is None
                    or contract[0] != model_id
                    or self.admitted_total >= 262
                    or self.admitted_models.get(model_id, 0) >= self.model_caps[model_id]
                    or self.admitted_operations.get(self.operation_id, 0) >= contract[1]
                ):
                    denied = "registered model/operation/init/global native-call budget exceeded"
                elif (event["field"], event["quantity"], event["points"]) != self.operation_calls[
                    self.operation_id
                ][self.admitted_operations.get(self.operation_id, 0)] or type(
                    event["points"]
                ) is not int:
                    denied = "unregistered native field/quantity/point-count order"
                else:
                    self.admitted_total += 1
                    self.admitted_models[model_id] = self.admitted_models.get(model_id, 0) + 1
                    self.admitted_operations[self.operation_id] = (
                        self.admitted_operations.get(self.operation_id, 0) + 1
                    )
            wrapped = storage.builtin(
                dict(
                    append_index=self.count,
                    model_id=model_id,
                    operation_id=self.operation_id,
                    event=event,
                )
            )
            encoded = json.dumps(wrapped, sort_keys=True, allow_nan=False) + "\n"
            with self.path.open("a") as stream:
                stream.write(encoded)
                stream.flush()
            self.count += 1
            self.latest.setdefault(model_id, {})[event["index"]] = copy.deepcopy(event)
            save(self.inflight, wrapped)
            if denied is not None:
                record = dict(
                    wrapped,
                    reason=denied,
                    native_dispatch_permitted=False,
                    admitted_requests=self.admitted_total,
                )
                with self.denials.open("a") as stream:
                    stream.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
                    stream.flush()
                raise NativeBudgetExceeded(denied)

        return receive

    def calls(self, model_id):
        events = self.latest.get(model_id, {})
        if sorted(events) != list(range(len(events))):
            raise ValueError("contiguous native request indices required")
        return [copy.deepcopy(events[i]) for i in range(len(events))]

    def references(self):
        result = dict(native_events=ref(self.path), native_event_records=self.count)
        if self.inflight.exists():
            result["native_inflight"] = ref(self.inflight)
        if self.denials.exists():
            result["native_denials"] = ref(self.denials)
        result["admitted_native_requests"] = self.admitted_total
        return result


def make_model(source, case, spec, geometry, callback):
    from fusion_baselines.clear_coil_field import ClearCoilField

    target = source["targets"][case["target"]]
    model = ClearCoilField(
        checked_source(target["wout"]),
        checked_source(target["input"]),
        geometry,
        spec["method"],
        source["normalization"][case["target"]]["B2_scale"],
        **spec["grid"],
        event_callback=callback,
    )
    bind_archived_inner_target(model, source, case)
    return model


def bind_archived_inner_target(model, source, case):
    """Install exact archived64 slices before any interior field request.

    The native Wout reconstruction is a checked replay, not the numerical
    target source. This producer implementation does not call audit helpers.
    """
    if (
        model._cache is not None
        or len(model.native_calls) != 1
        or any(
            type(model.native_calls[0].get(key)) is not type(value)
            or model.native_calls[0][key] != value
            for key, value in dict(
                index=0,
                field="loop",
                quantity="A",
                points=256,
                status="completed",
                native_started=True,
                native_completed=True,
            ).items()
        )
        or model.initialization_work != dict(seed_A_calls=1, seed_A_points=256)
        or type(model.ninner) is not int
        or model.ninner not in (32, 64)
    ):
        raise ValueError("archived target binding requires fresh one-A initialization")
    normalization = source["normalization"][case["target"]]
    archives = normalization["archives"]
    if not isinstance(archives, list) or len(archives) != 3:
        raise ValueError("three ordered pinned64 archives required")
    phi_grid, theta_grid = np.meshgrid(
        np.pi * np.arange(64) / 64, 2 * np.pi * np.arange(64) / 64, indexing="ij"
    )
    points, fields, complete, toroidal = [], [], [], []
    stride = 64 // model.ninner
    for row, surface in zip(archives, (0.25, 0.5, 0.75), strict=True):
        if type(row["n"]) is not int or row["n"] != 64 or row["s"] != surface:
            raise ValueError("exact ordered s=.25/.5/.75 archived64 targets required")
        with np.load(checked_source(row["arrays"]), allow_pickle=False) as archive:
            raw = {
                key: archive[key].copy()
                for key in ("phi", "theta", "radius", "height", "bt", "bp", "et", "ep", "native")
            }
        for key, value in raw.items():
            shape = (64, 64, 3) if key in ("et", "ep", "native") else (64, 64)
            if (
                value.dtype.kind not in "iuf"
                or value.shape != shape
                or not np.isfinite(value).all()
            ):
                raise ValueError("finite complete real archived64 arrays required")
        if (
            np.any(raw["radius"] <= 0)
            or np.max(np.abs(raw["phi"] - phi_grid)) > 5e-12
            or np.max(np.abs(raw["theta"] - theta_grid)) > 5e-12
        ):
            raise ValueError("positive R and registered64 angular nodes required")
        magnetic = raw["bt"][..., None] * raw["et"] + raw["bp"][..., None] * raw["ep"]
        if not np.allclose(raw["native"], magnetic, rtol=5e-10, atol=1e-12):
            raise ValueError("archived native and canonical Cartesian targets disagree")
        xyz = np.stack(
            (raw["radius"] * np.cos(raw["phi"]), raw["radius"] * np.sin(raw["phi"]), raw["height"]),
            axis=-1,
        )
        points.append(xyz[::stride, ::stride].reshape(-1, 3))
        fields.append(magnetic[::stride, ::stride].reshape(-1, 3))
        complete.append(magnetic.reshape(-1, 3))
        toroidal.append(magnetic[0, :, 1])
    b2 = float(np.mean(np.sum(np.concatenate(complete) ** 2, axis=1)))
    if not np.isfinite(b2) or b2 <= 0 or b2 != normalization["B2_scale"] or b2 != model.B2_scale:
        raise ValueError("exact unchanged canonical full64 B2 scale required")
    bphi = np.concatenate(toroidal)
    p, tangent = model.loop(1024)  # Pure contour geometry, no field request.
    area = float(0.5 * np.mean(p[:, 0] * tangent[:, 2] - p[:, 2] * tangent[:, 0]))
    normal = np.cross(p - p.mean(axis=0), tangent)
    if (
        not np.isfinite(bphi).all()
        or np.any(bphi == 0)
        or not np.all(np.sign(bphi) == np.sign(bphi[0]))
        or not np.isfinite(area)
        or area == 0
        or not np.isfinite(normal).all()
        or not np.all(np.sign(normal[:, 1]) == -np.sign(area))
    ):
        raise ValueError("consistent full64 toroidal sign and signed target contour required")
    flux = float(-np.sign(area) * np.sign(bphi[0]) * abs(model.input["phiedge"]))
    if not np.isfinite(flux) or flux == 0 or flux != model.target_flux:
        raise ValueError("unchanged full64 signed target flux required")
    exact = dict(inner_points=np.concatenate(points), inner_target=np.concatenate(fields))
    for key, expected in exact.items():
        for actual in (getattr(model, key), model.target[key]):
            value = np.asarray(actual)
            if (
                value.dtype.kind not in "iuf"
                or value.shape != expected.shape
                or not np.isfinite(value).all()
                or np.max(np.abs(value - expected)) > 5e-12
            ):
                raise ValueError("Wout replay differs from pinned64 target by more than 5e-12")
    # No changes are applied until every archive, scale, sign and replay check passed.
    for key, expected in exact.items():
        setattr(model, key, np.array(expected, dtype=float, order="C", copy=True))
        model.target[key] = np.array(expected, dtype=float, order="C", copy=True)


def supplement(model, raw, scale):
    raw["boundary_A"] = scale * np.asarray(model.field.A()).copy()
    raw["inner_A"] = scale * np.asarray(model.inner_field.A()).copy()
    raw["loop_B"] = scale * np.asarray(model.loop_field.B()).copy()
    return raw


def signed_fan(model, nrho, ntheta):
    from validate_coupled_coil_pilot import signed_fan as frozen_signed_fan

    return frozen_signed_fan(model, nrho, ntheta)


def execute(model, operation, frozen):
    if operation["kind"] == "qualification":
        x = np.asarray(operation["x"])
        value, gradient, metrics = model.evaluate(x)
        raw = model.arrays(x)
        snapshot = model.snapshot(x)
        return dict(
            J=value, gradient=gradient, metrics=metrics, snapshot_data=snapshot
        ), supplement(model, raw, metrics["scale"])
    snapshot, snapshot_ref = frozen
    scale, b2 = snapshot["scale"], snapshot["B2_scale"]
    common = dict(
        snapshot=snapshot_ref, scale=scale, B2_scale=b2, target_flux=snapshot["target_flux"]
    )
    if operation["kind"] == "diagnostic":
        x = np.asarray(operation["x"])
        metrics = model.diagnostics(x, scale, b2)
        raw = model.arrays(x, scale=scale, B2_scale=b2)
        return dict(common, metrics=metrics), supplement(model, raw, scale)
    ntheta = operation["ntheta"]
    if operation["form"] == "line":
        points, tangent = model.loop(ntheta)
        model.loop_field.set_points(points)
        a = scale * np.asarray(model.loop_field.A()).copy()
        b = scale * np.asarray(model.loop_field.B()).copy()
        raw = dict(points=points, tangents=tangent, A=a, B=b)
        flux = float(np.mean(np.sum(a * tangent, axis=1)))
    else:
        points, normal = signed_fan(model, operation["nrho"], ntheta)
        model.loop_field.set_points(points)
        b = scale * np.asarray(model.loop_field.B()).copy()
        a = scale * np.asarray(model.loop_field.A()).copy()
        raw = dict(points=points, weighted_normals=normal, A=a, B=b)
        flux = float(np.sum(b * normal))
    return dict(common, flux=flux), raw


def loaded_arrays(reference):
    with np.load(checked(reference), allow_pickle=False) as archive:
        return {key: archive[key].copy() for key in archive.files}


def seed_identity(normal_ref, vector_ref):
    normal, vector = read(checked(normal_ref)), read(checked(vector_ref))
    if normal["status"] != "completed" or vector["status"] != "completed":
        raise ValueError("both complete N/V seed bundles required before frozen diagnostics")
    first, second = read(checked(normal["snapshot"])), read(checked(vector["snapshot"]))
    if first.pop("method") != "N" or second.pop("method") != "V" or first != second:
        raise ValueError("N/V seed snapshots differ physically")
    a, b = loaded_arrays(normal["arrays"]), loaded_arrays(vector["arrays"])
    if set(a) != set(b) or any(not np.array_equal(a[key], b[key]) for key in a):
        raise ValueError("N/V seed raw physical arrays differ")
    if {key: value for key, value in normal["metrics"].items() if key != "J"} != {
        key: value for key, value in vector["metrics"].items() if key != "J"
    }:
        raise ValueError("N/V seed physical metrics differ")
    return dict(
        status="completed",
        passed=True,
        normal=normal_ref,
        vector=vector_ref,
        compared_arrays=sorted(a),
        snapshot=normal["snapshot"],
    )


def request_summary(models):
    calls = [event for model in models for event in model.get("native_calls", [])]
    return dict(
        native_requests=len(calls),
        completed_requests=sum(e["status"] == "completed" for e in calls),
        values=sum(e["quantity"] in ("A", "B") for e in calls),
        vjps=sum(e["quantity"] in ("A_vjp", "B_vjp") for e in calls),
        initialization_requests=sum(
            len(model.get("initialization_native_calls", [])) for model in models
        ),
        full_bundles=sum(
            row["kind"] == "qualification"
            for model in models
            for row in model.get("operation_summaries", [])
        ),
        equilibrium_solves=0,
        search_calls=0,
    )


def worker(config_path):
    config = read(config_path)
    source, case, output = config["source"], config["case"], Path(config["output"])
    if (
        case not in matrix()
        or source["matrix"] != matrix()
        or not output.is_absolute()
        or Path(config_path).resolve() != output / "config.json"
        or any(os.environ.get(key) != "1" for key in THREADS)
    ):
        raise ValueError("exact source-bound physical cell and one-thread worker required")
    guard = Guard(output, config["parent_pid"], config["started_monotonic"])
    model_refs, model_attempts, operation_refs, operation_attempts = [], [], [], []
    qualifications, diagnostics, flux = {"N": [], "V": []}, [], []
    model_documents, native, frozen, identity_ref = [], None, None, None
    model = None
    try:
        guard()
        if sources(ROOT) != source:
            raise ValueError("startup worker sources changed before any model work")
        geometry_ref = source["seeds"][case["seed_label"]]["snapshot"]
        geometry = read(checked_source(geometry_ref))
        seed = np.asarray(geometry["base_coefficients"], dtype=float).ravel()
        native = NativeLog(output, guard)
        (output / "models").mkdir()
        (output / "operations").mkdir()
        save(
            output / "plan.json",
            dict(
                models=model_plan(),
                operations=[op for spec in model_plan() for op in operations(spec, seed)],
            ),
        )
        for spec in model_plan():
            guard()
            if spec["kind"] != "qualification" and frozen is None:
                identity = seed_identity(qualifications["N"][0], qualifications["V"][0])
                save(output / "seed-identity.json", identity)
                identity_ref = ref(output / "seed-identity.json")
                frozen = (read(checked(identity["snapshot"])), identity["snapshot"])
            model_id = spec["id"]
            native.operation_id = f"init:{model_id}"
            start = time.monotonic()
            model_attempt_path = output / "models" / f"{model_id}-attempt.json"
            attempt = dict(
                spec,
                case=case,
                operation_id=native.operation_id,
                seed_geometry=geometry_ref,
                started_monotonic=start,
                B2_scale=source["normalization"][case["target"]]["B2_scale"],
            )
            save(model_attempt_path, attempt)
            model_attempts.append(ref(model_attempt_path))
            model = make_model(source, case, spec, geometry, native.callback(model_id))
            initialized = dict(
                spec,
                status="completed",
                model_id=model_id,
                initialization_operation_id=native.operation_id,
                attempt=model_attempts[-1],
                seed_geometry=geometry_ref,
                seed_x=model.seed_x,
                names=model.names,
                B2_scale=model.B2_scale,
                target_flux=model.target_flux,
                seed_unit_flux=model.seed_unit_flux,
                initialization_work=model.initialization_work,
                started_monotonic=start,
                ended_monotonic=time.monotonic(),
                native_range=[0, len(model.native_calls)],
                initialization_native_calls=copy.deepcopy(model.native_calls),
            )
            initialized_path = output / "models" / f"{model_id}-initialized.json"
            save(initialized_path, initialized)
            guard()
            model_rows, summaries = [], []
            for operation in operations(spec, seed):
                guard()
                operation_id = operation["operation_id"]
                native.operation_id = operation_id
                op_started, native_start = time.monotonic(), len(model.native_calls)
                attempt = dict(
                    operation,
                    started_monotonic=op_started,
                    native_start=native_start,
                    native_event_start=native.count,
                )
                path = output / "operations" / f"{operation_id}-attempt.json"
                save(path, attempt)
                operation_attempts.append(ref(path))
                row = dict(
                    operation,
                    status="running",
                    attempt=operation_attempts[-1],
                    started_monotonic=op_started,
                )
                try:
                    metadata, raw = execute(model, operation, frozen)
                    row.update(metadata)
                    row["arrays"] = storage.arrays(
                        output / "operations" / f"{operation_id}.npz", raw
                    )
                    if "snapshot_data" in row:
                        snapshot_path = output / "operations" / f"{operation_id}-snapshot.json"
                        save(snapshot_path, row.pop("snapshot_data"))
                        row["snapshot"] = ref(snapshot_path)
                    row["status"] = "completed"
                except (TimeoutError, OSError, ParentLost, NativeBudgetExceeded):
                    raise
                except Exception as error:
                    row.update(status="error", error_type=type(error).__name__, error=str(error))
                    row.pop("snapshot_data", None)
                row.update(
                    ended_monotonic=time.monotonic(),
                    native_range=[native_start, len(model.native_calls)],
                    native_event_range=[attempt["native_event_start"], native.count],
                )
                row_path = output / "operations" / f"{operation_id}.json"
                save(row_path, row)
                # Completed raw work survives a late finish but cannot advance the checkpoint.
                guard()
                row_ref = ref(row_path)
                operation_refs.append(row_ref)
                model_rows.append(row_ref)
                summaries.append(
                    {key: row[key] for key in ("operation_id", "kind", "status", "native_range")}
                )
                if spec["kind"] == "qualification":
                    qualifications[spec["method"]].append(row_ref)
                elif spec["kind"] == "diagnostic":
                    diagnostics.append(row_ref)
                if row["status"] == "completed":
                    save(
                        output / "checkpoint.json",
                        dict(
                            models=model_refs,
                            operations=operation_refs,
                            qualification=qualifications,
                            diagnostics=diagnostics,
                            flux=flux,
                            native_event_records=native.count,
                        ),
                    )
            document = dict(
                initialized,
                initialized=ref(initialized_path),
                operations=model_rows,
                operation_summaries=summaries,
                native_calls=copy.deepcopy(model.native_calls),
                model_ended_monotonic=time.monotonic(),
                status="completed"
                if all(row["status"] == "completed" for row in summaries)
                else "error",
            )
            path = output / "models" / f"{model_id}.json"
            save(path, document)
            model_refs.append(ref(path))
            model_documents.append(document)
            if spec["kind"] == "flux":
                rows = [read(checked(item)) for item in model_rows]
                block = dict(
                    status=document["status"],
                    full_bundles=0,
                    model_id=model_id,
                    ncoil=spec["grid"]["ncoil"],
                    snapshot=frozen[1],
                    scale=frozen[0]["scale"],
                    B2_scale=frozen[0]["B2_scale"],
                    target_flux=frozen[0]["target_flux"],
                    model=ref(path),
                    lines=[
                        reference
                        for reference, row in zip(model_rows, rows, strict=True)
                        if row["form"] == "line"
                    ],
                    areas=[
                        reference
                        for reference, row in zip(model_rows, rows, strict=True)
                        if row["form"] == "area"
                    ],
                )
                block_path = output / f"{model_id}.json"
                save(block_path, block)
                flux.append(ref(block_path))
            del model
            model = None
            gc.collect()
        guard()
        after = sources(ROOT)
        if after != source:
            raise ValueError("startup worker sources changed during execution")
        summary = request_summary(model_documents)
        complete = (
            len(operation_refs) == 44
            and all(doc["status"] == "completed" for doc in model_documents)
            and summary
            == dict(
                native_requests=262,
                completed_requests=262,
                values=202,
                vjps=60,
                initialization_requests=10,
                full_bundles=20,
                equilibrium_solves=0,
                search_calls=0,
            )
        )
        record = dict(
            schema_version=1,
            kind="clear-coil-field-start-cell",
            status="completed" if complete else "error",
            case=case,
            source_before=source,
            source_after=after,
            models=model_refs,
            model_attempts=model_attempts,
            operations=operation_refs,
            operation_attempts=operation_attempts,
            qualification=qualifications,
            diagnostics=diagnostics,
            flux=flux,
            seed_identity=identity_ref,
            snapshot=frozen[1],
            work=summary,
            **native.references(),
            threads={key: os.environ[key] for key in THREADS},
            elapsed_seconds=deadline(config["started_monotonic"]),
            ended_monotonic=time.monotonic(),
            minimum_observed_free_bytes=guard.minimum_free_bytes,
            scope=SCOPE,
        )
        save(output / "worker.json", record)
        return 0 if complete else 1
    except Exception as error:
        record = dict(
            status="error",
            error_type=type(error).__name__,
            error=str(error),
            case=case,
            models=model_refs,
            model_attempts=model_attempts,
            operations=operation_refs,
            operation_attempts=operation_attempts,
            qualification=qualifications,
            diagnostics=diagnostics,
            flux=flux,
            scope=SCOPE,
            elapsed_seconds=time.monotonic() - config["started_monotonic"],
        )
        if native is not None:
            record.update(native.references())
            record["native_prefixes"] = {key: native.calls(key) for key in native.latest}
        if model is not None:
            record["current_model_native_calls"] = copy.deepcopy(model.native_calls)
        save(output / "worker-error.json", record)
        return 1


def run_process(command, output, env, started):
    def check(path, reserve):
        deadline(started)
        return space_check(path, reserve)

    try:
        with (output / "stdout.txt").open("x") as stdout:
            process = guarded_run(
                command,
                cwd=ROOT,
                env=env,
                stdout=stdout,
                space_root=output,
                reserve_bytes=2 * GIB,
                check=check,
                interval=0.5,
            )
        return dict(process, timed_out=False, elapsed_seconds=time.monotonic() - started)
    except Exception as error:
        return dict(
            returncode=None,
            timed_out=isinstance(error, TimeoutError),
            error_type=type(error).__name__,
            error=str(error),
            elapsed_seconds=time.monotonic() - started,
        )


def process_complete(process, document, case, source, started):
    times = (
        process.get("elapsed_seconds"),
        document.get("elapsed_seconds"),
        document.get("ended_monotonic"),
        started,
    )
    if any(
        type(value) not in (int, float) or not np.isfinite(value) or value < 0 for value in times
    ):
        raise ValueError("finite nonnegative worker/process clocks required")
    if (
        type(process.get("returncode")) is not int
        or process["returncode"] != 0
        or process.get("timed_out") is not False
        or process.get("error_type")
        or process["elapsed_seconds"] >= WALL_SECONDS
        or document["elapsed_seconds"] >= WALL_SECONDS
        or not 0 <= document["ended_monotonic"] - started < WALL_SECONDS
        or document.get("status") != "completed"
        or document.get("case") != case
        or document.get("source_before") != source
        or document.get("source_after") != source
        or document.get("threads") != {key: "1" for key in THREADS}
        or document.get("scope") != SCOPE
    ):
        raise ValueError("timely successful source-bound physical worker required")


def _run(output):
    before = sources(ROOT)
    if before["matrix"] != matrix():
        raise ValueError("registered four physical cells required")
    save(output / "source-before.json", before)
    env = dict(os.environ, **{key: "1" for key in THREADS})
    env["PYTHONPATH"] = str(ROOT / "src")
    env.setdefault("MPLCONFIGDIR", "/private/tmp/fusion-mpl-cache")
    rows = []
    for index, case in enumerate(matrix()):
        space_check(output, 3 * GIB)
        directory = output / case["label"]
        directory.mkdir()
        started = time.monotonic()
        config = dict(
            case=case,
            output=str(directory),
            source=before,
            parent_pid=os.getpid(),
            started_monotonic=started,
        )
        save(directory / "config.json", config)
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker",
            str(directory / "config.json"),
        ]
        save(directory / "launch.json", dict(command=command, started_monotonic=started, case=case))
        process = run_process(command, directory, env, started)
        save(directory / "process.json", process)
        row = dict(
            index=index,
            case=case,
            status="error",
            config=ref(directory / "config.json"),
            launch=ref(directory / "launch.json"),
            process=ref(directory / "process.json"),
        )
        try:
            document = read(directory / "worker.json")
            process_complete(process, document, case, before, started)
            row.update(status="completed", worker=ref(directory / "worker.json"))
        except Exception as error:
            row.update(error_type=type(error).__name__, error=str(error))
        row["retained"] = [ref(path) for path in sorted(directory.rglob("*")) if path.is_file()]
        save(directory / "result.json", row)
        rows.append(ref(directory / "result.json"))
        if row["status"] == "completed":
            save(output / "checkpoint.json", dict(rows=rows))
    after = sources(ROOT)
    save(output / "source-after.json", after)
    complete = before == after and all(
        read(checked(item))["status"] == "completed" for item in rows
    )
    result = dict(
        schema_version=1,
        kind="clear-coil-field-start",
        status="completed",
        source_before=before,
        source_after=after,
        source_unchanged=before == after,
        matrix=matrix(),
        rows=rows,
        producer_complete=bool(complete),
        admission_status="pending-independent-audit",
        **SCOPE,
        limits=dict(
            wall_seconds=WALL_SECONDS,
            parent_poll_seconds=0.5,
            termination_grace_seconds=5,
            start_reserve_bytes=3 * GIB,
            live_reserve_bytes=2 * GIB,
        ),
    )
    save(output / "run.json", result)
    return result


def run(output):
    output = Path(output)
    if not output.is_absolute():
        raise ValueError("absolute fresh output directory required")
    output.mkdir(parents=True, exist_ok=False)
    try:
        return _run(output)
    except Exception as error:
        save(
            output / "terminal-error.json",
            dict(status="error", error_type=type(error).__name__, error=str(error), scope=SCOPE),
        )
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--raw", type=Path)
    group.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker is not None:
        return worker(args.worker)
    result = run(args.raw)
    print(
        json.dumps(
            dict(
                status=result["status"],
                producer_complete=result["producer_complete"],
                run=ref(args.raw / "run.json"),
            ),
            allow_nan=False,
        )
    )
    return 0 if result["producer_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
