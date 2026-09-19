"""Synthetic source/accounting/field gates; no project field/native evaluation."""

import copy
import hashlib
import json
from pathlib import Path

import audit_clear_coil_field_start as audit
import numpy as np
import pytest

from fusion_baselines import clear_coil_field_audit as numerical
from fusion_baselines import coupled_coil_audit as frozen


def ref(path):
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def save(path, document):
    path.write_text(json.dumps(document, allow_nan=False))
    return ref(path)


def save_arrays(path, arrays):
    np.savez_compressed(path, **arrays)
    return ref(path)


def torus():
    return dict(
        lasym=False,
        nfp=2,
        mpol=5,
        ntor=10,
        ns_array=[8, 16, 401],
        lfreeb=False,
        pres_scale=0.0,
        curtor=0.0,
        phiedge=np.pi / 100,
        rbc=[dict(m=0, n=0, value=1.0), dict(m=1, n=0, value=0.1)],
        zbs=[dict(m=1, n=0, value=0.1)],
    )


def uniform_field(points):
    points = np.asarray(points)
    magnetic = np.broadcast_to([0.0, 1.0, 0.0], points.shape).copy()
    potential = np.cross(magnetic, points) / 2
    return magnetic, potential


def test_max_component_relative_field_has_no_absolute_escape():
    independent = np.ones((64, 3)) * 1e-20
    assert audit.relative_field(independent.copy(), independent, "tiny") == 0
    changed = independent.copy()
    changed[63, 2] += 1e-25
    with pytest.raises(ValueError, match="relative field"):
        audit.relative_field(changed, independent, "tiny")
    with pytest.raises(ValueError, match="denominator"):
        audit.relative_field(np.zeros((64, 3)), np.zeros((64, 3)), "zero")


def test_every_boundary_inner_loop_B_and_A_is_checked(monkeypatch):
    raw = {}
    seen = []
    for prefix, size in (("boundary", 128), ("inner", 256), ("loop", 256)):
        points = np.column_stack((1 + np.arange(size) / size, np.zeros(size), np.ones(size)))
        b, a = uniform_field(points)
        raw.update({prefix + "_points": points, prefix + "_B": b, prefix + "_A": a})

    def direct(snapshot, points, ncoil):
        seen.append((len(points), ncoil))
        return uniform_field(points)

    monkeypatch.setattr(frozen, "direct_field", direct)
    assert len(audit.direct_fields({}, raw, 512)) == 6
    assert seen == [(64, 512)] * 3
    raw["inner_A"][-1, 0] += 0.1
    with pytest.raises(ValueError, match="inner_A"):
        audit.direct_fields({}, raw, 512)


def test_flux_full_signed_stokes_angular_radial_and_coil_checks(tmp_path, monkeypatch):
    monkeypatch.setattr(
        frozen, "direct_field", lambda snapshot, points, ncoil: uniform_field(points)
    )
    data = torus()
    snapshot = dict(scale=1.0, B2_scale=1.0, target_flux=-np.pi / 100)
    source = save(tmp_path / "source.json", snapshot)
    lines, areas = [], []
    for n in (256, 512, 1024):
        p, t = frozen.loop(data, n)
        b, a = uniform_field(p)
        value = float(np.mean(np.sum(a * t, axis=1)))
        arrays = save_arrays(tmp_path / f"line{n}.npz", dict(points=p, tangents=t, B=b, A=a))
        lines.append(
            save(
                tmp_path / f"line{n}.json",
                dict(status="completed", ntheta=n, arrays=arrays, flux=value),
            )
        )
    for r in (16, 32):
        for n in (256, 512, 1024):
            p, w = frozen.fan_area(data, r, n)
            b, a = uniform_field(p)
            value = float(np.sum(b * w))
            arrays = save_arrays(
                tmp_path / f"fan{r}-{n}.npz", dict(points=p, weighted_normals=w, B=b, A=a)
            )
            areas.append(
                save(
                    tmp_path / f"fan{r}-{n}.json",
                    dict(status="completed", nrho=r, ntheta=n, arrays=arrays, flux=value),
                )
            )
    block = dict(
        status="completed",
        ncoil=256,
        snapshot=source,
        full_bundles=0,
        lines=lines,
        areas=areas,
        **snapshot,
    )
    report = audit.flux_block(block, source, snapshot, dict(input=data), 256, audit.Evidence())
    assert report["passed"] is True
    assert len(report["grids"]) == 9
    counts = {
        kind: sum(r["kind"] == kind for r in report["checks"])
        for kind in {r["kind"] for r in report["checks"]}
    }
    assert counts == dict(
        target=9, stokes=6, line_angular=3, area16_angular=3, area32_angular=3, radial=3
    )
    assert audit.flux_coil_comparison(report, report, snapshot["target_flux"])["passed"] is True
    changed = copy.deepcopy(report)
    changed["values"][8] += 1e-6
    cross = audit.flux_coil_comparison(report, changed, snapshot["target_flux"])
    assert len(cross["checks"]) == 9 and cross["passed"] is False


def test_explicit_pair_gates_cannot_hide_opposite_deviations():
    target = 1.0
    lines = [1.0, 1.0, 1.0]
    areas = [1.0 - 0.75e-6, 1.0, 1.0, 1.0 + 0.75e-6, 1.0, 1.0]
    report = audit.flux_checks(lines, areas, target)
    assert all(r["passed"] for r in report["checks"] if r["kind"] in ("target", "stokes"))
    assert report["passed"] is False
    assert not next(r for r in report["checks"] if r["kind"] == "radial")["passed"]
    report = audit.flux_checks([1.0 - 0.75e-6, 1.0 + 0.75e-6, 1.0], [1.0] * 6, target)
    assert any(not r["passed"] for r in report["checks"] if r["kind"] == "line_angular")


@pytest.mark.parametrize("level", range(6))
@pytest.mark.parametrize(
    "key,bad",
    [
        ("normal_rms", 1.001e-4),
        ("normal_max", 1.001e-3),
        ("vector_rms", 0.01001),
        ("current", 500001.0),
        ("coil_distance", 0.0599),
        ("surface_distance", 0.0799),
    ],
)
def test_physical_gate_checks_all_six_levels_separately(level, key, bad):
    metrics = dict(
        normal_rms=0.0,
        normal_max=0.0,
        vector_rms=0.0,
        current=1e5,
        lengths=[2.0],
        kappa_max=[5.0],
        coil_distance=0.07,
        surface_distance=0.09,
    )
    rows = [dict(metrics=copy.deepcopy(metrics)) for _ in range(6)]
    snapshot = dict(physical=[dict(current=1e5)])
    assert audit.physical_gates(snapshot, rows, True)["physical_seed_pass"] is True
    rows[level]["metrics"][key] = bad
    assert audit.physical_gates(snapshot, rows, True)["physical_seed_pass"] is False


def test_large_physical_error_does_not_relabel_numerical_startup():
    row = dict(
        normal_rms=0.2,
        normal_max=0.4,
        vector_rms=0.9,
        current=1e5,
        lengths=[2.0],
        kappa_max=[5.0],
        coil_distance=0.07,
        surface_distance=0.09,
    )
    result = audit.physical_gates(dict(physical=[dict(current=1e5)]), [dict(metrics=row)] * 6, True)
    assert result["checks"]["startup"] is True
    assert result["physical_seed_pass"] is False


@pytest.mark.parametrize(
    "value", [np.array([1j]), np.array([True]), np.array(["1"]), np.array([np.nan])]
)
def test_array_loader_rejects_nonreal_or_nonfinite_data(tmp_path, value):
    reference = save_arrays(tmp_path / "bad.npz", dict(value=value))
    with pytest.raises(ValueError):
        audit.Evidence().array(reference)


def test_references_detect_content_bytes_and_alias_mutations(tmp_path):
    reference = save(tmp_path / "data.json", dict(x=1))
    evidence = audit.Evidence()
    evidence.bind(reference)
    with pytest.raises(ValueError, match="hash"):
        evidence.bind(dict(reference, sha256="0" * 64))
    with pytest.raises(ValueError, match="byte"):
        evidence.bind(dict(reference, bytes=True))
    with pytest.raises(ValueError, match="absolute"):
        evidence.bind(dict(reference, path="relative.json"))


def test_scalar_normalization_has_no_numpy_boolean_serialization_gap():
    result = numerical.json_value(
        dict(passed=np.bool_(True), count=np.int64(4), error=np.float64(0.1))
    )
    assert json.loads(json.dumps(result, allow_nan=False)) == dict(passed=True, count=4, error=0.1)


def test_source_metadata_is_opaque_but_raw_json_graph_is_transitive(tmp_path):
    wrong = dict(path=str(tmp_path / "historically-versioned-code.py"), sha256="0" * 64)
    metadata = save(tmp_path / "old-source-audit.json", dict(source_code=wrong))
    qualification = save(
        tmp_path / "qualification.json", dict(source=dict(path="old-relative.py", sha256="0" * 64))
    )
    raw = save_arrays(tmp_path / "raw.npz", dict(value=np.ones(3)))
    nested = save(tmp_path / "nested.json", dict(arrays=raw))
    run = dict(source=dict(audit=metadata, qualification=qualification), rows=[nested])
    evidence = audit.Evidence(opaque_json=[qualification])
    evidence.bind(run)
    assert raw["path"] in evidence.references
    assert metadata["path"] in evidence.references
    assert wrong["path"] not in evidence.references
    with pytest.raises(ValueError, match="hash"):
        evidence.bind(dict(source=dict(audit=dict(metadata, sha256="0" * 64))))
    Path(raw["path"]).write_bytes(b"corrupted")
    with pytest.raises(ValueError, match="hash"):
        audit.Evidence().bind(run)


@pytest.fixture(scope="module")
def ledger_fixture(tmp_path_factory):
    # Actual guarded producer/CountedField integration with explicitly fake
    # fields; native_history remains entirely independent of producer checks.
    from test_clear_coil_field_start_workflow import run_fake

    directory = tmp_path_factory.mktemp("startup-ledger-producer")
    with pytest.MonkeyPatch.context() as monkeypatch:
        output, code = run_fake(monkeypatch, directory)
    assert code == 0
    worker = json.loads((output / "worker.json").read_text())
    config = json.loads((output / "config.json").read_text())
    return worker, config, output


def audit_ledger(fixture, evidence=None, worker=None):
    document, config, _ = fixture
    evidence = audit.Evidence() if evidence is None else evidence
    worker = document if worker is None else worker
    models = [evidence.read(reference) for reference in worker["models"]]
    seed = np.asarray(models[0]["seed_x"])
    return audit.native_history(
        worker, models, seed, config["started_monotonic"], worker["ended_monotonic"], evidence
    )


def test_actual_fake_producer_all262_native_requests_reconstructed(ledger_fixture):
    report, initialized = audit_ledger(ledger_fixture)
    assert report["passed"] is True and report["events"] == 524
    assert report["work"] == dict(
        native_requests=262,
        completed_requests=262,
        values=202,
        vjps=60,
        initialization_requests=10,
        full_bundles=20,
        equilibrium_solves=0,
        search_calls=0,
    )
    assert len(initialized) == 10 and [m["model_id"] for m in initialized] == [
        s["id"] for s in audit.model_plan()
    ]


@pytest.mark.parametrize(
    "mutation",
    [
        "append",
        "model",
        "operation",
        "local_index",
        "points",
        "quantity",
        "field",
        "native_started",
        "native_completed",
        "clock_before",
        "clock_after",
        "clock_reverse",
        "missing",
    ],
)
def test_native_event_mutations_fail_closed(ledger_fixture, tmp_path, mutation):
    worker = copy.deepcopy(ledger_fixture[0])
    events = [
        json.loads(line) for line in Path(worker["native_events"]["path"]).read_text().splitlines()
    ]
    end = events[1]
    if mutation == "append":
        end["append_index"] = True
    elif mutation == "model":
        end["model_id"] = "qualification-V"
    elif mutation == "operation":
        end["operation_id"] = "qualification-N-00"
    elif mutation == "local_index":
        end["event"]["index"] = 1
    elif mutation == "points":
        end["event"]["points"] = 128
    elif mutation == "quantity":
        end["event"]["quantity"] = "A_vjp"
    elif mutation == "field":
        end["event"]["field"] = "inner"
    elif mutation == "native_started":
        end["event"]["native_started"] = False
    elif mutation == "native_completed":
        end["event"]["native_completed"] = 1
    elif mutation == "clock_before":
        events[0]["event"]["started_monotonic"] = 0.0
    elif mutation == "clock_after":
        end["event"]["completed_monotonic"] += 10000
    elif mutation == "clock_reverse":
        end["event"]["completed_monotonic"] = events[0]["event"]["started_monotonic"] - 1.0
    elif mutation == "missing":
        events.pop()
    path = tmp_path / "events.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in events))
    worker["native_events"] = ref(path)
    with pytest.raises(ValueError):
        audit_ledger(ledger_fixture, worker=worker)


def overlay(evidence, reference):
    value = copy.deepcopy(evidence.read(reference))
    evidence.documents[reference["path"]] = value
    return value


@pytest.mark.parametrize(
    "kind",
    [
        "model_seed_calls",
        "init_range",
        "op_range",
        "event_range",
        "attempt_index",
        "attempt_prefix",
        "duplicate_ops",
        "missing_model",
        "claimed_work",
    ],
)
def test_full_model_and_operation_prefix_guards(ledger_fixture, kind):
    worker = copy.deepcopy(ledger_fixture[0])
    evidence = audit.Evidence()
    model = overlay(evidence, worker["models"][0])
    if kind == "model_seed_calls":
        model["initialization_native_calls"] *= 2
    elif kind == "init_range":
        model["native_range"] = [0, 0]
    elif kind == "duplicate_ops":
        model["operations"][1] = model["operations"][0]
    elif kind == "missing_model":
        worker["models"].pop()
    elif kind == "claimed_work":
        worker["work"]["values"] -= 1
    else:
        row = overlay(evidence, model["operations"][0])
        if kind == "op_range":
            row["native_range"] = [0, 9]
        elif kind == "event_range":
            row["native_event_range"] = [0, 18]
        elif kind == "attempt_index":
            overlay(evidence, row["attempt"])["index"] = True
        elif kind == "attempt_prefix":
            overlay(evidence, row["attempt"])["native_start"] = 0
    with pytest.raises(ValueError):
        audit_ledger(ledger_fixture, evidence, worker)


def process_fixture(ledger_fixture, tmp_path):
    worker, config, output = ledger_fixture
    # No worker execution: add only synthetic parent bookkeeping around the
    # persisted fake-producer worker for strict saved-process admission tests.
    start = config["started_monotonic"]
    process = dict(
        returncode=0,
        timed_out=False,
        elapsed_seconds=worker["ended_monotonic"] - start + 1,
        minimum_observed_free_bytes=4 * 1024**3,
    )
    # Actual worker path must retain the parent's original config directory.
    process_ref = save(tmp_path / "process.json", process)
    launch_ref = save(
        tmp_path / "launch.json",
        dict(
            case=worker["case"],
            started_monotonic=start,
            command=["python", "runner", "--worker", str(output / "config.json")],
        ),
    )
    result = dict(
        status="completed",
        case=worker["case"],
        worker=ref(output / "worker.json"),
        config=ref(output / "config.json"),
        process=process_ref,
        launch=launch_ref,
        retained=[ref(path) for path in output.rglob("*") if path.is_file()],
    )
    # Semantic process checks use already hash-verified document overlays;
    # retained path constraints are tested separately on actual raw graphs.
    evidence = audit.Evidence()
    for key in ("process", "launch"):
        document = evidence.read(result[key])
        original = result[key]
        virtual = dict(original, path=str(output / (key + ".json")))
        evidence.references[virtual["path"]] = dict(
            sha256=virtual["sha256"], bytes=Path(original["path"]).stat().st_size
        )
        evidence.documents[virtual["path"]] = document
        result[key] = virtual
        result["retained"].append(virtual)
    return result, evidence, config["source"]


@pytest.mark.parametrize(
    "mutation",
    [
        None,
        "returncode_bool",
        "returncode_nonzero",
        "parent_timeout",
        "clock_nan",
        "late_end",
        "parent_disk",
        "worker_disk",
        "scope_alias",
    ],
)
def test_parent_and_worker_completion_guards(ledger_fixture, tmp_path, mutation):
    result, evidence, binding = process_fixture(ledger_fixture, tmp_path)
    worker = overlay(evidence, result["worker"])
    process = overlay(evidence, result["process"])
    if mutation == "returncode_bool":
        process["returncode"] = False
    elif mutation == "returncode_nonzero":
        process["returncode"] = 1
    elif mutation == "parent_timeout":
        process["elapsed_seconds"] = 1800.0
    elif mutation == "clock_nan":
        worker["elapsed_seconds"] = float("nan")
    elif mutation == "late_end":
        worker["ended_monotonic"] += 1900
    elif mutation == "parent_disk":
        process["minimum_observed_free_bytes"] = 1
    elif mutation == "worker_disk":
        worker["minimum_observed_free_bytes"] = 1
    elif mutation == "scope_alias":
        worker["scope"]["startup_pass"] = 0
    if mutation is None:
        assert (
            audit.process_audit(result, result["case"], binding, evidence)[0]["status"]
            == "completed"
        )
    else:
        with pytest.raises(ValueError):
            audit.process_audit(result, result["case"], binding, evidence)


def wiring_metrics(x, method, scale, b2, *, frozen_scale=False):
    x = np.asarray(x)
    n = len(x) // 33 if len(x) == 198 else 8
    jn = float(x @ x) + 1.0
    return dict(
        JN=jn,
        JV=20.0,
        J=jn + (1.0 if method == "V" else 0.0),
        scale=scale,
        B2_scale=b2,
        target_flux=2.0,
        unit_flux=1.0,
        flux=2.0,
        current=1e5 * scale,
        frozen_scale=frozen_scale,
        normal_rms=0.2,
        normal_max=0.3,
        vector_rms=0.4,
        boundary_B_rms=3.0,
        lengths=[2.0] * n,
        kappa_max=[5.0] * n,
        coil_distance=0.1,
        surface_distance=0.12,
        geometry_penalty=0.0,
    )


@pytest.fixture(scope="module")
def wiring_fixture(tmp_path_factory):
    """Actual four-cell producer artifacts; ONLY inner field physics is fake.

    Snapshot/model/grid/source mapping and complete native callback/operation
    ledgers are real producer code, not another handwritten record generator.
    """
    import run_clear_coil_field_start as runner
    from test_clear_coil_field import seed as valid_geometry
    from test_clear_coil_field_start_workflow import FakeModel, fixture_source

    directory = tmp_path_factory.mktemp("startup-full-producer-wiring")
    binding = fixture_source(directory)
    geometries = {}
    for n, m in ((6, 5), (8, 7)):
        label = f"n{n}-shape-d100mm"
        geometry = valid_geometry(n, m)
        geometry["sources"] = copy.deepcopy(binding["targets"])
        path = directory / f"admitted-geometry-{n}.json"
        binding["seeds"][label] = dict(snapshot=save(path, geometry))
        geometries[label] = geometry
    opaque = save(directory / "qualified-primitive-record.json", dict(synthetic=True))
    raw_predecessor = save(directory / "mocked-source-admission.json", dict(synthetic=True))
    binding.update(
        primitives_qualification=opaque,
        geometry=dict(run=raw_predecessor),
        bounded_reference=dict(run=raw_predecessor),
        repository=dict(commit="1" * 40, dirty=False),
        numerical_pin="unchanged",
    )

    class WiringModel(FakeModel):
        def __init__(self, source, case, spec, geometry, callback):
            super().__init__(source, case, spec, geometry, callback)
            self.seed_unit_flux = 1.0
            self.seed_geometry = copy.deepcopy(geometry)
            self.target_sources = copy.deepcopy(source["targets"][case["target"]])

        def _state(self, x, scale=None, B2_scale=None):
            metrics, raw = super()._state(x, scale, B2_scale)
            metrics.update(
                wiring_metrics(
                    x, self.method, metrics["scale"], self.B2_scale, frozen_scale=scale is not None
                )
            )
            return metrics, raw

        def snapshot(self, x):
            result = super().snapshot(x)
            physical = copy.deepcopy(self.seed_geometry["physical"])
            for row in physical:
                row["current"] = 1e5 * result["scale"] * (-1 if row["flip"] else 1)
            result.update(
                schema_version=1,
                nfp=2,
                nbase=self.nbase,
                order=self.order,
                physical=physical,
                unit_flux=1.0,
                sources=self.target_sources,
                seed_geometry=self.seed_geometry,
                construction=audit.CONSTRUCTION.copy(),
                initialization_work=audit.INIT_WORK.copy(),
            )
            return result

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(runner, "sources", lambda root: binding)
        monkeypatch.setattr(runner, "make_model", WiringModel)
        monkeypatch.setattr(runner, "space_check", lambda *args: dict(free_bytes=4 * 1024**3))
        monkeypatch.setattr(runner.os, "getppid", lambda: runner.os.getpid())

        def in_process(command, output, env, started):
            code = runner.worker(output / "config.json")
            return dict(
                returncode=code,
                timed_out=False,
                elapsed_seconds=runner.time.monotonic() - started,
                minimum_observed_free_bytes=4 * 1024**3,
            )

        monkeypatch.setattr(runner, "run_process", in_process)
        for name in runner.THREADS:
            monkeypatch.setenv(name, "1")
        output = directory / "run"
        result = runner.run(output)
    assert result["producer_complete"] is True
    return result, binding, geometries, output


def wire_inner_physics(monkeypatch, fixture):
    run, binding, geometries, _ = fixture
    monkeypatch.setattr(audit, "sources", lambda root: copy.deepcopy(binding))
    monkeypatch.setattr(audit, "prerequisites", lambda bound, evidence: geometries)
    context = dict(
        input={},
        B2_scale=3.25,
        target_flux=2.0,
        targets={
            n: dict(
                inner_points=np.tile([1.0, 0.0, 0.0], (3 * n * n, 1)),
                inner_target=np.ones((3 * n * n, 3)),
            )
            for n in (32, 64)
        },
    )
    monkeypatch.setattr(audit, "target", lambda *args: context)

    def composed(snapshot, data, raw, target, method, level):
        own = wiring_metrics(
            np.ravel(snapshot["base_coefficients"]), method, snapshot["scale"], snapshot["B2_scale"]
        )
        own.pop("frozen_scale")
        return dict(own, geometry=dict(total=0.0), mean_B=3.0, raw_bn_rms=0.5, raw_bn_max=0.7)

    monkeypatch.setattr(numerical, "composed_metrics", composed)
    monkeypatch.setattr(
        audit,
        "direct_fields",
        lambda *args: {f"{p}_{q}": 0.0 for p in ("boundary", "inner", "loop") for q in ("B", "A")},
    )
    monkeypatch.setattr(
        audit, "flux_grid", lambda *args: dict(flux=2.0, direct_errors=dict(B=0.0, A=0.0))
    )
    return run


def test_actual_full_four_cell_producer_to_overall_audit_wiring(wiring_fixture, monkeypatch):
    result = audit.audit(wire_inner_physics(monkeypatch, wiring_fixture))
    assert result["arithmetic_and_source_pass"] is True, result
    assert result["startup_pass"] is True
    assert result["physical_seed_pass"] is False
    assert len(result["cells"]) == 4
    assert sum(r["work"]["work"]["native_requests"] for r in result["cells"]) == 1048
    assert sum(r["direct_field_comparisons"] for r in result["cells"]) == 768
    assert all(r["physical_seed_pass"] is False for r in result["cells"])
    assert all(result[k] is False for k in ("search_allowed", "transfer_pass", "step4_pass"))
    assert json.loads(json.dumps(result, allow_nan=False)) == result


def test_full_wiring_cli_and_docs_only_replay(wiring_fixture, monkeypatch, tmp_path):
    wire_inner_physics(monkeypatch, wiring_fixture)
    output = tmp_path / "audit.json"
    run_path = wiring_fixture[3] / "run.json"
    original = run_path.read_bytes()
    monkeypatch.setattr("sys.argv", ["audit", "--run", str(run_path), "--output", str(output)])
    assert audit.main() == 0
    assert json.loads(output.read_text())["physical_seed_pass"] is False
    assert run_path.read_bytes() == original
    changed = copy.deepcopy(wiring_fixture[1])
    changed["repository"].update(commit="2" * 40, dirty=True)
    monkeypatch.setattr(audit, "sources", lambda root: changed)
    assert audit.audit(wiring_fixture[0])["startup_pass"] is True
    changed["numerical_pin"] = "modified"
    with pytest.raises(ValueError, match="numerical sources"):
        audit.audit(wiring_fixture[0])
    with pytest.raises(ValueError, match="fresh output"):
        audit.main()


@pytest.mark.parametrize(
    "mutation", ["snapshot", "native_denial", "admitted_bool", "fine_init", "B2", "missing_cell"]
)
def test_full_wiring_negative_cases_cannot_be_admitted(wiring_fixture, monkeypatch, mutation):
    run = copy.deepcopy(wire_inner_physics(monkeypatch, wiring_fixture))
    evidence = audit.Evidence()
    first = evidence.read(run["rows"][0])
    worker = overlay(evidence, first["worker"])
    if mutation == "snapshot":
        worker["snapshot"] = worker["models"][0]
    elif mutation == "native_denial":
        worker["native_denials"] = {}
    elif mutation == "admitted_bool":
        worker["admitted_native_requests"] = True
    elif mutation in ("fine_init", "B2"):
        model = overlay(evidence, worker["models"][4])
        initialized = overlay(evidence, model["initialized"])
        key = "seed_unit_flux" if mutation == "fine_init" else "B2_scale"
        model[key] = initialized[key] = 2.0
    elif mutation == "missing_cell":
        run["rows"].pop()
    monkeypatch.setattr(audit, "Evidence", lambda **kwargs: evidence)
    if mutation == "missing_cell":
        with pytest.raises(ValueError, match="four registered"):
            audit.audit(run)
    else:
        result = audit.audit(run)
        assert result["arithmetic_and_source_pass"] is False
        assert result["startup_pass"] is False
        assert result["cells"][0]["status"] == "error"
        assert all(row["status"] == "completed" for row in result["cells"][1:])


def test_full_wiring_negative_derivatives_are_a_complete_negative_study(
    wiring_fixture, monkeypatch
):
    run = wire_inner_physics(monkeypatch, wiring_fixture)
    evidence = audit.Evidence()
    result = evidence.read(run["rows"][0])
    worker = evidence.read(result["worker"])
    row = overlay(evidence, worker["qualification"]["N"][0])
    row["gradient"][0] += 0.1
    monkeypatch.setattr(audit, "Evidence", lambda **kwargs: evidence)
    report = audit.audit(run)
    assert report["arithmetic_and_source_pass"] is True
    assert report["startup_pass"] is False and report["physical_seed_pass"] is False
    assert all(r["status"] == "completed" for r in report["cells"])
    assert report["cells"][0]["qualification"]["N"]["passed"] is False


def test_full_wiring_corrupt_checkpoint_cannot_be_hidden(wiring_fixture, monkeypatch):
    run = wire_inner_physics(monkeypatch, wiring_fixture)
    evidence = audit.Evidence()
    result = evidence.read(run["rows"][0])
    checkpoint = next(r for r in result["retained"] if Path(r["path"]).name == "checkpoint.json")
    overlay(evidence, checkpoint)["native_event_records"] = 0
    monkeypatch.setattr(audit, "Evidence", lambda **kwargs: evidence)
    report = audit.audit(run)
    assert report["arithmetic_and_source_pass"] is False and report["startup_pass"] is False
    assert "checkpoint" in report["cells"][0]["error"]
    observations = report["cells"][0]["retained_native_observations"]
    assert observations["observed_completed_requests"] == 262
    assert observations["authoritative_complete_count"] is False


@pytest.mark.parametrize("ninner", [32, 64])
@pytest.mark.parametrize("key", ["inner_points", "inner_target"])
def test_even_subtolerance_archive_reconstruction_cannot_replace_exact_target(
    wiring_fixture, monkeypatch, ninner, key
):
    run = wire_inner_physics(monkeypatch, wiring_fixture)
    evidence = audit.Evidence()
    result = evidence.read(run["rows"][0])
    worker = evidence.read(result["worker"])
    at = 0 if ninner == 32 else 4
    row = evidence.read(worker["diagnostics"][at])
    snapshot = evidence.read(worker["snapshot"])
    context = audit.target(None, None, None)
    assert (
        audit.field_row(row, snapshot, context, numerical.levels()[at], evidence, diagnostic=True)[
            "status"
        ]
        == "completed"
    )
    raw = {k: v.copy() for k, v in evidence.array(row["arrays"]).items()}
    raw[key].flat[0] += 1e-14
    assert abs(raw[key].flat[0] - context["targets"][ninner][key].flat[0]) < 5e-12
    evidence.arrays[row["arrays"]["path"]] = raw
    with pytest.raises(ValueError, match="exact active archived64"):
        audit.field_row(row, snapshot, context, numerical.levels()[at], evidence, diagnostic=True)
