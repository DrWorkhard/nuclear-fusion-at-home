"""Small fake-field workflow controls; no native/project-field calculations."""

import copy
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_clear_coil_field_start as runner  # noqa: E402


def fixture_source(tmp_path):
    geometries = {}
    for nbase, order in ((6, 5), (8, 7)):
        coefficients = np.zeros((nbase, 3, 2 * order + 1))
        coefficients[:, 0, 0] = 0.3
        path = tmp_path / f"geometry-{nbase}.json"
        runner.save(
            path,
            dict(base_coefficients=coefficients.tolist(), names=runner.storage.local_names(order)),
        )
        geometries[f"n{nbase}-shape-d100mm"] = dict(snapshot=two_key_ref(path))
    target = tmp_path / "synthetic-target.json"
    runner.save(target, dict(unit_test_only=True))
    return dict(
        matrix=runner.matrix(),
        seeds=geometries,
        targets={
            key: dict(input=two_key_ref(target), wout=two_key_ref(target))
            for key in ("reference", "selected")
        },
        normalization={key: dict(B2_scale=3.25) for key in ("reference", "selected")},
    )


def two_key_ref(path):
    return {key: value for key, value in runner.ref(path).items() if key != "bytes"}


class FakeNative:
    def set_points(self, points):
        self.points = points.copy()

    def A(self):
        return np.ones_like(self.points)

    def B(self):
        return np.ones_like(self.points)

    def A_vjp(self, weights):
        return np.asarray(weights).copy()

    def B_vjp(self, weights):
        return np.asarray(weights).copy()


class FakeModel:
    def __init__(self, source, case, spec, geometry, callback):
        from fusion_baselines.clear_coil_field import CountedField

        self.method, self.spec = spec["method"], spec
        self.seed_x = np.ravel(geometry["base_coefficients"]).copy()
        self.names = [
            f"coil[{i}]/{name}"
            for i in range(case["nbase"])
            for name in runner.storage.local_names(case["order"])
        ]
        self.nbase, self.order = case["nbase"], case["order"]
        self.ncoil = spec["grid"]["ncoil"]
        self.B2_scale = source["normalization"][case["target"]]["B2_scale"]
        self.target_flux, self.seed_unit_flux = 2.0, self.ncoil / 256
        self.native_calls, self._cache = [], None
        self.field, self.inner_field, self.loop_field = [
            CountedField(FakeNative(), label, self.native_calls, callback)
            for label in ("boundary", "inner", "loop")
        ]
        self.loop_field.set_points(self.loop(256)[0])
        self.loop_field.A()
        self.initialization_work = dict(seed_A_calls=1, seed_A_points=256)

    def loop(self, ntheta):
        theta = 2 * np.pi * np.arange(ntheta) / ntheta
        return (
            np.column_stack((1 + 0.1 * np.cos(theta), np.zeros(ntheta), 0.1 * np.sin(theta))),
            np.column_stack(
                (-0.2 * np.pi * np.sin(theta), np.zeros(ntheta), 0.2 * np.pi * np.cos(theta))
            ),
        )

    def _state(self, x, scale=None, B2_scale=None):
        x = np.asarray(x)
        key = (x.tobytes(), scale, B2_scale)
        if self._cache is not None and self._cache[0] == key:
            return self._cache[1], self._cache[2]
        grid = self.spec["grid"]
        bp = np.tile([1.0, 0.0, 0.0], (grid["nphi"] * grid["ntheta"], 1))
        ip = np.tile([1.0, 0.0, 0.0], (3 * grid["ninner"] ** 2, 1))
        lp, tangent = self.loop(256)
        for field, points in ((self.field, bp), (self.inner_field, ip), (self.loop_field, lp)):
            field.set_points(points)
        b, bi, a = self.field.B(), self.inner_field.B(), self.loop_field.A()
        chosen = self.target_flux / self.seed_unit_flux if scale is None else scale
        normal = np.tile([1.0, 0.0, 0.0], (len(bp), 1))
        value = float(x @ x) + (1.0 if self.method == "N" else 2.0)
        metrics = dict(
            J=value,
            scale=chosen,
            B2_scale=self.B2_scale,
            target_flux=self.target_flux,
            unit_flux=self.seed_unit_flux,
            flux=chosen * self.seed_unit_flux,
            current=1e5 * chosen,
            frozen_scale=scale is not None,
            normal_rms=0.2,
            normal_max=0.3,
            vector_rms=0.4,
        )
        raw = dict(
            boundary_points=bp,
            boundary_normals=normal,
            boundary_weights=np.ones(len(bp)) / len(bp),
            boundary_B=chosen * b,
            inner_points=ip,
            inner_target=np.ones_like(ip),
            inner_B=chosen * bi,
            loop_points=lp,
            loop_tangents=tangent,
            loop_A=chosen * a,
            coil_positions=np.ones((4 * self.nbase, self.ncoil, 3)),
            coil_tangents=np.ones((4 * self.nbase, self.ncoil, 3)),
            coil_currents=np.ones(4 * self.nbase) * chosen * 1e5,
        )
        self._cache = key, metrics, raw
        return metrics, raw

    def evaluate(self, x):
        metrics, raw = self._state(x)
        self.field.B_vjp(np.zeros_like(raw["boundary_B"]))
        self.inner_field.B_vjp(np.zeros_like(raw["inner_B"]))
        self.loop_field.A_vjp(np.zeros_like(raw["loop_A"]))
        return metrics["J"], 2 * np.asarray(x), copy.deepcopy(metrics)

    def diagnostics(self, x, scale, B2_scale):
        return copy.deepcopy(self._state(x, scale, B2_scale)[0])

    def arrays(self, x, scale=None, B2_scale=None):
        return {key: value.copy() for key, value in self._state(x, scale, B2_scale)[1].items()}

    def snapshot(self, x):
        metrics = self._state(x)[0]
        return dict(
            method=self.method,
            scale=metrics["scale"],
            B2_scale=self.B2_scale,
            target_flux=self.target_flux,
            seed_unit_flux=self.seed_unit_flux,
            names=self.names,
            base_coefficients=np.asarray(x).reshape(self.nbase, 3, 2 * self.order + 1).tolist(),
        )


def run_fake(monkeypatch, tmp_path, *, constructor=None):
    source = fixture_source(tmp_path)
    output = tmp_path / "cell"
    output.mkdir()
    monkeypatch.setattr(runner, "sources", lambda root: source)
    monkeypatch.setattr(runner, "make_model", FakeModel if constructor is None else constructor)
    monkeypatch.setattr(runner, "space_check", lambda *args: dict(free_bytes=4 * runner.GIB))
    for name in runner.THREADS:
        monkeypatch.setenv(name, "1")
    config = dict(
        case=runner.matrix()[0],
        source=source,
        output=str(output),
        parent_pid=os.getppid(),
        started_monotonic=runner.time.monotonic(),
    )
    runner.save(output / "config.json", config)
    code = runner.worker(output / "config.json")
    return output, code


def test_exact_registered_plan_and_call_budget():
    models = runner.model_plan()
    assert len(runner.matrix()) == 4 and len(models) == 10
    assert [spec["id"] for spec in models] == ["qualification-N", "qualification-V"] + [
        f"diagnostic-{i}" for i in range(6)
    ] + ["flux-256", "flux-512"]
    ops = [op for spec in models for op in runner.operations(spec, np.zeros(198))]
    assert len(ops) == 44
    assert [
        sum(op["kind"] == kind for op in ops) for kind in ("qualification", "diagnostic", "flux")
    ] == [20, 6, 18]
    assert sum(1 if op["kind"] == "qualification" else 0 for op in ops) == 20
    assert runner.WALL_SECONDS == 1800


def test_full_fake_cell_preserves_frozen_scale_and_counts_every_value_and_vjp(
    monkeypatch, tmp_path
):
    output, code = run_fake(monkeypatch, tmp_path)
    assert code == 0
    document = runner.read(output / "worker.json")
    assert document["work"] == dict(
        native_requests=262,
        completed_requests=262,
        values=202,
        vjps=60,
        initialization_requests=10,
        full_bundles=20,
        equilibrium_solves=0,
        search_calls=0,
    )
    assert len(document["models"]) == 10 and len(document["operations"]) == 44
    assert document["native_event_records"] == 524
    assert document["scope"]["startup_pass"] is document["scope"]["physical_seed_pass"] is False
    snapshot = document["snapshot"]
    assert runner.read(runner.checked(snapshot))["scale"] == 2.0
    for ref in document["diagnostics"]:
        row = runner.read(runner.checked(ref))
        assert row["snapshot"] == snapshot and row["scale"] == row["metrics"]["scale"] == 2.0
        assert row["native_range"] == [1, 7]
    for ref in document["flux"]:
        block = runner.read(runner.checked(ref))
        assert block["snapshot"] == snapshot and block["full_bundles"] == 0
        assert len(block["lines"]) == 3 and len(block["areas"]) == 6
        for ref in block["lines"] + block["areas"]:
            assert runner.read(runner.checked(ref))["scale"] == 2.0
    models = [runner.read(runner.checked(ref)) for ref in document["models"]]
    assert [len(model["native_calls"]) for model in models] == [91, 91] + [7] * 6 + [19, 19]
    assert all(model["native_range"] == [0, 1] for model in models)
    assert models[-1]["seed_unit_flux"] == 2.0  # Fine native flux is not copied from coarse model.
    for method in ("N", "V"):
        rows = [runner.read(runner.checked(ref)) for ref in document["qualification"][method]]
        assert all(
            row["native_range"] == [1 + 9 * i, 1 + 9 * (i + 1)] for i, row in enumerate(rows)
        )
        assert rows[0]["J"] == rows[-1]["J"] and rows[0]["gradient"] == rows[-1]["gradient"]


def test_real_input_reference_shapes_accept_two_and_three_keys_before_mock_constructor(
    monkeypatch, tmp_path
):
    source = fixture_source(tmp_path)
    observed = []
    module = SimpleNamespace(
        ClearCoilField=lambda *args, **kwargs: observed.append((args, kwargs)) or "fake"
    )
    monkeypatch.setitem(sys.modules, "fusion_baselines.clear_coil_field", module)
    bindings = []
    monkeypatch.setattr(runner, "bind_archived_inner_target", lambda *args: bindings.append(args))
    case, spec = runner.matrix()[0], runner.model_plan()[0]
    geometry = runner.read(runner.checked_source(source["seeds"][case["seed_label"]]["snapshot"]))
    assert runner.make_model(source, case, spec, geometry, lambda event: None) == "fake"
    assert bindings == [("fake", source, case)]
    assert all(isinstance(path, Path) for path in observed[0][0][:2])
    path = observed[0][0][0]
    assert runner.checked_source(runner.ref(path)) == path
    assert runner.checked_source(two_key_ref(path)) == path


def archived_binding_fixture(tmp_path, ninner):
    """Synthetic angular/radial variation exposes transposition and wrong subsampling."""
    phi, theta = np.meshgrid(
        np.pi * np.arange(64) / 64, 2 * np.pi * np.arange(64) / 64, indexing="ij"
    )
    archives, positions, fields = [], [], []
    for i, surface in enumerate((0.25, 0.5, 0.75)):
        radius = 1 + surface / 10 * np.cos(theta) + phi / 100
        height = surface / 10 * np.sin(theta) + phi / 200
        bt = 0.1 + surface / 20 + theta / 100
        bp = 1 + surface / 10 + phi / 200 + theta / 300
        et = np.zeros((*phi.shape, 3))
        et[..., 2] = 1
        ep = np.stack((-np.sin(phi), np.cos(phi), np.zeros_like(phi)), axis=-1)
        magnetic = np.stack((-bp * np.sin(phi), bp * np.cos(phi), bt), axis=-1)
        data = dict(
            phi=phi,
            theta=theta,
            radius=radius,
            height=height,
            bt=bt,
            bp=bp,
            et=et,
            ep=ep,
            native=magnetic,
        )
        path = tmp_path / f"archive-{i}.npz"
        runner.storage.arrays(path, data)
        archives.append(dict(s=surface, n=64, arrays=two_key_ref(path)))
        positions.append(np.stack((radius * np.cos(phi), radius * np.sin(phi), height), axis=-1))
        fields.append(magnetic)
    b2 = float(np.mean(np.sum(np.concatenate([b.reshape(-1, 3) for b in fields]) ** 2, axis=1)))
    stride = 64 // ninner
    expected = dict(
        inner_points=np.concatenate([p[::stride, ::stride].reshape(-1, 3) for p in positions]),
        inner_target=np.concatenate([b[::stride, ::stride].reshape(-1, 3) for b in fields]),
    )
    reconstruction = {key: value.copy() + 1e-13 for key, value in expected.items()}
    model = SimpleNamespace(
        _cache=None,
        native_calls=[
            dict(
                index=0,
                field="loop",
                quantity="A",
                points=256,
                status="completed",
                native_started=True,
                native_completed=True,
            )
        ],
        initialization_work=dict(seed_A_calls=1, seed_A_points=256),
        ninner=ninner,
        B2_scale=b2,
        seed_unit_flux=1.25,
        target_flux=-0.2,
        loop=lambda n: FakeModel.loop(None, n),
        input=dict(phiedge=0.2),
        target=dict(reconstruction, sources={"unchanged": "synthetic"}),
        **reconstruction,
    )
    source = dict(normalization={"reference": dict(B2_scale=b2, archives=archives)})
    return model, source, dict(target="reference"), expected


@pytest.mark.parametrize("ninner", [32, 64])
def test_archived_target_exact_slice_replaces_small_wout_drift_without_native_calls(
    tmp_path, ninner
):
    model, source, case, expected = archived_binding_fixture(tmp_path, ninner)
    before_calls = copy.deepcopy(model.native_calls)
    old_arrays = {key: getattr(model, key) for key in expected}
    target_sources = copy.deepcopy(model.target["sources"])
    before_scalars = (model.B2_scale, model.target_flux, model.seed_unit_flux)
    runner.bind_archived_inner_target(model, source, case)
    assert model._cache is None and model.native_calls == before_calls
    assert (model.B2_scale, model.target_flux, model.seed_unit_flux) == before_scalars
    if ninner == 32:
        assert float(np.mean(np.sum(expected["inner_target"] ** 2, axis=1))) != model.B2_scale
    assert model.target["sources"] == target_sources
    for key, value in expected.items():
        installed = getattr(model, key)
        assert np.array_equal(installed, value)
        assert np.array_equal(model.target[key], value)
        assert installed.flags.c_contiguous and model.target[key].flags.c_contiguous
        assert not np.shares_memory(installed, model.target[key])
        assert not np.shares_memory(installed, old_arrays[key])
        old_arrays[key][:] = 100
        model.target[key][:] = 200
        assert np.array_equal(installed, value)
    for row in source["normalization"]["reference"]["archives"]:
        runner.checked_source(
            row["arrays"]
        )  # Mutating installed copies leaves pinned bytes intact.


@pytest.mark.parametrize(
    "mutation",
    [
        "points",
        "target",
        "target-dictionary",
        "normalization",
        "model-B2",
        "target-flux",
        "cache",
        "extra-call",
        "failed-initial-call",
        "archive-order",
    ],
)
def test_archived_target_binding_rejects_invalid_replay_before_mutation(tmp_path, mutation):
    model, source, case, _ = archived_binding_fixture(tmp_path, 32)
    if mutation == "points":
        model.inner_points[0, 0] += 1e-10
    elif mutation == "target":
        model.inner_target[0, 0] += 1e-10
    elif mutation == "target-dictionary":
        model.target["inner_target"] = model.inner_target.copy() + 1e-10
    elif mutation == "normalization":
        source["normalization"]["reference"]["B2_scale"] *= 1 + 1e-14
    elif mutation == "model-B2":
        model.B2_scale *= 1 + 1e-14
    elif mutation == "target-flux":
        model.target_flux *= -1
    elif mutation == "cache":
        model._cache = {}
    elif mutation == "extra-call":
        model.native_calls.append(copy.deepcopy(model.native_calls[0]))
    elif mutation == "failed-initial-call":
        model.native_calls[0]["status"] = "error"
    else:
        source["normalization"]["reference"]["archives"].reverse()
    calls = copy.deepcopy(model.native_calls)
    before = {key: getattr(model, key) for key in ("inner_points", "inner_target")}
    values = {key: value.copy() for key, value in before.items()}
    with pytest.raises(ValueError):
        runner.bind_archived_inner_target(model, source, case)
    assert model.native_calls == calls
    assert all(getattr(model, key) is value for key, value in before.items())
    assert all(np.array_equal(getattr(model, key), value) for key, value in values.items())


def test_full64_flux_sign_cannot_hide_at_point_omitted_by32_subsampling(tmp_path):
    model, source, case, _ = archived_binding_fixture(tmp_path, 32)
    row = source["normalization"]["reference"]["archives"][0]
    with np.load(runner.checked_source(row["arrays"]), allow_pickle=False) as archive:
        raw = {key: archive[key].copy() for key in archive.files}
    # phi0/theta1 is absent from the 32er interior, but remains a mandatory sign check.
    raw["bp"][0, 1] *= -1
    raw["native"] = raw["bt"][..., None] * raw["et"] + raw["bp"][..., None] * raw["ep"]
    path = tmp_path / "mixed-sign-archive.npz"
    runner.storage.arrays(path, raw)
    row["arrays"] = two_key_ref(path)
    old_points, old_target = model.inner_points, model.inner_target
    with pytest.raises(ValueError, match="full64 toroidal sign"):
        runner.bind_archived_inner_target(model, source, case)
    assert model.inner_points is old_points and model.inner_target is old_target
    assert len(model.native_calls) == 1


def test_numerical_diagnostic_failure_keeps_other_registered_levels(monkeypatch, tmp_path):
    def model(*args):
        instance = FakeModel(*args)
        if instance.spec["id"] == "diagnostic-0":
            instance.diagnostics = lambda *args: (_ for _ in ()).throw(
                ArithmeticError("injected numerical failure")
            )
        return instance

    output, code = run_fake(monkeypatch, tmp_path, constructor=model)
    assert code == 1
    document = runner.read(output / "worker.json")
    assert len(document["models"]) == 10 and len(document["diagnostics"]) == 6
    rows = [runner.read(runner.checked(ref)) for ref in document["diagnostics"]]
    assert [row["status"] for row in rows] == ["error"] + ["completed"] * 5
    assert len(document["flux"]) == 2 and document["scope"]["startup_pass"] is False


def test_initialization_failure_keeps_callback_work_and_model_attempt(monkeypatch, tmp_path):
    def fail(*args):
        FakeModel(*args)
        raise ArithmeticError("after first A")

    output, code = run_fake(monkeypatch, tmp_path, constructor=fail)
    assert code == 1
    document = runner.read(output / "worker-error.json")
    assert len(document["model_attempts"]) == 1 and document["operation_attempts"] == []
    assert document["native_prefixes"]["qualification-N"][0]["quantity"] == "A"
    assert document["native_prefixes"]["qualification-N"][0]["status"] == "completed"
    assert document["native_event_records"] == 2 and not (output / "checkpoint.json").exists()


@pytest.mark.parametrize("limit", ["global", "model", "operation", "initialization", "order"])
def test_native_budget_and_sequence_refusal_precedes_dispatch(tmp_path, limit):
    from fusion_baselines.clear_coil_field import CountedField

    class Tracked(FakeNative):
        calls = 0

        def A(self):
            self.calls += 1
            return super().A()

    log = runner.NativeLog(tmp_path, lambda: None)
    log.operation_id = "init:qualification-N"
    native, events = Tracked(), []
    proxy = CountedField(native, "loop", events, log.callback("qualification-N"))
    proxy.set_points(np.zeros((256, 3)))
    if limit == "global":
        log.admitted_total = 262
    elif limit == "model":
        log.admitted_models["qualification-N"] = 91
    elif limit == "operation":
        log.operation_id = "qualification-N-00"
        log.admitted_operations[log.operation_id] = 9
    elif limit == "initialization":
        proxy.A()
        assert native.calls == 1
    else:
        log.operation_id = "qualification-N-00"  # Must start with boundary.B, not extra loop.A.
    before = native.calls
    with pytest.raises(runner.NativeBudgetExceeded):
        proxy.A()
    assert native.calls == before
    assert events[-1]["native_started"] is events[-1]["native_completed"] is False
    assert events[-1]["status"] == "error"
    denied = json.loads(log.denials.read_text().splitlines()[-1])
    assert denied["native_dispatch_permitted"] is False
    assert log.references()["native_denials"] == runner.ref(log.denials)


def test_late_completed_operation_retains_raw_not_checkpoint(monkeypatch, tmp_path):
    original = runner.Guard.__call__

    def late(self):
        original(self)
        if (self.output / "operations/qualification-N-01.json").exists():
            raise TimeoutError("injected late result")

    monkeypatch.setattr(runner.Guard, "__call__", late)
    output, code = run_fake(monkeypatch, tmp_path)
    assert code == 1
    assert (output / "operations/qualification-N-01.npz").exists()
    checkpoint = runner.read(output / "checkpoint.json")
    assert len(checkpoint["operations"]) == 1
    assert runner.read(output / "worker-error.json")["error_type"] == "TimeoutError"


def test_parent_loss_before_a_native_request_stops_work(monkeypatch, tmp_path):
    actual_parent, lost = os.getppid(), []
    original = runner.NativeLog.callback

    def lose(self, model_id):
        receive = original(self, model_id)

        def wrapped(event):
            receive(event)
            if (
                model_id == "qualification-N"
                and event["index"] == 0
                and event["status"] == "completed"
            ):
                lost.append(True)

        return wrapped

    monkeypatch.setattr(runner.NativeLog, "callback", lose)
    monkeypatch.setattr(runner.os, "getppid", lambda: actual_parent + 1 if lost else actual_parent)
    output, code = run_fake(monkeypatch, tmp_path)
    assert code == 1
    record = runner.read(output / "worker-error.json")
    assert record["error_type"] == "ParentLost" and record["operation_attempts"] == []
    assert len(record["native_prefixes"]["qualification-N"]) == 1


def test_parent_tries_all_cells_but_never_relabels_process_failure(monkeypatch, tmp_path):
    source = dict(matrix=runner.matrix())
    reserves, calls = [], []
    monkeypatch.setattr(runner, "sources", lambda root: source)
    monkeypatch.setattr(
        runner,
        "space_check",
        lambda path, reserve: reserves.append(reserve) or dict(free_bytes=4 * runner.GIB),
    )
    monkeypatch.setattr(
        runner,
        "run_process",
        lambda command, output, env, started: (
            calls.append(command) or dict(returncode=1, timed_out=False, elapsed_seconds=0.01)
        ),
    )
    result = runner.run(tmp_path / "matrix")
    assert len(calls) == len(result["rows"]) == 4 and reserves == [3 * runner.GIB] * 4
    assert result["producer_complete"] is result["startup_pass"] is result["all_pass"] is False
    assert not (tmp_path / "matrix/checkpoint.json").exists()


@pytest.mark.parametrize(
    "key,value",
    [
        ("returncode", False),
        ("returncode", 0.0),
        ("elapsed_seconds", float("nan")),
        ("elapsed_seconds", 1800.0),
        ("timed_out", 0),
    ],
)
def test_parent_completion_requires_exact_success_types(key, value):
    process = dict(returncode=0, timed_out=False, elapsed_seconds=1.0)
    case, source = runner.matrix()[0], {}
    document = dict(
        status="completed",
        case=case,
        source_before=source,
        source_after=source,
        elapsed_seconds=0.9,
        ended_monotonic=10.9,
        threads={key: "1" for key in runner.THREADS},
        scope=runner.SCOPE,
    )
    runner.process_complete(process, document, case, source, 10.0)
    process[key] = value
    with pytest.raises(ValueError):
        runner.process_complete(process, document, case, source, 10.0)


def test_deadline_boundary_and_fresh_output_failure(monkeypatch, tmp_path):
    assert runner.deadline(10.0, 1809.9) < 1800
    with pytest.raises(TimeoutError):
        runner.deadline(10.0, 1810.0)
    with pytest.raises(ValueError):
        runner.deadline(10.0, 9.0)
    monkeypatch.setattr(
        runner, "_run", lambda output: (_ for _ in ()).throw(OSError("injected IO"))
    )
    directory = tmp_path / "fresh"
    with pytest.raises(OSError):
        runner.run(directory)
    original = (directory / "terminal-error.json").read_bytes()
    with pytest.raises(FileExistsError):
        runner.run(directory)
    assert (directory / "terminal-error.json").read_bytes() == original
