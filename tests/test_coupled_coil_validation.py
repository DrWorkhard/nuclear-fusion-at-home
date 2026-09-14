"""Synthetic fixed-current/stokes/workflow checks; never load a physical target."""

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_coupled_coil_pilot as validation  # noqa: E402

from fusion_baselines.coupled_coil_audit import parameter_names  # noqa: E402
from fusion_baselines.coupled_coil_workflow import cases  # noqa: E402


def toy_snapshot():
    nbase, order, scale = 6, 5, 0.25
    unit_flux = -2 * np.pi * 0.4 * (1 - np.sqrt(1 - 0.2**2))
    value = dict(
        schema_version=1,
        nfp=2,
        nbase=nbase,
        order=order,
        scale=scale,
        unit_flux=unit_flux,
        target_flux=scale * unit_flux,
        B2_scale=7.0,
        names=parameter_names(nbase, order),
        base_coefficients=np.zeros((nbase, 3, 2 * order + 1)).tolist(),
        physical=[],
    )
    for period in range(2):
        c, s = np.cos(np.pi * period), np.sin(np.pi * period)
        rotation = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
        for flip in (False, True):
            matrix = rotation.T @ (np.diag([1, -1, -1]) if flip else np.eye(3))
            for base in range(nbase):
                value["physical"].append(
                    dict(
                        base_index=base,
                        period=period,
                        flip=flip,
                        matrix=matrix.tolist(),
                        current=1e5 * scale * (-1 if flip else 1),
                    )
                )
    return value


class ToroidalField:
    def set_points(self, points):
        self.points = points

    def B(self):
        p = self.points
        r2 = p[:, 0] ** 2 + p[:, 1] ** 2
        return 0.4 * np.column_stack((-p[:, 1] / r2, p[:, 0] / r2, np.zeros(len(p))))

    def A(self):
        p = self.points
        return np.column_stack(
            (np.zeros(len(p)), np.zeros(len(p)), -0.4 * np.log(np.hypot(p[:, 0], p[:, 1])))
        )


class CircleModel:
    def __init__(self, snapshot):
        self.ncoil = 128
        self.names = snapshot["names"]
        self.x = np.ravel(snapshot["base_coefficients"])

    def loop(self, count):
        theta = 2 * np.pi * np.arange(count) / count
        points = np.column_stack((1 + 0.2 * np.cos(theta), np.zeros(count), 0.2 * np.sin(theta)))
        tangent = (
            2
            * np.pi
            * np.column_stack((-0.2 * np.sin(theta), np.zeros(count), 0.2 * np.cos(theta)))
        )
        return points, tangent

    def evaluate(self, *args, **kwargs):
        raise AssertionError("flux diagnostics must not request an optimization bundle")


def test_all_registered_levels_and_frozen_field_resolution_pairs():
    rows = validation.validation_levels()
    assert len(rows) == 7
    assert len({r["label"] for r in rows}) == 7
    assert [(r["nphi"], r["ncoil"], r["offset"]) for r in rows[:4]] == [
        (64, 256, 0),
        (128, 256, 0),
        (128, 512, 0),
        (128, 512, 0.5),
    ]
    assert [(r["ninner"], r["ncoil"]) for r in rows[4:]] == [(32, 256), (64, 256), (64, 512)]


def test_analytic_toroidal_circle_stokes_sign_and_frozen_scale(tmp_path, monkeypatch):
    snapshot = toy_snapshot()
    model = CircleModel(snapshot)
    monkeypatch.setattr(validation, "_native_field", lambda m: ToroidalField())
    result = validation.flux_diagnostics(model, model.x, snapshot, tmp_path / "flux")
    assert result["status"] == "completed"
    assert result["full_bundles"] == 0
    assert not result["transfer_pass"] and not result["step4_pass"]
    assert result["scale"] == 0.25 and result["B2_scale"] == 7
    assert len(result["native_calls"]) == 18
    assert all(r["status"] == "completed" for r in result["native_calls"])
    assert [r["ntheta"] for r in result["lines"]] == [256, 512, 1024]
    assert [(r["nrho"], r["ntheta"]) for r in result["areas"]] == [
        (n, t) for n in (16, 32) for t in (256, 512, 1024)
    ]
    for row in result["lines"] + result["areas"]:
        assert row["flux"] < 0
        assert abs(row["flux"] / snapshot["target_flux"] - 1) < 1e-13
        with np.load(validation.checked(row["arrays"]), allow_pickle=False) as raw:
            assert {"points", "B", "A"} <= set(raw.files)
            direct = ToroidalField()
            direct.set_points(raw["points"])
            np.testing.assert_array_equal(raw["B"], 0.25 * direct.B())
            np.testing.assert_array_equal(raw["A"], 0.25 * direct.A())
    assert json.loads((tmp_path / "flux/run.json").read_text()) == result


def test_fan_orientation_follows_parametrized_loop():
    model = CircleModel(toy_snapshot())
    points, normals = validation.signed_fan(model, 16, 256)
    assert np.all(points[:, 0] > 0) and np.all(normals[:, 1] < 0)
    assert abs(normals[:, 1].sum() + np.pi * 0.2**2) < 1e-15
    original = model.loop

    def reverse(count):
        points, tangent = original(count)
        points[:, 2] *= -1
        tangent[:, 2] *= -1
        return points, tangent

    model.loop = reverse
    _, reversed_normals = validation.signed_fan(model, 32, 512)
    assert np.all(reversed_normals[:, 1] > 0)


def test_invalid_fan_does_not_drop_predeclared_records(tmp_path, monkeypatch):
    snapshot = toy_snapshot()
    model = CircleModel(snapshot)
    original = model.loop

    def degenerate(count):
        points, tangent = original(count)
        tangent[0] = 0
        return points, tangent

    model.loop = degenerate
    monkeypatch.setattr(validation, "_native_field", lambda m: ToroidalField())
    result = validation.flux_diagnostics(model, model.x, snapshot, tmp_path / "failed")
    assert result["status"] == "error"
    assert len(result["lines"]) == 3 and len(result["areas"]) == 6
    assert all(r["status"] == "error" for r in result["areas"])
    assert all("flux" not in r and "arrays" not in r for r in result["areas"])
    assert len(result["native_calls"]) == 6


def test_flux_native_failure_retains_later_attempts(tmp_path, monkeypatch):
    snapshot = toy_snapshot()
    model = CircleModel(snapshot)

    class BadField(ToroidalField):
        def B(self):
            if len(self.points) == 512:
                return np.full_like(self.points, np.nan)
            return super().B()

    monkeypatch.setattr(validation, "_native_field", lambda m: BadField())
    result = validation.flux_diagnostics(model, model.x, snapshot, tmp_path / "failed")
    assert result["status"] == "error"
    assert [r["status"] for r in result["lines"]] == ["completed", "error", "completed"]
    assert all(r["status"] == "completed" for r in result["areas"])
    assert len(result["native_calls"]) == 17
    assert any(r["status"] == "error" for r in result["native_calls"])


def test_flux_constructor_failure_still_records_all_grids(tmp_path, monkeypatch):
    snapshot = toy_snapshot()
    model = CircleModel(snapshot)

    def failed(model):
        raise RuntimeError("synthetic native initialization failure")

    monkeypatch.setattr(validation, "_native_field", failed)
    result = validation.flux_diagnostics(model, model.x, snapshot, tmp_path / "failed")
    assert result["status"] == "error"
    assert len(result["lines"]) == 3 and len(result["areas"]) == 6
    assert all(r["status"] == "error" for r in result["lines"] + result["areas"])
    assert result["native_calls"] == []


def test_flux_disk_reserve_failure_retains_complete_attempt_matrix(tmp_path, monkeypatch):
    snapshot = toy_snapshot()
    model = CircleModel(snapshot)
    monkeypatch.setattr(validation, "_native_field", lambda m: ToroidalField())

    def insufficient(*args):
        raise OSError("synthetic insufficient free space")

    monkeypatch.setattr(validation, "space_check", insufficient)
    result = validation.flux_diagnostics(model, model.x, snapshot, tmp_path / "failed")
    assert result["status"] == "error" and "resource_terminal_error" in result
    assert len(result["lines"]) == 3 and len(result["areas"]) == 6
    assert result["native_calls"] == []
    assert result["minimum_observed_free_bytes"] is None


@pytest.mark.parametrize("mutation", ["coordinates", "names", "scale", "source_grid"])
def test_frozen_identity_cannot_change(tmp_path, mutation):
    snapshot = toy_snapshot()
    model = CircleModel(snapshot)
    x = model.x.copy()
    if mutation == "coordinates":
        x[0] += 1e-7
    elif mutation == "names":
        model.names = list(reversed(model.names))
    elif mutation == "scale":
        snapshot["scale"] = 0.5
    else:
        model.ncoil = 256
    with pytest.raises(ValueError):
        validation.flux_diagnostics(model, x, snapshot, tmp_path / "forbidden")
    assert not (tmp_path / "forbidden").exists()


def search_fixture(tmp_path):
    snapshot = toy_snapshot()
    validation.save_json(tmp_path / "snapshot.json", snapshot)
    row = dict(
        status="completed",
        J=1.0,
        x=np.ravel(snapshot["base_coefficients"]).tolist(),
        metrics={k: snapshot[k] for k in ("scale", "unit_flux", "target_flux", "B2_scale")},
        snapshot=validation.reference(tmp_path / "snapshot.json"),
    )
    source, search_ref = {"synthetic": True}, {"path": "synthetic", "sha256": "test"}
    search = dict(
        status="completed",
        phase="search",
        source=source,
        case=cases()[0],
        names=snapshot["names"],
        rows=[row],
        selected=0,
    )
    audit = dict(
        status="completed",
        phase="search",
        source=source,
        case=search["case"],
        search=search_ref,
        arithmetic_and_source_pass=True,
        search_pass=True,
    )
    return search, search_ref, audit, source


def test_selected_construction_snapshot_retained_exactly(tmp_path):
    search, ref, audit, source = search_fixture(tmp_path)
    row, snapshot = validation.selected_source(search, ref, audit, source)
    assert row is search["rows"][0]
    assert snapshot == toy_snapshot()


@pytest.mark.parametrize("mutation", ["audit", "source", "index", "scale", "denominator", "x"])
def test_bad_search_prerequisite_rejected(tmp_path, mutation):
    search, ref, audit, source = search_fixture(tmp_path)
    if mutation == "audit":
        audit["search_pass"] = False
    elif mutation == "source":
        audit["source"] = {"different": True}
    elif mutation == "index":
        search["selected"] = True
    elif mutation in ("scale", "denominator"):
        search["rows"][0]["metrics"]["scale" if mutation == "scale" else "B2_scale"] *= 2
    else:
        search["rows"][0]["x"][0] += 1
    with pytest.raises(ValueError):
        validation.selected_source(search, ref, audit, source)


def test_array_evidence_exclusive_and_json_strict(tmp_path):
    path = tmp_path / "raw.npz"
    validation.save_arrays(path, {"x": [1.0, 2.0]})
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        validation.save_arrays(path, {"x": [3.0]})
    assert path.read_bytes() == before
    with pytest.raises(ValueError):
        validation.save_arrays(tmp_path / "nan.npz", {"x": [np.nan]})
    assert not (tmp_path / "nan.npz").exists()
    assert validation.json_value({"n": np.int64(2), "x": np.array([0.5])}) == {"n": 2, "x": [0.5]}
    for value in (np.nan, np.inf, {1: "not a string"}, object()):
        with pytest.raises(ValueError):
            validation.json_value(copy.deepcopy(value))


@pytest.mark.parametrize(
    "message",
    [
        "strictly positive speed not certified between curve nodes",
        "detected coincident non-endpoint filament positions within roundoff",
        "zero-speed filament",
        "degenerate zero-speed curve",
    ],
)
def test_recognized_geometry_failure_is_uncertified_not_a_physical_pass(
    tmp_path, monkeypatch, message
):
    def unavailable(*args):
        raise ValueError(message)

    monkeypatch.setattr(validation, "geometry_certificates", unavailable)
    result = validation.geometry_diagnostics(toy_snapshot(), "synthetic", tmp_path)
    assert result == dict(
        status="uncertified", error=f"ValueError: {message}", certificate_available=False
    )
    assert not (tmp_path / "geometry.json").exists()


def test_unknown_geometry_error_is_not_relabelled_as_completed(tmp_path, monkeypatch):
    def broken(*args):
        raise ValueError("unexpected malformed surface")

    monkeypatch.setattr(validation, "geometry_certificates", broken)
    result = validation.geometry_diagnostics(toy_snapshot(), "synthetic", tmp_path)
    assert result["status"] == "error"


def test_geometry_record_preserved_without_producer_admission(tmp_path, monkeypatch):
    measured = dict(geometry_pass=False, ncoil=1024)
    monkeypatch.setattr(validation, "geometry_certificates", lambda *args: measured)
    result = validation.geometry_diagnostics(toy_snapshot(), "synthetic", tmp_path)
    assert result["status"] == "completed"
    assert json.loads(validation.checked(result["result"]).read_text()) == measured
    assert "entry_pass" not in result


@pytest.mark.parametrize("fail_first", [False, True])
def test_full_diagnostic_driver_freezes_source_and_attempts_every_level(
    tmp_path, monkeypatch, fail_first
):
    import coupled_coil_inputs

    from fusion_baselines import coupled_coils

    search, _, audit, source = search_fixture(tmp_path)
    snapshot = toy_snapshot()
    search["seed_x"] = search["rows"][0]["x"].copy()
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        monkeypatch.setenv(name, "1")
    target_input, target_wout = tmp_path / "input.json", tmp_path / "wout"
    validation.save_json(target_input, {"synthetic": True})
    validation.save_json(target_wout, {"synthetic": True})
    source["targets"] = dict(
        reference=dict(
            input=validation.reference(target_input), wout=validation.reference(target_wout)
        )
    )
    search_path, audit_path = tmp_path / "search.json", tmp_path / "audit.json"
    validation.save_json(search_path, search)
    audit["search"] = validation.reference(search_path)
    validation.save_json(audit_path, audit)
    monkeypatch.setattr(coupled_coil_inputs, "sources", lambda root: source)
    requested, fluxes = [], []

    class Field:
        def B(self):
            return np.ones((4, 3))

        A = B

    class Model:
        def __init__(self, wout, target, nbase, order, method, **level):
            requested.append(level)
            if fail_first and len(requested) == 1:
                raise RuntimeError("synthetic first-level failure")
            self.ncoil = level["ncoil"]
            self.names = snapshot["names"]
            self.initialization_work = dict(seed_A_calls=1, seed_A_points=256)
            self.field = self.inner_field = self.loop_field = Field()

        def diagnostics(self, x, scale, B2_scale):
            assert scale == snapshot["scale"] and B2_scale == snapshot["B2_scale"]
            self.x = x
            return dict(scale=scale, B2_scale=B2_scale, frozen_scale=True)

        def arrays(self, x, scale, B2_scale):
            assert scale == snapshot["scale"] and B2_scale == snapshot["B2_scale"]
            np.testing.assert_array_equal(x, np.ravel(snapshot["base_coefficients"]))
            return dict(boundary_B=scale * np.ones((4, 3)))

        def evaluate(self, *args, **kwargs):
            raise AssertionError("validation must never optimize or recalibrate")

    def flux(model, x, frozen, output, ncoil):
        fluxes.append((frozen, ncoil))
        assert frozen == snapshot and model.ncoil == 512
        return dict(status="completed", ncoil=ncoil)

    monkeypatch.setattr(coupled_coils, "CoupledCoils", Model)
    monkeypatch.setattr(validation, "flux_diagnostics", flux)
    monkeypatch.setattr(
        validation,
        "geometry_diagnostics",
        lambda *args: dict(
            status="uncertified",
            certificate_available=False,
            error="ValueError: strictly positive speed not certified between curve nodes",
        ),
    )
    run = validation.validate(search_path, audit_path, tmp_path / "validation")
    assert len(requested) == len(run["rows"]) == 7
    assert len(fluxes) == 1
    assert run["snapshot"] == search["rows"][0]["snapshot"]
    assert run["seed_x"] == search["seed_x"]
    assert run["status"] == ("error" if fail_first else "completed")
    assert all(r["status"] == "completed" for r in run["rows"][1:])
    assert run["full_bundles"] == run["equilibrium_solves"] == 0
    assert not any(run[k] for k in ("entry_pass", "transfer_pass", "step4_pass"))
    assert json.loads((tmp_path / "validation/run.json").read_text()) == run
