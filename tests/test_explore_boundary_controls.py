"""Representation-only controls; no real fixture or native field calls."""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "explore_boundary_controls", ROOT / "scripts/explore_boundary_controls.py")
experiment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(experiment)


@pytest.fixture
def imports(monkeypatch):
    pytest.importorskip("simsopt")
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    from simsopt.field import Current, coils_via_symmetries
    from simsopt.geo import CurveXYZFourier, SurfaceXYZTensorFourier

    return Current, coils_via_symmetries, CurveXYZFourier, SurfaceXYZTensorFourier


@pytest.mark.parametrize("regularization", [None, [0.02]])
def test_requadrature_preserves_named_coils(imports, regularization):
    Current, symmetries, Curve, _ = imports
    curve = Curve(32, 2)
    curve.set("xc(0)", 1.)
    curve.set("xc(1)", .2)
    curve.set("zs(1)", .2)
    original = symmetries([curve], [Current(-7.)], 2, True,
                          regularizations=regularization)
    copied, error = experiment.clone_coils(original, 1, 48)
    assert error == 0.
    assert len(copied) == 4
    assert len(copied[0].curve.quadpoints) == 48
    np.testing.assert_array_equal(copied[0].curve.local_full_x, curve.local_full_x)
    assert [c.current.get_value() for c in copied] == [-7., 7., -7., 7.]
    assert getattr(copied[0], "regularization", None) == (
        None if regularization is None else regularization[0])


@pytest.mark.parametrize("legacy_names", [False, True])
def test_tensor_surface_not_truncated(imports, legacy_names):
    *_, Surface = imports
    source = Surface(nfp=2, stellsym=True, mpol=3, ntor=2)
    if legacy_names:
        source.dofs._names = [f"x{i}" for i in range(len(source.local_full_x))]
    copy = experiment.surface_grid(source, 20, .5)
    assert copy.mpol == 3 and copy.ntor == 2
    assert copy.nfp == 2 and copy.stellsym
    np.testing.assert_array_equal(copy.local_full_x, source.local_full_x)
    for component in ("xcs", "ycs", "zcs"):
        np.testing.assert_array_equal(getattr(copy, component), getattr(source, component))
    np.testing.assert_allclose(copy.quadpoints_phi, (np.arange(20)+.5)/40)
    np.testing.assert_allclose(copy.quadpoints_theta, (np.arange(20)+.5)/20)


def test_fixed_schedule_and_exclusive_output(tmp_path):
    assert experiment.SCHEDULE == ((21, 160, 0.), (42, 160, 0.), (42, 320, 0.),
                                   (84, 320, 0.), (84, 640, 0.), (84, 640, .5))
    path = tmp_path / "result.json"
    experiment.save_json(path, {"passed": False})
    with pytest.raises(FileExistsError):
        experiment.save_json(path, {"passed": True})
    with pytest.raises(FileExistsError):
        experiment.run(tmp_path)
    assert '"passed": false' in path.read_text(encoding="utf-8")


def test_no_field_import_at_module_load():
    assert "BiotSavart" not in experiment.__dict__
    assert sys.modules["fusion_baselines.boundary_control_metrics"] is not None
