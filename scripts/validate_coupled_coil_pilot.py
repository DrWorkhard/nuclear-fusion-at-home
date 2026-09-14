"""No-feedback, fixed-current diagnostics for the registered paired-coil pilot.

The source-selected physical snapshot is never replaced by a fine-grid
renormalization. This producer records every registered level, including errors;
only the separate auditor may judge the entry screen. No VMEC or gradient work.
"""

import argparse
import json
import os
import time
from pathlib import Path

import numpy as np
from current_diagnostic_inputs import checked, reference

from fusion_baselines.coupled_coil_audit import geometry_certificates, validate_snapshot
from fusion_baselines.coupled_coil_workflow import cases, choose_search
from fusion_baselines.provenance import write_json_atomic
from fusion_baselines.resource_guard import GIB, space_check


def json_value(value):
    """Convert numpy scalars but refuse nonfinite or non-JSON evidence."""
    if isinstance(value, np.ndarray):
        return json_value(value.tolist())
    if isinstance(value, np.generic):
        return json_value(value.item())
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise ValueError("JSON evidence requires string keys")
        return {key: json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_value(item) for item in value]
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float) and np.isfinite(value):
        return value
    raise ValueError("nonfinite or unsupported JSON evidence value")


def save_json(path, value):
    write_json_atomic(Path(path), json_value(value))


def save_arrays(path, arrays):
    """Exclusive raw-data creation: existing evidence is never replaced."""
    path = Path(path)
    arrays = {key: np.asarray(value) for key, value in arrays.items()}
    if not arrays or any(
        value.dtype.kind not in "biuf" or not np.isfinite(value).all() for value in arrays.values()
    ):
        raise ValueError("finite nonempty numeric raw arrays required")
    with path.open("xb") as handle:
        np.savez_compressed(handle, **arrays)
    return reference(path)


def validation_levels():
    return [
        dict(
            kind="boundary",
            label="boundary-64-c256",
            ncoil=256,
            nphi=64,
            ntheta=64,
            ninner=16,
            offset=0,
        ),
        dict(
            kind="boundary",
            label="boundary-128-c256",
            ncoil=256,
            nphi=128,
            ntheta=128,
            ninner=16,
            offset=0,
        ),
        dict(
            kind="boundary",
            label="boundary-128-c512",
            ncoil=512,
            nphi=128,
            ntheta=128,
            ninner=16,
            offset=0,
        ),
        dict(
            kind="boundary",
            label="boundary-128-c512-shift",
            ncoil=512,
            nphi=128,
            ntheta=128,
            ninner=16,
            offset=0.5,
        ),
        dict(
            kind="inner", label="inner-32-c256", ncoil=256, nphi=32, ntheta=32, ninner=32, offset=0
        ),
        dict(
            kind="inner", label="inner-64-c256", ncoil=256, nphi=32, ntheta=32, ninner=64, offset=0
        ),
        dict(
            kind="inner", label="inner-64-c512", ncoil=512, nphi=32, ntheta=32, ninner=64, offset=0
        ),
    ]


def _native_field(model):
    from simsopt.field import BiotSavart

    # Separate field cache: flux diagnostics cannot leave the model's cached
    # construction points inconsistent with its already-evaluated arrays.
    return BiotSavart(model.coils)


def _physical_fields(field, points, scale, work):
    points = np.ascontiguousarray(points, dtype=float).reshape(-1, 3)
    if not np.isfinite(points).all() or not len(points):
        raise ValueError("finite nonempty field points required")
    field.set_points(points)
    arrays = {}
    for name in ("B", "A"):
        call = dict(quantity=name, points=len(points), status="attempted")
        work.append(call)
        try:
            values = scale * np.asarray(getattr(field, name)(), dtype=float).copy()
            if values.shape != points.shape or not np.isfinite(values).all():
                raise ValueError("nonfinite or incompatible physical field")
            if name == "B" and np.any(np.linalg.norm(values, axis=1) <= 0):
                raise ValueError("zero physical field at registered diagnostic point")
            arrays[name] = values
            call["status"] = "completed"
        except Exception as exc:
            call.update(status="error", error=f"{type(exc).__name__}: {exc}")
            raise
    return arrays


def signed_fan(model, nrho, ntheta):
    """Producer's signed radial fan, independent of audit.fan_area."""
    if nrho not in (16, 32) or ntheta not in (256, 512, 1024):
        raise ValueError("registered radial/angular fan resolution required")
    section, tangent = [np.asarray(v, dtype=float) for v in model.loop(ntheta)]
    center = np.asarray(model.loop(1024)[0], dtype=float).mean(axis=0)
    if section.shape != (ntheta, 3) or tangent.shape != section.shape:
        raise ValueError("one complete Cartesian loop and analytic tangent required")
    if not np.isfinite([section, tangent]).all() or not np.isfinite(center).all():
        raise ValueError("finite fan section required")
    if np.any(section[:, 1] != 0) or np.any(tangent[:, 1] != 0) or center[1] != 0:
        raise ValueError("registered phi=0 R-Z fan required")
    if np.any(section[:, 0] <= 0) or center[0] <= 0:
        raise ValueError("fan boundary and center must have positive R")
    delta = section - center
    jacobian = np.cross(delta, tangent)
    if np.any(jacobian[:, 1] == 0) or not np.all(
        np.sign(jacobian[:, 1]) == np.sign(jacobian[0, 1])
    ):
        raise ValueError("fan Jacobian is zero or changes orientation")
    rho, weights = np.polynomial.legendre.leggauss(nrho)
    rho, weights = (rho + 1) / 2, weights / 2
    points = center + rho[:, None, None] * delta[None, :, :]
    normals = (weights * rho)[:, None, None] * jacobian[None, :, :] / ntheta
    if np.any(points[..., 0] <= 0) or not np.isfinite([points, normals]).all():
        raise ValueError("fan crosses nonpositive R or has nonfinite geometry")
    return points.reshape(-1, 3), normals.reshape(-1, 3)


def flux_diagnostics(model, x, snapshot, output_dir, ncoil=128):
    """Native signed line/area data at unchanged physical current; zero bundles.

    All nine registered records are retained, even after a previous level fails.
    Returned scalar fluxes are provisional measurements, not acceptance flags.
    """
    validate_snapshot(snapshot)
    x = np.asarray(x, dtype=float)
    if (
        ncoil not in (128, 512)
        or model.ncoil != ncoil
        or not np.array_equal(x, np.ravel(snapshot["base_coefficients"]))
        or model.names != snapshot["names"]
    ):
        raise ValueError("fixed physical snapshot, named parameters and source grid required")
    if not np.array_equal(model.x, x):
        model.x = x
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    scale = float(snapshot["scale"])
    result = dict(
        schema_version=1,
        status="running",
        ncoil=ncoil,
        scale=scale,
        B2_scale=snapshot["B2_scale"],
        target_flux=snapshot["target_flux"],
        lines=[],
        areas=[],
        native_calls=[],
        resources=[],
        full_bundles=0,
        transfer_pass=False,
        step4_pass=False,
    )
    try:
        field = _native_field(model)
        result["field_initialization"] = dict(status="completed")
    except Exception as exc:
        field = None
        result["field_initialization"] = dict(status="error", error=f"{type(exc).__name__}: {exc}")
    for ntheta in (256, 512, 1024):
        row = dict(ntheta=ntheta, status="running")
        result["lines"].append(row)
        try:
            result["resources"].append(space_check(output_dir, 2 * GIB))
            if field is None:
                raise ValueError(result["field_initialization"]["error"])
            points, tangents = model.loop(ntheta)
            fields = _physical_fields(field, points, scale, result["native_calls"])
            row["arrays"] = save_arrays(
                output_dir / f"line-{ntheta}.npz",
                dict(points=points, tangents=tangents, **fields),
            )
            row.update(
                status="completed", flux=float(np.mean(np.sum(fields["A"] * tangents, axis=1)))
            )
        except Exception as exc:
            row.update(status="error", error=f"{type(exc).__name__}: {exc}")
        save_json(output_dir / "run.json", result)
    for nrho in (16, 32):
        for ntheta in (256, 512, 1024):
            row = dict(nrho=nrho, ntheta=ntheta, status="running")
            result["areas"].append(row)
            try:
                result["resources"].append(space_check(output_dir, 2 * GIB))
                if field is None:
                    raise ValueError(result["field_initialization"]["error"])
                points, normals = signed_fan(model, nrho, ntheta)
                fields = _physical_fields(field, points, scale, result["native_calls"])
                row["arrays"] = save_arrays(
                    output_dir / f"area-{nrho}-{ntheta}.npz",
                    dict(points=points, weighted_normals=normals, **fields),
                )
                row.update(status="completed", flux=float(np.sum(fields["B"] * normals)))
            except Exception as exc:
                row.update(status="error", error=f"{type(exc).__name__}: {exc}")
            save_json(output_dir / "run.json", result)
    result["status"] = (
        "completed"
        if all(row["status"] == "completed" for row in result["lines"] + result["areas"])
        else "error"
    )
    try:
        result["resources_after"] = space_check(output_dir, 2 * GIB)
        result["resources"].append(result["resources_after"])
    except OSError as exc:
        result.update(status="error", resource_terminal_error=str(exc))
    result["minimum_observed_free_bytes"] = min(
        (row["free_bytes"] for row in result["resources"]), default=None
    )
    save_json(output_dir / "run.json", result)
    return result


def selected_source(search, search_ref, audit, source):
    """Require independent search bookkeeping admission, not physical admission."""
    if (
        search.get("phase") != "search"
        or search.get("status") != "completed"
        or search.get("source") != source
        or search.get("case") not in cases()
        or audit.get("status") != "completed"
        or audit.get("phase") != "search"
        or audit.get("arithmetic_and_source_pass") is not True
        or audit.get("search_pass") is not True
        or audit.get("search") != search_ref
        or audit.get("source") != source
        or audit.get("case") != search["case"]
    ):
        raise ValueError("matching completed independent search audit required")
    selected = search.get("selected")
    if type(selected) is not int or selected != choose_search(search["rows"]):
        raise ValueError("audited stable actual-search minimum required")
    row = search["rows"][selected]
    snapshot = json.loads(checked(row["snapshot"]).read_text())
    validate_snapshot(snapshot)
    if (
        snapshot["names"] != search["names"]
        or not np.array_equal(row["x"], np.ravel(snapshot["base_coefficients"]))
        or any(
            snapshot[k] != row["metrics"][k]
            for k in ("scale", "unit_flux", "target_flux", "B2_scale")
        )
    ):
        raise ValueError("selected physical snapshot and construction normalization differ")
    return row, snapshot


def geometry_diagnostics(snapshot, input_path, output_dir):
    """A correctly unavailable physical certificate is not an execution failure."""
    known_uncertified = {
        "strictly positive speed not certified between curve nodes",
        "detected coincident non-endpoint filament positions within roundoff",
        "zero-speed filament",
        "degenerate zero-speed curve",
    }
    try:
        geometry = geometry_certificates(snapshot, input_path, 1024, 256, 256)
        path = Path(output_dir) / "geometry.json"
        if path.exists():
            raise FileExistsError("fresh geometry evidence required")
        save_json(path, geometry)
        return dict(status="completed", result=reference(path))
    except ValueError as exc:
        return dict(
            status="uncertified" if str(exc) in known_uncertified else "error",
            error=f"{type(exc).__name__}: {exc}",
            certificate_available=False,
        )
    except Exception as exc:
        return dict(status="error", error=f"{type(exc).__name__}: {exc}")


def validate(search_path, search_audit_path, output_dir):
    from coupled_coil_inputs import sources

    from fusion_baselines.coupled_coils import CoupledCoils

    root = Path(__file__).resolve().parents[1]
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        if os.environ.get(name) != "1":
            raise ValueError(f"{name}=1 required for serial registered diagnostics")
    search_path, search_audit_path = Path(search_path), Path(search_audit_path)
    if not search_path.is_absolute() or not search_audit_path.is_absolute():
        raise ValueError("absolute bound search and audit paths required")
    source = sources(root)
    search, audit = [json.loads(path.read_text()) for path in (search_path, search_audit_path)]
    selected, snapshot = selected_source(search, reference(search_path), audit, source)
    reserve = space_check(root, 3 * GIB)
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    case = search["case"]
    target = source["targets"][case["target"]]
    x = np.asarray(selected["x"], dtype=float)
    scale, b2 = snapshot["scale"], snapshot["B2_scale"]
    run = dict(
        schema_version=1,
        status="running",
        phase="validation",
        source=source,
        case=case,
        search=reference(search_path),
        search_audit=reference(search_audit_path),
        selected=search["selected"],
        x=x.tolist(),
        names=snapshot["names"],
        seed_x=search["seed_x"],
        snapshot=selected["snapshot"],
        rows=[],
        flux=None,
        geometry=None,
        resources=dict(before=reserve),
        native_initializations=[],
        threads={
            name: os.environ[name]
            for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")
        },
        full_bundles=0,
        equilibrium_solves=0,
        entry_pass=False,
        entry_assessment="independent audit required",
        transfer_pass=False,
        step4_pass=False,
    )
    save_json(output_dir / "run.json", run)
    flux_model = None
    for level in validation_levels():
        row = dict(level, status="running", native_calls=[])
        run["rows"].append(row)
        init = dict(label=level["label"], status="attempted")
        run["native_initializations"].append(init)
        start = time.monotonic()
        try:
            space_check(root, 2 * GIB)
            model = CoupledCoils(
                checked(target["wout"]),
                checked(target["input"]),
                case["nbase"],
                case["order"],
                case["method"],
                **{k: level[k] for k in ("ncoil", "nphi", "ntheta", "ninner", "offset")},
            )
            init.update(status="completed", work=model.initialization_work)
            if model.names != snapshot["names"]:
                raise ValueError("fine native physical names differ from source candidate")
            # This value-only state issues B(boundary), B(inner), A(loop); no VJP.
            call = dict(quantity="diagnostics", status="attempted", value_calls=3)
            row["native_calls"].append(call)
            row["metrics"] = model.diagnostics(x, scale=scale, B2_scale=b2)
            call["status"] = "completed"
            arrays = model.arrays(x, scale=scale, B2_scale=b2)
            for key, field, quantity in (
                ("boundary_A", model.field, "A"),
                ("inner_A", model.inner_field, "A"),
                ("loop_B", model.loop_field, "B"),
            ):
                call = dict(quantity=key, status="attempted")
                row["native_calls"].append(call)
                arrays[key] = scale * getattr(field, quantity)().copy()
                call["status"] = "completed"
            row["arrays"] = save_arrays(output_dir / f"{level['label']}.npz", arrays)
            row["status"] = "completed"
            if level["ncoil"] == 512:
                flux_model = model
        except Exception as exc:
            row.update(status="error", error=f"{type(exc).__name__}: {exc}")
            if init["status"] == "attempted":
                init.update(status="error", error=row["error"])
        row["elapsed_seconds"] = time.monotonic() - start
        save_json(output_dir / "run.json", run)
    try:
        space_check(root, 2 * GIB)
        if flux_model is None:
            raise ValueError("no completed frozen-current 512-node native model")
        run["flux"] = flux_diagnostics(flux_model, x, snapshot, output_dir / "flux", ncoil=512)
    except Exception as exc:
        run["flux"] = dict(status="error", error=f"{type(exc).__name__}: {exc}")
    save_json(output_dir / "run.json", run)
    try:
        space_check(root, 2 * GIB)
        run["geometry"] = geometry_diagnostics(snapshot, checked(target["input"]), output_dir)
    except Exception as exc:
        run["geometry"] = dict(status="error", error=f"{type(exc).__name__}: {exc}")
    try:
        run["resources"]["after"] = space_check(root, 2 * GIB)
    except OSError as exc:
        run["resources"]["terminal_error"] = str(exc)
    complete = all(row["status"] == "completed" for row in run["rows"])
    complete &= run["flux"]["status"] == "completed" and run["geometry"]["status"] in (
        "completed",
        "uncertified",
    )
    run["status"] = (
        "completed" if complete and "terminal_error" not in run["resources"] else "error"
    )
    save_json(output_dir / "run.json", run)
    return run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--search", required=True, type=Path)
    parser.add_argument("--search-audit", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run = validate(args.search, args.search_audit, args.output)
    print(
        json.dumps(
            dict(status=run["status"], rows=len(run["rows"]), transfer_pass=False, step4_pass=False)
        )
    )
    return 0 if run["status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
