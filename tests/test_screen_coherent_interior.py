"""Synthetic-only frozen interior screen controls: no native field evaluations."""

import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
with pytest.MonkeyPatch.context() as patch:
    patch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "screen_coherent_interior", ROOT / "scripts/screen_coherent_interior.py"
    )
    screen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(screen)


@pytest.fixture
def snapshot():
    coefficients = np.zeros((6, 3, 11))
    coefficients[:, 0, 0] = np.linspace(1, 2, 6)
    coefficients[:, 0, 2] = 0.2
    coefficients[:, 1, 1] = 0.2
    physical = []
    for period in range(2):
        c, s = np.cos(np.pi * period), np.sin(np.pi * period)
        rotation = np.array([[c, s, 0.0], [-s, c, 0.0], [0.0, 0.0, 1.0]])
        for flip in (False, True):
            matrix = rotation @ np.diag([1.0, -1.0, -1.0]) if flip else rotation
            physical.extend(
                dict(
                    base_index=i,
                    period=period,
                    flip=flip,
                    matrix=matrix.tolist(),
                    current=200000.0 * (-1 if flip else 1),
                )
                for i in range(6)
            )
    return dict(
        schema_version=1,
        nbase=6,
        order=5,
        nfp=2,
        names=screen.independent.parameter_names(6, 5),
        base_coefficients=coefficients.tolist(),
        physical=physical,
        B2_scale=screen.B2,
        target_flux=screen.TARGET_FLUX,
        scale=2.0,
        unit_flux=screen.TARGET_FLUX / 2,
        seed_unit_flux=screen.TARGET_FLUX / 2,
    )


def selected_trial(snapshot, index=12):
    return dict(
        index=index,
        role="search",
        status="completed",
        x=np.ravel(snapshot["base_coefficients"]).tolist(),
        metrics=dict(
            scale=snapshot["scale"],
            unit_flux=snapshot["unit_flux"],
            current=1e5 * snapshot["scale"],
        ),
    )


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


@pytest.fixture
def selected(tmp_path, snapshot, monkeypatch):
    monkeypatch.setattr(screen, "ROOT", tmp_path)
    source = write(tmp_path / screen.TARGET, {"test": "target"})
    monkeypatch.setitem(screen.FIXED, screen.TARGET, screen.digest(source))
    trial = selected_trial(snapshot)
    fine = [
        dict(
            n=128,
            nodes=512,
            shift=shift,
            checks_pass=True,
            metrics=dict(frozen_scale=2.0, current=200000.0),
        )
        for shift in (0.0, 0.5)
    ]
    folder = tmp_path / "run"
    stem = folder / "control"
    write(stem / "selected-snapshot.json", snapshot)
    write(stem / "trial-0012.json", trial)
    for row in fine:
        path = stem / f"fine-{row['shift']}.npz"
        path.write_bytes(b"synthetic saved-field identity fixture")
        row["arrays_sha256"] = screen.digest(path)
        write(stem / f"fine-{row['shift']}.json", row)
    arm = dict(
        arm="control",
        active_names=snapshot["names"],
        active_count=198,
        startup_pass=True,
        status=dict(reason="budget"),
        fine=fine,
        fine_selected=trial,
        fine_selection="sampled-feasible",
    )
    sources = {str(source): screen.digest(source)}
    report = dict(
        completed=True,
        sources_unchanged=True,
        sources_before=sources,
        sources_after=copy.deepcopy(sources),
        arms=[arm],
    )
    return report, folder


def test_selected_trial_fine_and_source_binding(selected, snapshot):
    report, folder = selected
    sources = {}
    actual, association = screen.selected_snapshot(report, folder, "control", sources, width=4)
    assert actual == snapshot and association["selected_index"] == 12
    assert association["geometry_admission"] == "not_assessed_here"
    assert len(sources) == 7


@pytest.mark.parametrize(
    "fault",
    [
        "failed",
        "boolean",
        "changed",
        "target",
        "missing-arm",
        "duplicate-arm",
        "startup",
        "execution",
        "failure",
        "fine-count",
        "fine-flag",
        "names",
        "trial",
        "snapshot-current",
        "fine-current",
        "array",
    ],
)
def test_selected_source_poisoning_rejects(selected, fault):
    report, folder = selected
    arm = report["arms"][0]
    if fault == "failed":
        report["completed"] = False
    if fault == "boolean":
        report["completed"] = 1
    if fault == "changed":
        report["sources_after"] = {}
    if fault == "target":
        report["sources_before"] = report["sources_after"] = {}
    if fault == "missing-arm":
        arm["arm"] = "other"
    if fault == "duplicate-arm":
        report["arms"].append(copy.deepcopy(arm))
    if fault == "startup":
        arm["startup_pass"] = False
    if fault == "execution":
        arm["execution_error"] = "stopped"
    if fault == "failure":
        arm["status"]["reason"] = "failure"
    if fault == "fine-count":
        arm["fine"].pop()
    if fault == "fine-flag":
        arm["fine"][0]["checks_pass"] = False
    if fault == "names":
        arm["active_names"] = list(reversed(arm["active_names"]))
    if fault == "trial":
        arm["fine_selected"]["x"][0] += 0.001
    if fault == "snapshot-current":
        path = folder / "control/selected-snapshot.json"
        data = screen.read_json(path)
        data["physical"][0]["current"] *= -1
        write(path, data)
    if fault == "fine-current":
        arm["fine"][0]["metrics"]["frozen_scale"] = 3.0
        write(folder / "control/fine-0.0.json", arm["fine"][0])
    if fault == "array":
        (folder / "control/fine-0.0.npz").write_bytes(b"changed")
    with pytest.raises(ValueError):
        screen.selected_snapshot(report, folder, "control", {}, width=4)


@pytest.mark.parametrize("field", ["scale", "unit_flux", "target_flux", "B2_scale"])
def test_snapshot_normalization_is_exact(snapshot, field):
    snapshot[field] = np.nextafter(snapshot[field], np.inf)
    with pytest.raises(ValueError):
        screen.snapshot_identity(snapshot)


def metric_arrays(n=32):
    target = np.tile([1.0, 0.0, 0.0], (3 * n * n, 1))
    B = target + np.tile([0.0, 0.02, 0.0], (len(target), 1))
    A = np.tile([screen.TARGET_FLUX, 0.0, 0.0], (256, 1))
    tangent = np.tile([1.0, 0.0, 0.0], (256, 1))
    return B, target, A, tangent


def test_metrics_use_fixed_b2_equal_surface_weight_and_frozen_currents(snapshot):
    B, target, A, tangent = metric_arrays()
    row = screen.field_metrics(B, target, A, tangent, snapshot, 32)
    assert row["vector_rms"] == pytest.approx(0.02 / np.sqrt(screen.B2))
    assert row["surface_vector_rms"] == pytest.approx([row["vector_rms"]] * 3)
    assert row["field_rms_over_target"] == pytest.approx(np.sqrt(1 + 0.02**2))
    assert row["base_current"] == 200000.0 and row["flux_limit_met"]
    assert not row["inner_limit_met"] and not row["fine_renormalization_applied"]
    B[:1024] = target[:1024]
    second = screen.field_metrics(B, target, A * 0.9, tangent, snapshot, 32)
    assert second["surface_vector_rms"][0] == 0.0
    assert second["vector_rms"] == pytest.approx(0.02 * np.sqrt(2 / (3 * screen.B2)))
    assert not second["flux_limit_met"] and second["base_current"] == 200000.0


@pytest.mark.parametrize("fault", ["missing", "nan", "overflow", "zero-target", "bad-loop"])
def test_metric_input_gates(snapshot, fault):
    B, target, A, tangent = metric_arrays()
    if fault == "missing":
        B = B[:-1]
    if fault == "nan":
        B[0, 0] = np.nan
    if fault == "overflow":
        B[:] = 1e308
    if fault == "zero-target":
        target[0] = 0.0
    if fault == "bad-loop":
        A = A[:255]
        tangent = tangent[:255]
    with pytest.raises(ValueError):
        screen.field_metrics(B, target, A, tangent, snapshot, 32)


def test_zero_coil_field_is_retained_as_negative(snapshot):
    B, target, A, tangent = metric_arrays()
    row = screen.field_metrics(B * 0, target, A * 0, tangent, snapshot, 32)
    assert row["zero_field_sampled"] and row["min_b"] == 0.0
    assert not row["inner_limit_met"] and not row["flux_limit_met"]


def fake_native(monkeypatch, snapshot, fault=None):
    class Curve:
        def __init__(self, nodes, order):
            self.nodes = nodes
            self.local_full_dof_names = [name.split("/")[1] for name in snapshot["names"][:33]]
            if fault == "names":
                self.local_full_dof_names.reverse()

        def fix_all(self):
            pass

        def arrays(self):
            return screen.independent.fourier_curves(
                self.local_full_x.reshape(1, 3, 11), self.nodes
            )

        def gamma(self):
            return self.arrays()["positions"][0]

        def gammadash(self):
            return self.arrays()["tangents"][0]

    class Current:
        def __init__(self, value):
            self.value = value

        def fix_all(self):
            pass

        def get_value(self):
            return self.value

    def copies(curves, currents, nfp, symmetry):
        assert nfp == 2 and symmetry is True
        coils = []
        for row in snapshot["physical"]:
            base, matrix = row["base_index"], np.asarray(row["matrix"])
            current = currents[base].get_value() * (-1 if row["flip"] else 1)
            curve = SimpleNamespace(
                gamma=lambda b=base, m=matrix: curves[b].gamma() @ m,
                gammadash=lambda b=base, m=matrix: curves[b].gammadash() @ m,
            )
            if fault == "position":
                curve.gamma = lambda: np.zeros((256, 3))
            if fault == "current":
                current *= -1
            coils.append(SimpleNamespace(curve=curve, current=Current(current)))
        return coils

    monkeypatch.setitem(sys.modules, "simsopt.geo", SimpleNamespace(CurveXYZFourier=Curve))
    monkeypatch.setitem(
        sys.modules, "simsopt.field", SimpleNamespace(Current=Current, coils_via_symmetries=copies)
    )


def test_native_named_mapping_all24_signed_currents(monkeypatch, snapshot):
    fake_native(monkeypatch, snapshot)
    coils, own, checks = screen.native_coils(snapshot, 256)
    assert len(coils) == 24 and max(checks.values()) < 1e-15
    assert np.array_equal(own["currents"], [r["current"] for r in snapshot["physical"]])


@pytest.mark.parametrize("fault", ["names", "position", "current"])
def test_native_mapping_poisoning(monkeypatch, snapshot, fault):
    fake_native(monkeypatch, snapshot, fault)
    with pytest.raises(ValueError):
        screen.native_coils(snapshot, 256)


@pytest.fixture
def clock(monkeypatch):
    now = [0.0]
    monkeypatch.setattr(screen.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(screen.shutil, "disk_usage", lambda _: SimpleNamespace(free=8 * 1024**3))
    return now


def test_deadline_denies_work_and_late_final_is_not_completed(tmp_path, clock):
    record = screen.Recorder(tmp_path / "run", 180.0)
    clock[0] = 181.0
    calls = []
    with pytest.raises(TimeoutError):
        record.request("B", 128, lambda: calls.append(True))
    assert not calls and record.counts["B"]["attempted"] == 0
    report = dict(completed=True)
    assert screen.paired.publish(record, report, 0.0) == 1
    assert screen.read_json(record.output / "result.json")["completed"] is False


def test_shared_byte_cap_and_points_completed_on_postcall_timeout(tmp_path, clock, monkeypatch):
    record = screen.Recorder(tmp_path / "run", 180.0)

    def late():
        clock[0] = 181.0
        return 3.0

    with pytest.raises(TimeoutError):
        record.request("B", 128, late)
    assert record.counts["B"] == dict(attempted=1, completed=1)
    assert record.points["B"] == dict(attempted=128, completed=128)
    monkeypatch.setattr(screen, "MAX_BYTES", 10)
    with pytest.raises(OSError):
        record.save("large.json", {"value": "larger than ceiling"})


def test_refinement_zero_and_equality_and_original_denominator():
    def rows(values):
        return [
            dict(ninner=n, ncoil=c, metrics=dict(vector_rms=v))
            for (n, c), v in zip(screen.LEVELS, values, strict=True)
        ]

    assert all(r["relative_change"] is None for r in screen.refinements(rows([0.0, 0.0, 0.0])))
    result = screen.refinements(rows([50.0, 51.0, 53.0]))
    assert result[0]["absolute_change"] == 1.0 and result[0]["relative_change"] == 0.02
    assert result[1]["relative_change"] == 2 / 51
    assert not any("threshold_met" in r for r in result)
    with pytest.raises(ValueError):
        screen.refinements(list(reversed(rows([1.0, 1.0, 1.0]))))


def test_explicit_result_digest_and_missing_file_fail_closed(tmp_path):
    path = write(tmp_path / "result.json", {"completed": True})
    with pytest.raises(ValueError):
        screen.bind(path, "", {})
    with pytest.raises(ValueError):
        screen.bind(path, "0" * 64, {})
    assert screen.bind(path, screen.digest(path), {}) == path
    with pytest.raises(FileNotFoundError):
        screen.bind(tmp_path / "missing", "0" * 64, {})


@pytest.mark.parametrize("ninner,nodes", screen.LEVELS)
def test_full_mocked_level_blocking_frozen_fields_and_samples(
    tmp_path, clock, monkeypatch, snapshot, ninner, nodes
):
    own = screen.independent.physical_curves(snapshot, nodes)
    monkeypatch.setattr(
        screen, "native_coils", lambda *_: ([], own, dict(position=0.0, tangent=0.0))
    )

    class Field:
        def __init__(self, coils):
            assert coils == []

        def set_points(self, points):
            self.points = points

        def B(self):
            return np.tile([2.0, 0.0, 0.0], (len(self.points), 1))

        def A(self):
            return np.tile([screen.TARGET_FLUX, 0.0, 0.0], (len(self.points), 1))

    monkeypatch.setitem(sys.modules, "simsopt.field", SimpleNamespace(BiotSavart=Field))
    lp = np.tile([1.0, 0.0, 0.0], (nodes, 1))
    monkeypatch.setattr(screen.independent, "loop", lambda *_: (lp, lp.copy()))

    def direct(points, positions, tangents, currents):
        assert np.array_equal(currents, own["currents"])
        return np.tile([2.0, 0.0, 0.0], (len(points), 1)), np.tile(
            [screen.TARGET_FLUX, 0.0, 0.0], (len(points), 1)
        )

    monkeypatch.setattr(screen.independent, "filament_field_and_potential", direct)
    target = dict(
        ninner=ninner,
        B2_scale=screen.B2,
        inner_points=np.tile([1.0, 0.0, 0.0], (3 * ninner * ninner, 1)),
        inner_target=np.tile([1.0, 0.0, 0.0], (3 * ninner * ninner, 1)),
    )
    record = screen.Recorder(tmp_path / "run", 180.0)
    row, arrays = screen.screen_level(snapshot, {}, target, ninner, nodes, record)
    assert row["checks_pass"] and not row["physical_admission"]
    assert row["metrics"]["vector_rms"] == pytest.approx(1 / np.sqrt(screen.B2))
    assert row["metrics"]["flux_limit_met"]
    assert np.array_equal(arrays["inner_B"][:, 0], np.full(3 * ninner * ninner, 2.0))
    assert record.counts["B"] == dict(
        attempted=3 * ninner * ninner // 128, completed=3 * ninner * ninner // 128
    )
    assert record.counts["A"] == dict(attempted=nodes // 128, completed=nodes // 128)
    assert record.counts["independent_BA"] == dict(attempted=2, completed=2)
    assert record.points["independent_BA"] == dict(attempted=128, completed=128)
    assert arrays["B_indices"].shape == arrays["A_indices"].shape == (64,)


@pytest.fixture
def intake_context(tmp_path, snapshot, monkeypatch):
    monkeypatch.setattr(screen, "ROOT", tmp_path)
    refs = {}

    def save(name, value):
        path = write(tmp_path / name, value)
        refs[name] = screen.digest(path)
        return dict(path=str(path), sha256=refs[name])

    input_ref = save(screen.TARGET, dict(reference=True))
    wout_ref = save(screen.WOUT, dict(synthetic=True))
    original = copy.deepcopy(snapshot)
    original["sources"] = dict(input=input_ref, wout=wout_ref)
    save(screen.ORIGINAL, original)
    save(screen.SHAPE52, snapshot)
    trial52, trial598 = selected_trial(snapshot, 52), selected_trial(snapshot, 598)
    save(screen.paired.TRIAL, trial52)
    save(screen.COHERENT, snapshot)
    save(screen.COHERENT_TRIAL, trial598)
    save(screen.COHERENT_RESULT, dict(arms=[{}, dict(fine_selected=trial598)]))
    fields = []
    for s in (0.25, 0.5, 0.75):
        for n in (64, 128):
            path = tmp_path / f"field-{s}-{n}.npz"
            np.savez(path, fixture=np.zeros(1))
            fields.append(
                dict(
                    s=s,
                    n=n,
                    arrays=dict(path=str(path), sha256=screen.digest(path)),
                    checks={
                        k: True
                        for k in (
                            "cartesian",
                            "magnitude",
                            "missing_2pi",
                            "poloidal",
                            "toroidal",
                            "wrong_sign",
                        )
                    },
                )
            )
    index = dict(
        status="completed",
        all_phases_completed=True,
        states=[dict(label="reference-401", errors=[], wout=wout_ref, fields=fields)],
    )
    save(screen.INDEX, index)
    monkeypatch.setattr(screen, "FIXED", refs)
    monkeypatch.setattr(
        screen, "archived_target", lambda archives, n: dict(B2_scale=screen.B2, ninner=n)
    )
    calls = []

    def selected(report, folder, arm, sources, width):
        calls.append((arm, width))
        return copy.deepcopy(snapshot), dict(selected_index=598 if arm == "coherent" else 12)

    monkeypatch.setattr(screen, "selected_snapshot", selected)
    restart = dict(
        kind="matched-absolute-box-coherent-restarts",
        seed_sha256=refs[screen.COHERENT],
        center_sha256=refs[screen.SHAPE52],
        arms=[dict(arm="control"), dict(arm="expanded-low")],
    )
    path = write(tmp_path / "restart/result.json", restart)
    return path, restart, calls, index


def test_intake_prospectively_keeps_all_five_and_qualified_target_levels(intake_context):
    path, _, calls, _ = intake_context
    _, targets, states, sources = screen.intake(path, screen.digest(path))
    assert [s["label"] for s in states] == list(screen.LABELS)
    assert list(targets) == [32, 64] and len(sources) == len(screen.FIXED) + 7
    assert calls == [("coherent", 3), ("control", 4), ("expanded-low", 4)]


@pytest.mark.parametrize(
    "fault",
    [
        "kind",
        "seed",
        "center",
        "order",
        "missing",
        "target-label",
        "target-wout",
        "target-grid",
        "target-check",
    ],
)
def test_intake_pairing_and_domain_poisoning(intake_context, fault):
    path, restart, _, index = intake_context
    if fault == "kind":
        restart["kind"] = "other"
    if fault == "seed":
        restart["seed_sha256"] = "0" * 64
    if fault == "center":
        restart["center_sha256"] = "0" * 64
    if fault == "order":
        restart["arms"].reverse()
    if fault == "missing":
        restart["arms"].pop()
    if fault == "target-label":
        index["states"][0]["label"] = "selected-401"
    if fault == "target-wout":
        index["states"][0]["wout"]["sha256"] = "0" * 64
    if fault == "target-grid":
        index["states"][0]["fields"].pop()
    if fault == "target-check":
        index["states"][0]["fields"][0]["checks"]["cartesian"] = 1
    write(path, restart)
    write(screen.ROOT / screen.INDEX, index)
    screen.FIXED[screen.INDEX] = screen.digest(screen.ROOT / screen.INDEX)
    with pytest.raises(ValueError):
        screen.intake(path, screen.digest(path))
