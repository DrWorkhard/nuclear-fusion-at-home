"""Independent saved-data admission of the registered clear-coil field starts.

Only NumPy/SciPy reconstruction and immutable evidence are used. No producer,
native field, VMEC solve, search or new physical target evaluation is invoked.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from fusion_baselines import clear_coil_field_audit as numerical
from fusion_baselines import coupled_coil_audit as frozen
from fusion_baselines.provenance import write_json_atomic

ROOT = Path(__file__).resolve().parents[1]
THREADS = {
    key: "1" for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")
}
SCOPE = dict(
    equilibrium_solves=0,
    search_calls=0,
    search_allowed=False,
    transfer_pass=False,
    step4_pass=False,
)
PENDING = dict(
    all_pass=False, startup_pass=False, physical_seed_pass=False, independent_audit_pass=False
)
CONSTRUCTION = dict(
    ncoil=256,
    nphi=64,
    ntheta=64,
    ninner=32,
    offset=0,
    nloop=256,
    geometry_nphi=128,
    geometry_ntheta=128,
    geometry_full_torus=True,
    geometry_offset=0,
)
INIT_WORK = dict(seed_A_calls=1, seed_A_points=256)
RAW_KEYS = {
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
require, finite, scalar = numerical.require, numerical.finite, numerical.scalar


def sources(root):
    from clear_coil_field_start_inputs import sources as bound_sources

    return bound_sources(root)


def typed_equal(actual, expected):
    if isinstance(expected, dict):
        return (
            isinstance(actual, dict)
            and set(actual) == set(expected)
            and all(typed_equal(actual[k], v) for k, v in expected.items())
        )
    if isinstance(expected, list):
        return (
            isinstance(actual, list)
            and len(actual) == len(expected)
            and all(typed_equal(a, b) for a, b in zip(actual, expected, strict=True))
        )
    return type(actual) is type(expected) and actual == expected


class Evidence:
    def __init__(self, opaque_json=()):
        self.references, self.documents, self.arrays = {}, {}, {}
        # Historical qualification metadata uses its own relative-path schema.
        # Its bytes remain pinned; sourcebinder separately exposes absolute pins.
        self.opaque_json = {str(self.check(ref)) for ref in opaque_json}

    def check(self, ref):
        require(
            isinstance(ref, dict) and set(ref) in ({"path", "sha256"}, {"path", "sha256", "bytes"}),
            "exact immutable byte reference",
        )
        require(
            type(ref["path"]) is str
            and Path(ref["path"]).is_absolute()
            and type(ref["sha256"]) is str
            and len(ref["sha256"]) == 64
            and all(c in "0123456789abcdef" for c in ref["sha256"]),
            "absolute SHA256 reference",
        )
        path = Path(ref["path"])
        if str(path) not in self.references:
            with path.open("rb") as stream:
                sha = hashlib.file_digest(stream, "sha256").hexdigest()
            self.references[str(path)] = dict(sha256=sha, bytes=path.stat().st_size)
        actual = self.references[str(path)]
        require(ref["sha256"] == actual["sha256"], f"changed evidence hash: {path}")
        if "bytes" in ref:
            require(
                type(ref["bytes"]) is int and ref["bytes"] == actual["bytes"],
                "changed evidence byte count",
            )
        return path

    def read(self, ref):
        path = self.check(ref)
        if str(path) not in self.documents:
            self.documents[str(path)] = json.loads(path.read_text())
        return self.documents[str(path)]

    def array(self, ref):
        path = self.check(ref)
        if str(path) not in self.arrays:
            with np.load(path, allow_pickle=False) as archive:
                self.arrays[str(path)] = {k: finite(archive[k]).copy() for k in archive.files}
        return self.arrays[str(path)]

    def bind(self, value, expanded=None, *, expand_json=True):
        expanded = set() if expanded is None else expanded
        if isinstance(value, dict):
            if "path" in value and "sha256" in value:
                path = self.check(value)
                if (
                    expand_json
                    and path.suffix == ".json"
                    and str(path) not in expanded
                    and str(path) not in self.opaque_json
                ):
                    expanded.add(str(path))
                    self.bind(self.read(value), expanded)
            else:
                for key, item in value.items():
                    self.bind(
                        item,
                        expanded,
                        expand_json=expand_json
                        and key not in ("source", "source_before", "source_after", "sources"),
                    )
        elif isinstance(value, list):
            for item in value:
                self.bind(item, expanded, expand_json=expand_json)


def close(actual, expected, label, *, rtol=5e-10, atol=1e-12):
    return numerical.close(actual, expected, label, rtol=rtol, atol=atol)


def indices(size):
    require(type(size) is int and size >= 64, "at least64 ordered field points")
    return np.linspace(0, size - 1, 64, dtype=int)


def relative_field(actual, independent, label):
    actual, independent = finite(actual), finite(independent)
    require(
        actual.shape == independent.shape and actual.shape == (64, 3), "64 complete vector checks"
    )
    denominator = float(abs(independent).max())
    require(denominator > 0, f"{label}: nonzero independent field/potential denominator")
    error = float(abs(actual - independent).max() / denominator)
    require(error <= 5e-10, f"{label}: direct relative field error {error}")
    return error


def direct_fields(snapshot, raw, ncoil):
    result = {}
    for prefix in ("boundary", "inner", "loop"):
        points = finite(raw[prefix + "_points"])
        at = indices(len(points))
        magnetic, potential = frozen.direct_field(snapshot, points[at], ncoil=ncoil)
        for key, expected in (("B", magnetic), ("A", potential)):
            name = prefix + "_" + key
            require(finite(raw[name]).shape == points.shape, "complete stored field/potential")
            result[name] = relative_field(raw[name][at], expected, name)
    return result


def prerequisites(binding, evidence):
    """Recheck named inherited admissions; never substitute a global any-pass."""
    geo, old = (
        evidence.read(binding["geometry"]["audit"]),
        evidence.read(binding["geometry"]["run"]),
    )
    require(
        geo["status"] == "completed"
        and geo["phase"] == "geometry_initialization"
        and all(
            geo[k] is True
            for k in (
                "all_pass",
                "arithmetic_and_source_pass",
                "all_twelve_sets_checked",
                "both_classes_pass",
                "geometry_pass",
            )
        )
        and geo["run"] == binding["geometry"]["run"]
        and geo["source"] == old["source"] == binding["geometry"]["source"],
        "complete source-bound accepted geometry predecessor",
    )
    require(
        len(geo["sets"]) == len(old["sets"]) == 12
        and geo["work"]["attempted_lps"] == 168
        and geo["work"]["original_lps"] == geo["work"]["repeated_lps"] == 84,
        "all12 original geometry sets and168 LPs",
    )
    require(
        typed_equal(
            binding["geometry"]["selected"], {f"n{n}": f"n{n}-shape-d100mm" for n in (6, 8)}
        )
        and geo["selected"] == binding["geometry"]["selected"],
        "preselected seeds unchanged",
    )
    seeds = {}
    for n in (6, 8):
        label = f"n{n}-shape-d100mm"
        record = binding["seeds"][label]
        at = record["geometry_report_index"]
        require(type(at) is int and 0 <= at < 12, "exact selected geometry index")
        report, source_set = geo["sets"][at], old["sets"][at]
        require(
            report["case"] == source_set["case"] == record["case"]
            and record["case"]["label"] == label
            and report["geometry_pass"] is True
            and report["available_geometry"] is True
            and record["snapshot"] == source_set["snapshot"],
            "individually accepted exact seed snapshot",
        )
        require(
            len(report["coils"]) == n
            and all(
                r["exact_repeat"] is True and r["available_geometry"] is True
                for r in report["coils"]
            ),
            "complete selected LP repeats",
        )
        seeds[label] = evidence.read(record["snapshot"])
        numerical.clear_geometry.validate_snapshot(seeds[label])
    block = evidence.read(binding["bounded_reference"]["audit"])
    reference = evidence.read(binding["bounded_reference"]["run"])
    require(
        block["status"] == "completed"
        and block["arithmetic_and_source_pass"] is True
        and block["bounded_reference_pass"] is True
        and block["all_pass"] is True
        and block["legacy_all_pass"] is False
        and block["legacy_sparse_pass"] is True
        and block["run"] == binding["bounded_reference"]["run"]
        and block["source"]
        == reference["source_before"]
        == reference["source_after"]
        == binding["bounded_reference"]["source"]
        and block["compared_quantities"] == 336,
        "separate positive block reference; original dense rejection preserved",
    )
    require(
        len(block["workers"]) == 4
        and all(r["passed"] is True for r in block["workers"])
        and len(block["legacy_workers"]) == 8
        and all(r["mathematical_pass"] is True for r in block["legacy_workers"])
        and sum(r["resource_pass"] is False for r in block["legacy_workers"]) == 3
        and all(
            r["passed"] is True for r in block["legacy_workers"] if r["case"]["backend"] == "sparse"
        ),
        "all individual new references and old Sparse admissions",
    )
    return seeds


def target(binding, case, evidence):
    label = case["target"]
    data = evidence.read(binding["targets"][label]["input"])
    numerical.boundary_input(data)
    require(
        data["mpol"] == 5
        and data["ntor"] == 10
        and data["ns_array"][-1] == 401
        and data["lfreeb"] is False
        and data["pres_scale"] == 0
        and data["curtor"] == 0,
        "original401 vacuum target input",
    )
    close(abs(scalar(data["phiedge"])), np.pi / 100, "fixed physical edge flux", rtol=0, atol=1e-15)
    normalization = binding["normalization"][label]
    archive = binding["target_archives"][label]
    require(archive["wout"] == binding["targets"][label]["wout"], "original archived target Wout")
    expected = [r for r in archive["fields"] if r["n"] == 64]
    require(
        typed_equal(normalization["archives"], expected),
        "exact three canonical64 archive references",
    )
    rows = [dict(row, arrays=evidence.array(row["arrays"])) for row in expected]
    targets = {n: numerical.archived_target(rows, n) for n in (32, 64)}
    require(
        normalization["B2_scale"] == targets[64]["B2_scale"] == targets[32]["B2_scale"],
        "exact unchanged canonical archived64 B2",
    )
    bphi = targets[64]["inner_target"].reshape(3, 64, 64, 3)[:, 0, :, 1]
    require(
        np.all(bphi != 0) and np.all(np.sign(bphi) == np.sign(bphi.flat[0])),
        "consistent nonzero toroidal field orientation at all archived phi0 points",
    )
    p, t = frozen.loop(data, 1024)
    area = float(0.5 * np.mean(p[:, 0] * t[:, 2] - p[:, 2] * t[:, 0]))
    require(np.isfinite(area) and area != 0, "nondegenerate signed target contour")
    flux = float(-np.sign(area) * np.sign(bphi.flat[0]) * abs(data["phiedge"]))
    return dict(input=data, targets=targets, target_flux=flux, B2_scale=normalization["B2_scale"])


def snapshot_identity(snapshot, row, case, geometry, binding, context, method):
    numerical.validate_snapshot(snapshot)
    require(
        snapshot["nbase"] == case["nbase"]
        and snapshot["order"] == case["order"]
        and snapshot["method"] == method
        and typed_equal(snapshot["construction"], CONSTRUCTION)
        and typed_equal(snapshot["initialization_work"], INIT_WORK),
        "exact construction snapshot identity",
    )
    require(
        snapshot["seed_geometry"] == geometry
        and snapshot["sources"] == binding["targets"][case["target"]],
        "unaltered admitted seed and target provenance",
    )
    require(
        np.array_equal(finite(snapshot["base_coefficients"]).ravel(), finite(row["x"])),
        "actual per-probe named snapshot coefficients",
    )
    require(
        snapshot["B2_scale"] == context["B2_scale"]
        and snapshot["target_flux"] == context["target_flux"],
        "frozen physical target normalization",
    )
    require(
        abs(scalar(snapshot["seed_unit_flux"])) > 1e-12
        and np.sign(snapshot["unit_flux"]) == np.sign(snapshot["seed_unit_flux"]),
        "nonzero original current orientation preserved",
    )
    if row["index"] in (0, 9):
        numerical.seed_identity(snapshot, geometry, binding["targets"][case["target"]])
        require(snapshot["seed_unit_flux"] == snapshot["unit_flux"], "exact initial seed unit flux")


def field_row(row, snapshot, context, level, evidence, *, method="N", diagnostic=False):
    require(row["status"] == "completed", "complete raw field operation")
    raw = evidence.array(row["arrays"])
    require(set(raw) == RAW_KEYS, "all and only declared stored field arrays")
    archived = context["targets"][level["ninner"]]
    require(
        all(np.array_equal(raw[key], archived[key]) for key in ("inner_points", "inner_target")),
        "exact active archived64 interior coordinates and vector target",
    )
    own = numerical.composed_metrics(
        snapshot, context["input"], raw, context["targets"][level["ninner"]], method, level
    )
    expected_metrics = set(own) - {"geometry", "mean_B", "raw_bn_rms", "raw_bn_max"} | {
        "frozen_scale"
    }
    require(
        set(row["metrics"]) == expected_metrics and row["metrics"]["frozen_scale"] is diagnostic,
        "complete normalization-aware native metrics",
    )
    for key in expected_metrics - {"frozen_scale"}:
        close(row["metrics"][key], own[key], "independent " + key)
    for key in ("scale", "B2_scale", "target_flux"):
        require(row["metrics"][key] == snapshot[key], "exact fixed physical " + key)
    require(row["metrics"]["current"] == 1e5 * snapshot["scale"], "actual common physical current")
    if not diagnostic:
        close(row["J"], own["J"], "independent composed objective")
        close(
            own["flux"], snapshot["target_flux"], "calibrated construction flux", rtol=1e-12, atol=0
        )
        close(
            own["unit_flux"], snapshot["unit_flux"], "same geometric unit flux", rtol=5e-10, atol=0
        )
    own["direct_errors"] = direct_fields(snapshot, raw, level["ncoil"])
    return dict(metrics=own, arrays=raw, snapshot=snapshot, status="completed")


def flux_grid(row, kind, snapshot, data, ncoil, evidence):
    require(row["status"] == "completed", "complete raw flux grid")
    raw = evidence.array(row["arrays"])
    if kind == "line":
        points, tangent = frozen.loop(data, row["ntheta"])
        expected = dict(points=points, tangents=tangent)
    else:
        points, normal = frozen.fan_area(data, row["nrho"], row["ntheta"])
        expected = dict(points=points, weighted_normals=normal)
    require(set(raw) == set(expected) | {"B", "A"}, "complete signed flux raw data")
    for key, value in expected.items():
        close(raw[key], value, "independent flux " + key, rtol=0, atol=5e-12)
    at = indices(len(points))
    b, a = frozen.direct_field(snapshot, points[at], ncoil=ncoil)
    errors = {
        key: relative_field(raw[key][at], value, "flux " + key)
        for key, value in (("B", b), ("A", a))
    }
    require(raw["B"].shape == raw["A"].shape == points.shape, "complete flux vector grids")
    value = (
        float(np.mean(np.sum(raw["A"] * tangent, axis=1)))
        if kind == "line"
        else float(np.sum(raw["B"] * normal))
    )
    close(row["flux"], value, "signed flux arithmetic")
    return dict(flux=value, direct_errors=errors)


def flux_checks(lines, areas, target_flux):
    """Explicit target, Stokes, angular and radial gates; no aggregate shortcut."""
    target_flux = scalar(target_flux)
    require(target_flux != 0 and len(lines) == 3 and len(areas) == 6, "all nine nonzero flux grids")
    values = finite(lines + areas)
    denominator = abs(target_flux)
    checks = []

    def check(kind, first, second, a, b):
        error = float(abs(a - b) / denominator)
        checks.append(
            dict(
                kind=kind,
                first=first,
                second=second,
                relative_error=error,
                passed=bool(error <= 1e-6),
            )
        )

    for i, value in enumerate(values):
        check("target", i, "target", value, target_flux)
    for r in range(2):
        for t in range(3):
            check("stokes", 3 + 3 * r + t, t, values[3 + 3 * r + t], values[t])
    for row, offset in (("line_angular", 0), ("area16_angular", 3), ("area32_angular", 6)):
        for i, j in ((0, 1), (1, 2), (0, 2)):
            check(row, offset + i, offset + j, values[offset + i], values[offset + j])
    for t in range(3):
        check("radial", 3 + t, 6 + t, values[3 + t], values[6 + t])
    return dict(values=values.tolist(), checks=checks, passed=all(r["passed"] for r in checks))


def flux_block(block, snapshot_ref, snapshot, context, ncoil, evidence):
    require(
        block["status"] == "completed"
        and type(block["ncoil"]) is int
        and block["ncoil"] == ncoil
        and block["snapshot"] == snapshot_ref
        and type(block["full_bundles"]) is int
        and block["full_bundles"] == 0,
        "fixed-current no-gradient flux block",
    )
    require(
        all(block[k] == snapshot[k] for k in ("scale", "B2_scale", "target_flux")),
        "fixed flux scales",
    )
    lines, areas = (
        [evidence.read(ref) for ref in block["lines"]],
        [evidence.read(ref) for ref in block["areas"]],
    )
    require(
        [r["ntheta"] for r in lines] == [256, 512, 1024]
        and [(r["nrho"], r["ntheta"]) for r in areas]
        == [(r, n) for r in (16, 32) for n in (256, 512, 1024)],
        "all three line and six fan grids in fixed order",
    )
    reports = [
        flux_grid(row, kind, snapshot, context["input"], ncoil, evidence)
        for kind, group in (("line", lines), ("area", areas))
        for row in group
    ]
    checks = flux_checks(
        [r["flux"] for r in reports[:3]], [r["flux"] for r in reports[3:]], snapshot["target_flux"]
    )
    return dict(ncoil=ncoil, grids=reports, **checks)


def flux_coil_comparison(first, second, target_flux):
    require(len(first["values"]) == len(second["values"]) == 9, "all corresponding flux grids")
    denominator = abs(scalar(target_flux))
    require(denominator > 0, "nonzero fixed target flux")
    checks = [
        dict(
            grid=i,
            relative_error=float(abs(a - b) / denominator),
            passed=bool(abs(a - b) / denominator <= 1e-6),
        )
        for i, (a, b) in enumerate(zip(first["values"], second["values"], strict=True))
    ]
    return dict(checks=checks, passed=all(r["passed"] for r in checks))


def physical_gates(snapshot, diagnostics, startup_pass):
    require(len(diagnostics) == 6, "all six mandatory physical diagnostic states")
    metrics = [r["metrics"] for r in diagnostics]

    def bounded(key, limit):
        return all(0 <= scalar(row[key]) <= limit for row in metrics)

    checks = dict(
        startup=startup_pass is True,
        normal_rms=bounded("normal_rms", 1e-4),
        normal_max=bounded("normal_max", 1e-3),
        vector_rms=bounded("vector_rms", 0.01),
        current=all(abs(scalar(row["current"])) <= 500000 for row in metrics)
        and all(abs(scalar(row["current"])) <= 500000 for row in snapshot["physical"]),
        lengths=all(np.all(finite(row["lengths"]) <= 3.5) for row in metrics),
        curvature=all(np.all(finite(row["kappa_max"]) <= 12) for row in metrics),
        coil_distance=all(scalar(row["coil_distance"]) >= 0.06 for row in metrics),
        plasma_distance=all(scalar(row["surface_distance"]) >= 0.08 for row in metrics),
    )
    return numerical.json_value(dict(checks=checks, physical_seed_pass=all(checks.values())))


def model_plan():
    base = {k: v for k, v in numerical.levels()[0].items() if k != "index"}
    return (
        [
            dict(id=f"qualification-{m}", kind="qualification", method=m, grid=base.copy())
            for m in ("N", "V")
        ]
        + [
            dict(
                id=f"diagnostic-{level['index']}",
                kind="diagnostic",
                method="N",
                level=level,
                grid={k: v for k, v in level.items() if k != "index"},
            )
            for level in numerical.levels()
        ]
        + [
            dict(id=f"flux-{n}", kind="flux", method="N", grid=dict(base, ncoil=n))
            for n in (256, 512)
        ]
    )


def operation_plan(spec, seed):
    identifier, kind = spec["id"], spec["kind"]
    if kind == "qualification":
        labels = (
            ["seed"]
            + [f"{d}-{h:g}-{s:+d}" for d in ("sin", "cos") for h in (1e-5, 5e-6) for s in (1, -1)]
            + ["seed-repeat"]
        )
        return [
            dict(
                operation_id=f"{identifier}-{i:02d}",
                model_id=identifier,
                kind=kind,
                index=i,
                label=label,
                method=spec["method"],
                x=x.tolist(),
            )
            for i, (label, x) in enumerate(
                zip(labels, numerical.qualification_points(seed), strict=True)
            )
        ]
    if kind == "diagnostic":
        return [
            dict(
                operation_id=identifier,
                model_id=identifier,
                kind=kind,
                index=spec["level"]["index"],
                level=spec["level"],
                x=seed.tolist(),
            )
        ]
    grids = [dict(form="line", ntheta=n) for n in (256, 512, 1024)] + [
        dict(form="area", nrho=r, ntheta=n) for r in (16, 32) for n in (256, 512, 1024)
    ]
    return [
        dict(
            operation_id=f"{identifier}-{g['form']}-"
            + (f"{g['nrho']}-" if g["form"] == "area" else "")
            + str(g["ntheta"]),
            model_id=identifier,
            kind=kind,
            index=i,
            ncoil=spec["grid"]["ncoil"],
            **g,
        )
        for i, g in enumerate(grids)
    ]


def expected_calls(spec, operation=None):
    if operation is None:
        return [("loop", "A", 256)]
    if spec["kind"] == "flux":
        n = operation["ntheta"] * operation.get("nrho", 1)
        return [("loop", q, n) for q in (("A", "B") if operation["form"] == "line" else ("B", "A"))]
    grid = spec["grid"]
    b, i = grid["nphi"] * grid["ntheta"], 3 * grid["ninner"] ** 2
    result = [("boundary", "B", b), ("inner", "B", i), ("loop", "A", 256)]
    if spec["kind"] == "qualification":
        result += [("boundary", "B_vjp", b), ("inner", "B_vjp", i), ("loop", "A_vjp", 256)]
    return result + [("boundary", "A", b), ("inner", "A", i), ("loop", "B", 256)]


def clock_value(value):
    require(
        type(value) in (int, float) and np.isfinite(value) and value >= 0,
        "finite nonnegative exact clock scalar",
    )
    return float(value)


def native_history(worker, models, seed, cell_start, cell_end, evidence):
    require(
        type(worker["admitted_native_requests"]) is int
        and worker["admitted_native_requests"] == 262
        and "native_denials" not in worker,
        "all262 requests admitted without budget denial",
    )
    events = [
        json.loads(line)
        for line in evidence.check(worker["native_events"]).read_text().splitlines()
    ]
    require(
        type(worker["native_event_records"]) is int
        and worker["native_event_records"] == len(events) == 524,
        "exact524 native attempt/outcome events",
    )
    require(
        typed_equal(evidence.read(worker["native_inflight"]), events[-1]),
        "last atomic native event identity",
    )
    cursor, previous, all_operations, all_attempts, initializations, native_total = (
        0,
        cell_start,
        [],
        [],
        [],
        [],
    )
    for model, spec in zip(models, model_plan(), strict=True):
        initialized = evidence.read(model["initialized"])
        init_start, init_end = [
            clock_value(initialized[k]) for k in ("started_monotonic", "ended_monotonic")
        ]
        require(previous <= init_start <= init_end <= cell_end, "serial timely initialization")
        require(
            model["status"] == initialized["status"] == "completed"
            and all(typed_equal(initialized.get(k), v) for k, v in spec.items())
            and initialized["model_id"] == spec["id"]
            and initialized["initialization_operation_id"] == "init:" + spec["id"]
            and typed_equal(initialized["native_range"], [0, 1]),
            "exact registered completed model initialization",
        )
        require(
            all(typed_equal(model[k], v) for k, v in initialized.items()),
            "final model preserves initialized metadata",
        )
        model_attempt = evidence.read(initialized["attempt"])
        require(
            typed_equal(
                model_attempt,
                dict(
                    spec,
                    case=worker["case"],
                    operation_id="init:" + spec["id"],
                    seed_geometry=initialized["seed_geometry"],
                    started_monotonic=initialized["started_monotonic"],
                    B2_scale=initialized["B2_scale"],
                ),
            ),
            "persisted pre-constructor attempt",
        )
        initializations.append(initialized)
        local_calls = []

        def consume(
            operation_id, requests, start, end, model_id=spec["id"], local_calls=local_calls
        ):
            nonlocal cursor, previous
            for field, quantity, points in requests:
                require(cursor + 2 <= len(events), "complete native request pair")
                attempted, completed = events[cursor : cursor + 2]
                for record, status in ((attempted, "attempted"), (completed, "completed")):
                    require(
                        type(record["append_index"]) is int
                        and record["append_index"] == cursor + (status == "completed")
                        and record["model_id"] == model_id
                        and record["operation_id"] == operation_id,
                        "exact global append and model/operation native identity",
                    )
                first, last = attempted["event"], completed["event"]
                start_native = clock_value(first["started_monotonic"])
                stop_native = clock_value(last["completed_monotonic"])
                expected = dict(
                    index=len(local_calls),
                    field=field,
                    quantity=quantity,
                    points=points,
                    status="attempted",
                    started_monotonic=first["started_monotonic"],
                    native_started=False,
                    native_completed=False,
                )
                require(
                    typed_equal(first, expected)
                    and typed_equal(
                        last,
                        dict(
                            expected,
                            status="completed",
                            native_started=True,
                            native_completed=True,
                            completed_monotonic=last["completed_monotonic"],
                        ),
                    ),
                    "exact native attempted/completed schemas and quantities",
                )
                require(
                    start <= start_native <= stop_native <= end and previous <= start_native,
                    "native request clocks within operation and serial globally",
                )
                local_calls.append(last)
                previous, cursor = stop_native, cursor + 2

        consume("init:" + spec["id"], expected_calls(spec), init_start, init_end)
        require(
            typed_equal(initialized["initialization_native_calls"], local_calls),
            "one actual initial A request",
        )
        previous = init_end
        expected_ops = operation_plan(spec, seed)
        require(len(model["operations"]) == len(expected_ops), "all registered model operations")
        summaries = []
        for reference, expected in zip(model["operations"], expected_ops, strict=True):
            row = evidence.read(reference)
            require(
                row["status"] == "completed"
                and all(typed_equal(row[k], v) for k, v in expected.items()),
                "exact immutable operation state and order",
            )
            start, end = [clock_value(row[k]) for k in ("started_monotonic", "ended_monotonic")]
            require(previous <= start <= end <= cell_end, "serial timely operation")
            native_start, event_start = len(local_calls), cursor
            attempt = evidence.read(row["attempt"])
            require(
                typed_equal(
                    attempt,
                    dict(
                        expected,
                        started_monotonic=row["started_monotonic"],
                        native_start=native_start,
                        native_event_start=event_start,
                    ),
                ),
                "persisted exact operation attempt and prefixes",
            )
            consume(expected["operation_id"], expected_calls(spec, expected), start, end)
            require(
                typed_equal(row["native_range"], [native_start, len(local_calls)])
                and typed_equal(row["native_event_range"], [event_start, cursor]),
                "exact local/global native request ranges",
            )
            previous = end
            all_operations.append(reference)
            all_attempts.append(row["attempt"])
            summaries.append(
                {k: row[k] for k in ("operation_id", "kind", "status", "native_range")}
            )
        require(
            typed_equal(model["operation_summaries"], summaries)
            and typed_equal(model["native_calls"], local_calls),
            "complete exact final native model ledger",
        )
        require(
            previous <= clock_value(model["model_ended_monotonic"]) <= cell_end, "timely model end"
        )
        previous = clock_value(model["model_ended_monotonic"])
        native_total.extend(local_calls)
    require(
        cursor == len(events)
        and typed_equal(worker["operations"], all_operations)
        and typed_equal(worker["operation_attempts"], all_attempts)
        and typed_equal(worker["model_attempts"], [r["attempt"] for r in initializations]),
        "complete whole-cell operation and model attempt prefixes",
    )
    summary = dict(
        native_requests=len(native_total),
        completed_requests=len(native_total),
        values=sum(r["quantity"] in ("A", "B") for r in native_total),
        vjps=sum(r["quantity"] in ("A_vjp", "B_vjp") for r in native_total),
        initialization_requests=len(models),
        full_bundles=20,
        equilibrium_solves=0,
        search_calls=0,
    )
    expected = dict(
        native_requests=262,
        completed_requests=262,
        values=202,
        vjps=60,
        initialization_requests=10,
        full_bundles=20,
        equilibrium_solves=0,
        search_calls=0,
    )
    require(
        typed_equal(summary, expected) and typed_equal(worker["work"], expected),
        "all262 actual requested native calls",
    )
    return dict(passed=True, events=cursor, work=summary), initializations


def process_audit(result, case, binding, evidence):
    require(
        result["status"] == "completed" and typed_equal(result["case"], case),
        "completed expected physical cell",
    )
    worker, process, config, launch = [
        evidence.read(result[k]) for k in ("worker", "process", "config", "launch")
    ]
    folder = Path(result["worker"]["path"]).parent
    require(
        config["output"] == str(folder)
        and type(config["parent_pid"]) is int
        and config["parent_pid"] > 0
        and typed_equal(config["case"], case)
        and typed_equal(config["source"], binding),
        "bound owned worker configuration",
    )
    require(
        worker["status"] == "completed"
        and worker["kind"] == "clear-coil-field-start-cell"
        and type(worker["schema_version"]) is int
        and worker["schema_version"] == 1
        and typed_equal(worker["case"], case)
        and typed_equal(worker["source_before"], binding)
        and typed_equal(worker["source_after"], binding)
        and typed_equal(worker["threads"], THREADS)
        and typed_equal(worker["scope"], dict(SCOPE, **PENDING)),
        "unchanged scoped worker identity",
    )
    start, end, elapsed, parent = map(
        clock_value,
        (
            config["started_monotonic"],
            worker["ended_monotonic"],
            worker["elapsed_seconds"],
            process["elapsed_seconds"],
        ),
    )
    require(
        type(process["returncode"]) is int
        and process["returncode"] == 0
        and process["timed_out"] is False
        and not process.get("error_type")
        and 0 <= elapsed <= end - start <= parent < 1800,
        "timely parent and worker with exact integer exit0",
    )
    require(
        typed_equal(launch["case"], case)
        and launch["started_monotonic"] == start
        and launch["command"][-2:] == ["--worker", str(folder / "config.json")],
        "bound worker launch",
    )
    require(
        all(
            type(record["minimum_observed_free_bytes"]) is int
            and record["minimum_observed_free_bytes"] >= 2 * 1024**3
            for record in (worker, process)
        ),
        "both worker and parent observed disk reserves",
    )
    retained = result["retained"]
    require(
        len({r["path"] for r in retained}) == len(retained)
        and all(Path(r["path"]).is_relative_to(folder) for r in retained),
        "unique owned retained evidence",
    )
    for key in ("worker", "config", "launch", "process"):
        require(result[key] in retained, "all completed process evidence retained")
    checkpoint_refs = [r for r in retained if Path(r["path"]) == folder / "checkpoint.json"]
    require(len(checkpoint_refs) == 1, "single durable last-successful checkpoint")
    require(
        typed_equal(
            evidence.read(checkpoint_refs[0]),
            dict(
                models=worker["models"][:-1],
                operations=worker["operations"],
                qualification=worker["qualification"],
                diagnostics=worker["diagnostics"],
                flux=worker["flux"][:-1],
                native_event_records=524,
            ),
        ),
        "exact final pre-model-commit operation checkpoint",
    )
    plan_refs = [r for r in retained if Path(r["path"]) == folder / "plan.json"]
    require(len(plan_refs) == 1, "single recorded immutable model/operation plan")
    first_model = evidence.read(worker["models"][0])
    expected_plan = dict(
        models=model_plan(),
        operations=[
            op
            for spec in model_plan()
            for op in operation_plan(spec, finite(first_model["seed_x"]))
        ],
    )
    require(
        typed_equal(evidence.read(plan_refs[0]), expected_plan), "exact pre-execution fixed plan"
    )
    return worker, dict(
        started=start,
        ended=end,
        parent_ended=start + parent,
        worker_seconds=elapsed,
        parent_seconds=parent,
    )


def cell_audit(result, case, binding, geometry, context, evidence):
    worker, clock = process_audit(result, case, binding, evidence)
    seed = finite(geometry["base_coefficients"]).ravel()
    require(len(worker["models"]) == 10, "ten separately initialized models")
    models = [evidence.read(ref) for ref in worker["models"]]
    work, initializations = native_history(
        worker, models, seed, clock["started"], clock["ended"], evidence
    )
    for initialized in initializations:
        require(
            initialized["seed_geometry"] == binding["seeds"][case["seed_label"]]["snapshot"]
            and np.array_equal(finite(initialized["seed_x"]), seed)
            and initialized["names"] == geometry["names"]
            and initialized["B2_scale"] == context["B2_scale"]
            and initialized["target_flux"] == context["target_flux"]
            and abs(scalar(initialized["seed_unit_flux"])) > 1e-12
            and typed_equal(initialized["initialization_work"], INIT_WORK),
            "actual named admitted geometry before initial A",
        )
    require(
        set(worker["qualification"]) == {"N", "V"}
        and len(worker["diagnostics"]) == 6
        and len(worker["flux"]) == 2,
        "complete two-method/six-grid/two-flux matrix",
    )
    qualifications, seed_rows, snapshots = {}, {}, {}
    for at, method in enumerate(("N", "V")):
        refs = worker["qualification"][method]
        require(
            typed_equal(refs, models[at]["operations"]), "qualification rows bind correct model"
        )
        rows = [evidence.read(ref) for ref in refs]
        own, values = [], []
        for row in rows:
            snapshot = evidence.read(row["snapshot"])
            snapshot_identity(snapshot, row, case, geometry, binding, context, method)
            require(
                snapshot["seed_unit_flux"] == initializations[at]["seed_unit_flux"],
                "original exact initialized seed flux",
            )
            checked = field_row(
                row, snapshot, context, numerical.levels()[0], evidence, method=method
            )
            own.append(checked)
            values.append(checked["metrics"]["J"])
        fd = numerical.derivative_checks(rows, seed, values)
        require(
            typed_equal(own[0]["snapshot"], own[9]["snapshot"])
            and all(np.array_equal(own[0]["arrays"][k], own[9]["arrays"][k]) for k in RAW_KEYS),
            "exact repeated full physical seed state",
        )
        qualifications[method] = dict(
            derivatives=fd, rows=[r["metrics"] for r in own], passed=fd["passed"]
        )
        seed_rows[method] = dict(rows[0], arrays=own[0]["arrays"], snapshot=own[0]["snapshot"])
        snapshots[method] = own[0]["snapshot"]
    identity = numerical.physical_identity(seed_rows["N"], seed_rows["V"])
    seed_identity_report = evidence.read(worker["seed_identity"])
    nref = evidence.read(worker["qualification"]["N"][0])["snapshot"]
    require(
        worker["snapshot"] == nref
        and typed_equal(
            seed_identity_report,
            dict(
                status="completed",
                passed=True,
                normal=worker["qualification"]["N"][0],
                vector=worker["qualification"]["V"][0],
                compared_arrays=sorted(RAW_KEYS),
                snapshot=nref,
            ),
        ),
        "unchanged original N-seed frozen source",
    )
    snapshot = snapshots["N"]
    for initialized in initializations:
        if initialized["grid"]["ncoil"] == 256:
            close(
                initialized["seed_unit_flux"],
                snapshot["unit_flux"],
                "all256-coil initial fluxes match original seed",
                atol=0,
            )
    diagnostics = []
    for i, (ref, level) in enumerate(zip(worker["diagnostics"], numerical.levels(), strict=True)):
        require(models[2 + i]["operations"] == [ref], "diagnostic source model")
        row = evidence.read(ref)
        require(
            typed_equal(row["level"], level)
            and row["snapshot"] == nref
            and np.array_equal(finite(row["x"]), seed)
            and all(row[k] == snapshot[k] for k in ("scale", "B2_scale", "target_flux")),
            "frozen diagnostic state and current",
        )
        checked = field_row(row, snapshot, context, level, evidence, diagnostic=True)
        close(
            initializations[2 + i]["seed_unit_flux"],
            checked["metrics"]["unit_flux"],
            "own-resolution initial unit flux",
            atol=0,
        )
        diagnostics.append(dict(status="completed", level=level, metrics=checked["metrics"]))
    refinement = numerical.refinement_checks(diagnostics)
    flux = []
    for i, ncoil in enumerate((256, 512)):
        block = evidence.read(worker["flux"][i])
        require(
            block["model"] == worker["models"][8 + i]
            and block["model_id"] == models[8 + i]["id"]
            and block["lines"] + block["areas"] == models[8 + i]["operations"],
            "all flux operations bind own source model",
        )
        for ref in block["lines"] + block["areas"]:
            row = evidence.read(ref)
            require(
                row["snapshot"] == nref
                and all(row[k] == snapshot[k] for k in ("scale", "B2_scale", "target_flux")),
                "every flux grid freezes original N-seed current",
            )
        report = flux_block(block, nref, snapshot, context, ncoil, evidence)
        close(
            initializations[8 + i]["seed_unit_flux"],
            report["values"][0] / snapshot["scale"],
            "flux-model own-resolution initialization",
            atol=0,
        )
        flux.append(report)
    cross = flux_coil_comparison(*flux, snapshot["target_flux"])
    startup = bool(
        all(r["passed"] for r in qualifications.values())
        and identity["passed"]
        and refinement["passed"]
        and all(r["passed"] for r in flux)
        and cross["passed"]
    )
    physical = physical_gates(snapshot, diagnostics, startup)
    return dict(
        status="completed",
        case=case,
        arithmetic_and_source_pass=True,
        work=work,
        clock=clock,
        qualification=qualifications,
        identity=identity,
        diagnostics=diagnostics,
        refinement=refinement,
        flux=flux,
        flux_coil_comparison=cross,
        direct_point_reconstructions=96,
        direct_field_comparisons=192,
        startup_pass=startup,
        **physical,
        **SCOPE,
    )


def audit(run, root=ROOT):
    current = sources(root)
    binding = run["source_before"]
    evidence = Evidence(
        opaque_json=[current["primitives_qualification"], binding["primitives_qualification"]]
    )
    for value in (current, binding):
        evidence.bind(value, expand_json=False)
    # Expand current raw runs, not a graph of historical source-audit internals.
    for name in ("geometry", "bounded_reference"):
        evidence.bind(binding[name]["run"])
    evidence.bind(run)
    require(
        type(run["schema_version"]) is int
        and run["schema_version"] == 1
        and run["kind"] == "clear-coil-field-start"
        and run["status"] == "completed",
        "complete separate startup-study schema",
    )
    require(
        typed_equal(binding, run["source_after"])
        and run["source_unchanged"] is True
        and typed_equal(
            {k: v for k, v in binding.items() if k != "repository"},
            {k: v for k, v in current.items() if k != "repository"},
        ),
        "unchanged execution/current numerical sources; only later root Git metadata may differ",
    )
    require(
        all(typed_equal(run[k], v) for k, v in dict(SCOPE, **PENDING).items())
        and run["admission_status"] == "pending-independent-audit"
        and type(run["producer_complete"]) is bool,
        "producer cannot issue independent or physical admission",
    )
    require(
        typed_equal(run["matrix"], numerical.physical_cases())
        and typed_equal(binding["matrix"], numerical.physical_cases())
        and len(run["rows"]) == 4,
        "all four registered physical cells",
    )
    require(
        typed_equal(
            run["limits"],
            dict(
                wall_seconds=1800.0,
                parent_poll_seconds=0.5,
                termination_grace_seconds=5,
                start_reserve_bytes=3 * 1024**3,
                live_reserve_bytes=2 * 1024**3,
            ),
        ),
        "unchanged parent wall and disk policy",
    )
    geometries = prerequisites(binding, evidence)
    contexts = {
        label: target(
            binding, next(c for c in numerical.physical_cases() if c["target"] == label), evidence
        )
        for label in ("reference", "selected")
    }
    reports = []
    previous = 0.0
    for i, (reference, case) in enumerate(
        zip(run["rows"], numerical.physical_cases(), strict=True)
    ):
        result = evidence.read(reference)
        require(
            type(result["index"]) is int
            and result["index"] == i
            and typed_equal(result["case"], case),
            "ordered registered physical cell",
        )
        try:
            report = cell_audit(
                result,
                case,
                binding,
                geometries[case["seed_label"]],
                contexts[case["target"]],
                evidence,
            )
            require(report["clock"]["started"] >= previous, "serial physical workers")
            previous = report["clock"]["parent_ended"]
        except Exception as error:
            report = dict(
                status="error",
                case=case,
                arithmetic_and_source_pass=False,
                startup_pass=False,
                physical_seed_pass=False,
                error=f"{type(error).__name__}: {error}",
                **SCOPE,
            )
            histories = [
                r
                for r in result.get("retained", [])
                if Path(r["path"]).name == "native-events.jsonl"
            ]
            if len(histories) == 1:
                # Observations from an incomplete ledger are bounds, never an
                # assertion that an attempted/pre-dispatch call did zero work.
                try:
                    events = [
                        json.loads(line)
                        for line in evidence.check(histories[0]).read_text().splitlines()
                    ]
                    attempted = {
                        (r["model_id"], r["event"]["index"])
                        for r in events
                        if r["event"].get("status") == "attempted"
                    }
                    returned = {
                        (r["model_id"], r["event"]["index"])
                        for r in events
                        if r["event"].get("status") == "completed"
                    }
                    report["retained_native_observations"] = dict(
                        event_records=len(events),
                        observed_attempted_requests=len(attempted),
                        observed_completed_requests=len(returned),
                        not_confirmed_complete=len(attempted - returned),
                        authoritative_complete_count=False,
                        unrecorded_native_work_not_excluded=True,
                    )
                except Exception as ledger_error:
                    report["retained_native_observations"] = dict(
                        error=str(ledger_error), authoritative_complete_count=False
                    )
        reports.append(report)
    complete = all(r["arithmetic_and_source_pass"] is True for r in reports)
    startup = bool(complete and all(r["startup_pass"] is True for r in reports))
    physical = bool(startup and all(r["physical_seed_pass"] is True for r in reports))
    return numerical.json_value(
        dict(
            status="completed",
            source=binding,
            auditor_repository=current["repository"],
            arithmetic_and_source_pass=complete,
            startup_pass=startup,
            physical_seed_pass=physical,
            all_pass=startup,
            independent_audit_pass=startup,
            cells=reports,
            verified_reference_files=len(evidence.references),
            **SCOPE,
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(
        args.run.is_absolute() and not args.output.exists(), "absolute saved run and fresh output"
    )
    result = dict(status="error", arithmetic_and_source_pass=False, **PENDING, **SCOPE)
    try:
        result.update(audit(json.loads(args.run.read_text())))
    except Exception as error:
        result["error"] = f"{type(error).__name__}: {error}"
    with args.run.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    result["run"] = dict(path=str(args.run), sha256=digest, bytes=args.run.stat().st_size)
    result = numerical.json_value(result)
    json.dumps(result, allow_nan=False)
    write_json_atomic(args.output, result)
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "status",
                    "arithmetic_and_source_pass",
                    "startup_pass",
                    "physical_seed_pass",
                )
            }
        ),
        flush=True,
    )
    return 0 if result["startup_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
