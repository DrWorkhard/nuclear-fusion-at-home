"""Static field screen of four previously audited starts; no design acceptance."""

import argparse
import importlib
import io
import json
import shutil
import time
from pathlib import Path

import numpy as np

from fusion_baselines.boundary_control_metrics import boundary_metrics
from fusion_baselines.provenance import git_state, sha256_file

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "artifacts/clear-coil-initialization-v1/sets/"
CASES = {
    "n6-circle-d100mm": "829ea3573b6e46771d771810420c0e378a07f4bb16363305376f4b6d39856de6",
    "n6-shape-d100mm": "90fe6f84395d319d45ac39fab832a2b3908f0d16d7638e971e2a4602a3ef65d1",
    "n6-shape-d140mm": "53784adda5dd4d0d4d5fba3b1ba31e08707d55624ed7d9b633999298b54580df",
    "n6-shape-d180mm": "40e075d4fc856c0149523a5c6be8139dd65f4499ac602fbbd9c09c5a3cf100e1",
}
TARGET = "evidence/plasma-design-v2/reference-input-401.json"
REFERENCE = ("artifacts/clear-coil-field-start-v1/reference-n6/operations/"
             "qualification-N-00-snapshot.json")
SEED_RESULT = REFERENCE.replace("-snapshot.json", ".json")
AUDIT = "evidence/clear-coil-initialization-v1-audit.json"
RUN = "artifacts/clear-coil-initialization-v1/run.json"
INPUTS = {
    TARGET: "57394ef682f3c6399faa03012abc02da2eb1ce40703a4f99640ece3d07e5691f",
    REFERENCE: "4c29c1f7afb67f290bd3c7c2ec23829e5f386e7e8c299f8d40a0e0f4e2f03830",
    SEED_RESULT: "264f345594ed2effa987f836e3e3167623db233024bf454da917b0c129dcde8f",
    AUDIT: "b068fd6a6c76e8b4aaf57341e5a2ae139be196f35defacc644f1d5c890c0ea49",
    RUN: "5f3f5b86e3a80101491a70475fbbbdcdee6138754873463a1c63f0545b45a309",
    **{PREFIX+case+"/snapshot.json": digest for case, digest in CASES.items()},
}
SCHEDULE = ((64, 256, 0.), (128, 512, 0.), (128, 512, .5))
SECONDS, MAX_BYTES = 180, 64*1024**2


def fingerprints():
    modules = ("simsoptpp", "simsopt.field.biotsavart", "simsopt.field.coil",
               "simsopt.field.magneticfield", "simsopt.geo.curve", "simsopt.geo.curvexyzfourier",
               "simsopt._core.optimizable", "simsopt._core.util",
               "fusion_baselines.clear_coil_geometry_audit", "fusion_baselines.coupled_coil_audit",
               "fusion_baselines.boundary_control_metrics", "fusion_baselines.provenance")
    paths = [Path(importlib.import_module(m).__file__).resolve() for m in modules]
    paths += [Path(__file__).resolve(), *(ROOT/name for name in INPUTS)]
    return {str(path): sha256_file(path) for path in paths}


def normalize(target, unit_flux):
    if not np.isfinite([target, unit_flux]).all() or target == 0 or abs(unit_flux) <= 1e-12:
        raise ValueError("finite nonzero target and nondegenerate fresh unit flux required")
    scale = float(target/unit_flux)
    if not np.isfinite(scale):
        raise ValueError("nonfinite physical current scale")
    return scale


def error(actual, expected):
    a, b = np.asarray(actual).reshape(-1, 3), np.asarray(expected).reshape(-1, 3)
    if a.shape != b.shape or not len(a) or not np.isfinite([a, b]).all():
        raise ValueError("matched finite nonempty vector arrays required")
    return float(np.max(np.linalg.norm(a-b, axis=1)/np.maximum(1., np.linalg.norm(b, axis=1))))


def seed_replay(metrics, original):
    return {key: dict(actual=metrics[key], expected=original[old], passed=bool(np.isclose(
        metrics[key], original[old], rtol=1e-10, atol=1e-12)))
        for key, old in (("unit_flux", "unit_flux"), ("scale", "scale"),
                         ("flux_normalized_raw", "JN"), ("normal_rms", "normal_rms"))}


def native_coils(snapshot, nodes):
    from simsopt.field import Current, coils_via_symmetries
    from simsopt.geo import CurveXYZFourier

    from fusion_baselines.clear_coil_geometry_audit import physical_curves

    own = physical_curves(snapshot, nodes)
    if (snapshot["nbase"], snapshot["order"]) != (6, 5):
        raise ValueError("six order-five base coils required")
    curves, currents = [], []
    for i, coefficients in enumerate(snapshot["base_coefficients"]):
        curve, current = CurveXYZFourier(nodes, 5), Current(1e5)
        if [f"coil[{i}]/{name}" for name in curve.local_full_dof_names] != (
                snapshot["names"][33*i:33*(i+1)]):
            raise ValueError("named physical coefficient mapping changed")
        curve.local_full_x = np.asarray(coefficients).ravel()
        curve.fix_all()
        current.fix_all()
        curves.append(curve)
        currents.append(current)
    coils = coils_via_symmetries(curves, currents, 2, True)
    own["currents"] = np.array([-1e5 if row["flip"] else 1e5 for row in snapshot["physical"]])
    checks = dict(position=error([c.curve.gamma() for c in coils], own["positions"]),
                  tangent=error([c.curve.gammadash() for c in coils], own["tangents"]))
    if (not np.array_equal([c.current.get_value() for c in coils], own["currents"])
            or max(checks.values()) > 1e-12):
        raise ValueError("native/independent physical coil identity differs")
    return coils, own, checks


def screen(snapshot, target, reference, n, nodes, shift, frozen_scale, guard, counts):
    from simsopt.field import BiotSavart

    from fusion_baselines.coupled_coil_audit import boundary, filament_field_and_potential, loop

    def call(name, function, *args):
        guard()
        counts[name]["attempted"] += 1
        answer = function(*args)
        counts[name]["completed"] += 1
        guard()
        return answer

    def sample(field, name, points):
        blocks = []
        for first in range(0, len(points), 128):
            field.set_points(np.ascontiguousarray(points[first:first+128]))
            blocks.append(call(name, getattr(field, name)).copy())
        return np.concatenate(blocks)

    guard()
    coils, own, identity = native_coils(snapshot, nodes)
    field = BiotSavart(coils)  # Plain native identity; no instrumentation subclass.
    lp, tangent = loop(target, nodes)
    unit_A = sample(field, "A", lp)
    phi = float(np.mean(np.sum(unit_A*tangent, axis=1)))
    fresh_scale = normalize(reference["target_flux"], phi)
    scale = fresh_scale if frozen_scale is None else frozen_scale
    surface = boundary(target, n, n, shift=bool(shift))
    points, normals = surface["points"], surface["normal"]
    B = scale*sample(field, "B", points.reshape(-1, 3)).reshape(points.shape)
    currents, A = scale*own["currents"], scale*unit_A
    indices, loop_indices = np.linspace(0, n*n-1, 64, dtype=int), np.linspace(0, nodes-1, 64,
                                                                           dtype=int)
    independent_B, _ = call("independent", filament_field_and_potential,
                            points.reshape(-1, 3)[indices], own["positions"], own["tangents"],
                            currents)
    _, independent_A = call("independent", filament_field_and_potential,
                            lp[loop_indices], own["positions"], own["tangents"], currents)
    checks = dict(B=error(independent_B, B.reshape(-1, 3)[indices]),
                  A=error(independent_A, A[loop_indices]), **identity)
    metrics = boundary_metrics(B, normals)
    metrics.update(base_current=1e5*scale, current_limit_met=abs(1e5*scale) <= 500000,
                   scale=scale, unit_flux=phi, fine_renormalization_applied=False,
                   measured_flux=scale*phi, target_flux=reference["target_flux"],
                   flux_relative_error=abs(scale*phi/reference["target_flux"]-1),
                   flux_normalized_raw=metrics["raw_quadratic_flux"]
                   / (metrics["mean_area_jacobian"]*reference["B2_scale"]),
                   normal_limit_met=metrics["normal_rms"] <= 1e-4,
                   normal_max_limit_met=metrics["normal_max"] <= 1e-3)
    metrics["flux_limit_met"] = metrics["flux_relative_error"] <= 1e-6
    arrays = dict(points=points, normals=normals, B=B, loop_points=lp, loop_tangent=tangent, A=A,
                  positions=own["positions"], tangents=own["tangents"], currents=currents,
                  indices=indices, loop_indices=loop_indices,
                  independent_B=independent_B, independent_A=independent_A)
    guard()
    return dict(n=n, nodes=nodes, shift=shift, metrics=metrics, checks=checks,
                checks_pass=max(checks.values()) <= 1e-12), arrays, scale


def run(output):
    started = time.monotonic()
    if output.exists():
        raise FileExistsError("fresh output directory required")
    if shutil.disk_usage(ROOT).free < 3*1024**3:
        raise OSError("3 GiB starting reserve required")
    output.mkdir(parents=True)

    def guard():
        if time.monotonic()-started >= SECONDS:
            raise TimeoutError("180 s exploratory limit reached")
        if shutil.disk_usage(output).free < 2*1024**3:
            raise OSError("2 GiB live reserve required")

    def save(name, value):
        payload = value if isinstance(value, bytes) else (
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+"\n").encode("utf-8")
        if sum(p.stat().st_size for p in output.iterdir()) + len(payload) > MAX_BYTES:
            raise OSError("64 MiB output cap reached")
        with (output/name).open("xb") as stream:
            stream.write(payload)

    for name, digest in INPUTS.items():
        if sha256_file(ROOT/name) != digest:
            raise ValueError(f"fixed source changed: {name}")
    source = {name: json.loads((ROOT/name).read_text(encoding="utf-8")) for name in INPUTS}
    reference = {key: source[REFERENCE][key] for key in ("target_flux", "B2_scale")}
    if (not np.isfinite(list(reference.values())).all() or reference["B2_scale"] <= 0
            or source[AUDIT]["geometry_pass"] is not True):
        raise ValueError("finite target, positive fixed B2 and previous geometry pass required")
    counts = {name: dict(attempted=0, completed=0) for name in ("B", "A", "independent")}
    report = dict(kind="static-coil-start-screen", sources_before=fingerprints(),
                  repository=git_state(ROOT), rows=[], counts=counts, normalization=reference,
                  schedule=SCHEDULE, completed=False, physical_admission=False,
                  new_geometry_certificate=False, inner_vector_checked=False)
    save("inputs.json", report)
    try:
        for case in CASES:
            snapshot = source[PREFIX+case+"/snapshot.json"]
            audited = [r for r in source[AUDIT]["sets"] if r["case"]["label"] == case]
            if (len(audited) != 1 or not audited[0]["geometry_pass"]
                    or snapshot["case"]["label"] != case
                    or snapshot["sources"]["reference"]["input"]["sha256"] != INPUTS[TARGET]):
                raise ValueError("unchanged audited geometry and matching target required")
            scale = None
            for index, (n, nodes, shift) in enumerate(SCHEDULE):
                guard()
                stem = f"{case}-{index}"
                save(stem+"-attempt.json", dict(case=case, n=n, nodes=nodes, shift=shift))
                row, arrays, scale = screen(snapshot, source[TARGET], reference,
                                            n, nodes, shift, scale, guard, counts)
                if case == "n6-shape-d100mm" and index == 0:
                    row["seed_replay"] = seed_replay(row["metrics"], source[SEED_RESULT]["metrics"])
                    row["checks_pass"] &= all(r["passed"] for r in row["seed_replay"].values())
                buffer = io.BytesIO()
                np.savez_compressed(buffer, **arrays)
                guard()
                save(stem+".npz", buffer.getvalue())
                row.update(case=case, arrays_sha256=sha256_file(output/(stem+".npz")),
                           existing_geometry_audit=dict(path=AUDIT, sha256=INPUTS[AUDIT],
                                                        case=case))
                save(stem+".json", row)
                report["rows"].append(row)
                guard()
                if not row["checks_pass"]:
                    raise ValueError("independent numerical screen failed; outputs retained")
        guard()
        report["completed"] = True
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    report["sources_after"] = fingerprints()
    report["sources_unchanged"] = report["sources_before"] == report["sources_after"]
    report["elapsed_s"] = time.monotonic()-started
    report["completed"] &= report["sources_unchanged"] and report["elapsed_s"] < SECONDS
    save("result.json", report)
    print(json.dumps(dict(output=str(output), completed=report["completed"],
                          rows=len(report["rows"]))))
    return 0 if report["completed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    raise SystemExit(run(parser.parse_args().output.resolve()))
