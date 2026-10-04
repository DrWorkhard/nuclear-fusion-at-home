"""Frozen-current checks, source poisoning and bounded execution controls."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from fusion_baselines import coil_check as screen
from fusion_baselines import coil_fit as fit

ROOT=Path(__file__).resolve().parents[1]


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

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path

@pytest.mark.parametrize("field", ["scale", "unit_flux", "target_flux", "B2_scale"])
def test_snapshot_normalization_is_exact(snapshot, field):
    snapshot[field] = np.nextafter(snapshot[field], np.inf)
    with pytest.raises(ValueError):
        screen.snapshot_identity(snapshot)

def test_flux_constant_matches_exact_committed_input():
    source = ROOT / screen.TARGET
    assert screen.digest(source) == screen.FIXED[screen.TARGET]
    assert screen.TARGET_FLUX == -screen.read_json(source)["phiedge"]
    # This one-ULP substitution caused real intake to reject all original snapshots.
    assert screen.TARGET_FLUX != -np.pi / 100

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
    monkeypatch.setattr(fit.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(fit.shutil, "disk_usage", lambda _: SimpleNamespace(free=8 * 1024**3))
    return now

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
def intake_context(tmp_path, monkeypatch):
    monkeypatch.setattr(screen, "ROOT", tmp_path)
    refs = {}

    def save(name, value):
        path = write(tmp_path / name, value)
        refs[name] = screen.digest(path)
        return dict(path=str(path), sha256=refs[name])

    save(screen.TARGET, dict(reference=True, phiedge=-screen.TARGET_FLUX))
    wout_ref = save(screen.WOUT, dict(synthetic=True))
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
    return index


def test_intake_loads_only_the_fixed_target(intake_context):
    data, targets, sources = screen.intake()
    assert data["phiedge"] == -screen.TARGET_FLUX
    assert list(targets) == [32, 64] and len(sources) == 9


@pytest.mark.parametrize("fault", ["label", "wout", "grid", "check", "flux", "bytes"])
def test_intake_source_poisoning(intake_context, fault):
    index = intake_context
    state = index["states"][0]
    if fault == "label":
        state["label"] = "selected-401"
    elif fault == "wout":
        state["wout"]["sha256"] = "0" * 64
    elif fault == "grid":
        state["fields"].pop()
    elif fault == "check":
        state["fields"][0]["checks"]["cartesian"] = 1
    elif fault == "flux":
        target = write(screen.ROOT/screen.TARGET,
                       dict(phiedge=np.nextafter(-screen.TARGET_FLUX, np.inf)))
        screen.FIXED[screen.TARGET] = screen.digest(target)
    elif fault == "bytes":
        Path(state["fields"][0]["arrays"]["path"]).write_bytes(b"corrupt")
    path = write(screen.ROOT/screen.INDEX, index)
    screen.FIXED[screen.INDEX] = screen.digest(path)
    with pytest.raises(ValueError):
        screen.intake()
