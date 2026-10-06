import json

import netCDF4
import numpy as np
import pytest

from fusion_baselines.realized_field import Target, summarize, winding


def torus(iota=-0.55, radius=1.0, minor=0.1, ns=11):
    """Circular torus with nested circles: R = R0 + r(s) cos theta, Z = r(s) sin theta."""
    rows = np.sqrt(np.linspace(0, 1, ns)) * minor
    rmnc = np.column_stack((np.full(ns, radius), rows))
    return Target([0, 1], [0, 0], rmnc, np.column_stack((np.zeros(ns), rows)), np.full(ns, iota))


def helix(target, s, turns=5.0, n=20001):
    phi = np.linspace(0, 2 * np.pi * turns, n)
    theta = target.iota(s) * phi
    r, z = target.rz(s, theta, phi)
    return np.column_stack((r * np.cos(phi), r * np.sin(phi), z))


@pytest.mark.parametrize("iota", [-0.59, -0.25, 0.3, 1.7])
def test_winding_recovers_transform_and_transits_including_sign(iota):
    target = torus(iota)
    transits, measured = winding(helix(target, 0.5), target)
    assert transits == pytest.approx(5.0, rel=1e-12)
    assert measured == pytest.approx(iota, rel=1e-10)


def test_reversed_line_direction_keeps_transform():
    target = torus(-0.59)
    _, forward = winding(helix(target, 0.7), target)
    _, backward = winding(helix(target, 0.7)[::-1], target)
    assert backward == pytest.approx(forward, rel=1e-12)


def test_target_surfaces_axis_and_wout_round_trip(tmp_path):
    target = torus()
    r, z = target.rz(1.0, np.array([0.0, np.pi / 2]), np.zeros(2))
    np.testing.assert_allclose(r, [1.1, 1.0], atol=1e-15)
    np.testing.assert_allclose(z, [0.0, 0.1], atol=1e-15)
    np.testing.assert_allclose(target.axis(np.array([0.3])), [[1.0], [0.0]], atol=1e-15)
    path = tmp_path / "wout_test.nc"
    with netCDF4.Dataset(path, "w") as data:
        data.createDimension("radius", target.ns)
        data.createDimension("mn_mode", 2)
        data.createVariable("lasym__logical__", "i4")[...] = 0
        for name, dims in (("xm", ("mn_mode",)), ("xn", ("mn_mode",)), ("iotaf", ("radius",)),
                           ("rmnc", ("radius", "mn_mode")), ("zmns", ("radius", "mn_mode"))):
            data.createVariable(name, "f8", dims)[...] = getattr(target, name)
    loaded = Target.from_wout(path)
    assert len(loaded.sha256) == 64
    np.testing.assert_array_equal(loaded.rmnc, target.rmnc)
    assert loaded.iota(0.5) == target.iota(0.5)


def test_invalid_inputs_are_rejected():
    with pytest.raises(ValueError):
        Target([0], [0], [[1.0]], [[0.0], [0.0]], [0.5, 0.5])
    with pytest.raises(ValueError):
        torus().rz(1.5, 0.0, 0.0)
    with pytest.raises(ValueError):
        winding(np.zeros((1, 3)), torus())


def test_summary_requires_every_line_confined_and_matching():
    good = [dict(transits=200., left_target=False, iota_traced=-0.59, iota_target=-0.587)] * 3
    assert summarize(good, 200)["all_confined_and_iota_matching"] is True
    escaped = good[:2] + [dict(good[0], transits=5., left_target=True)]
    assert summarize(escaped, 200)["lines_confined"] == 2
    assert summarize(escaped, 200)["all_confined_and_iota_matching"] is False
    shifted = [dict(transits=200., left_target=False, iota_traced=-0.62, iota_target=-0.587)]
    assert summarize(shifted, 200)["all_confined_and_iota_matching"] is False
    assert summarize(good, 200)["physical_admission"] is False


def test_summary_rejects_opposite_sign_and_short_traces():
    good = dict(transits=200., left_target=False, iota_traced=-0.59, iota_target=-0.59)
    flipped = summarize([dict(good, iota_traced=0.59)], 200)
    assert flipped["max_abs_iota_mismatch"] == pytest.approx(1.18)
    assert not flipped["all_confined_and_iota_matching"]
    short = summarize([dict(good, transits=199.99)], 200)
    assert short["lines_completing_transits"] == 0
    assert not short["all_confined_and_iota_matching"]
    assert not summarize([good], 200)["nestedness_tested"]
    with pytest.raises(ValueError, match="nonempty"):
        summarize([], 200)
    with pytest.raises(ValueError, match="finite trace"):
        summarize([dict(good, transits=float("nan"))], 200)


def test_transit_stop_is_not_an_escape_and_time_cap_cannot_pass(monkeypatch):
    from simsopt import geo
    from simsopt.field import tracing

    from fusion_baselines.realized_field import trace

    target = torus()
    def compute(field, starts, z, **kwargs):
        assert len(kwargs["stopping_criteria"]) == 2
        paths = []
        for turns in (5., 0.5):
            xyz = helix(target, 0.5, turns=turns)
            paths.append(np.column_stack((np.arange(len(xyz)), xyz)))
        endpoint = paths[0][-1]
        paths[0] = paths[0][:-1]  # Native paths omit the stopping event itself.
        return paths, [np.array([[endpoint[0], -2, *endpoint[1:]]]), np.empty((0, 5))]
    monkeypatch.setattr(tracing, "compute_fieldlines", compute)
    monkeypatch.setattr(tracing, "LevelsetStoppingCriterion", lambda value: value)
    monkeypatch.setattr(geo, "SurfaceClassifier", lambda *a, **k: type(
        "Classifier", (), {"dist": staticmethod(lambda *a: 1.)})())
    lines, _ = trace(None, target, None, transits=5, s_values=(0.5, 0.5))
    assert not any(line["left_target"] for line in lines)
    assert [line["termination"] for line in lines] == ["requested_transits", "integration_limit"]
    assert not summarize(lines, 5)["all_confined_and_iota_matching"]


def test_wout_target_binding_rejects_wrong_period_before_loading_surfaces(tmp_path):
    path = tmp_path / "wrong-period.nc"
    with netCDF4.Dataset(path, "w") as data:
        data.createVariable("nfp", "i4")[...] = 3
    with pytest.raises(ValueError, match="symmetric nfp2"):
        Target.from_wout(path, target_input={})


def test_native_toroidal_field_completes_requested_transits_without_escape():
    from simsopt.field import ToroidalField
    from simsopt.geo import SurfaceRZFourier

    from fusion_baselines.realized_field import trace

    surface = SurfaceRZFourier.from_nphi_ntheta(32, 32, nfp=2, mpol=1, ntor=0)
    surface.set_rc(0, 0, 1.)
    surface.set_rc(1, 0, .1)
    surface.set_zs(1, 0, .1)
    lines, _ = trace(ToroidalField(1., 1.), torus(iota=0.), surface,
                     transits=3, s_values=(.25,))
    assert lines[0]["termination"] == "requested_transits"
    assert summarize(lines, 3)["all_confined_and_iota_matching"]
    json.dumps(dict(lines=lines, summary=summarize(lines, 3)))


def test_summary_with_numpy_transit_counts_is_json_serializable():
    line = dict(transits=np.float64(200.1), left_target=False,
                iota_traced=-.59, iota_target=-.59)
    report = json.loads(json.dumps(summarize([line], 200)))
    assert report["lines_completing_transits"] == 1
    assert report["all_confined_and_iota_matching"] is True


def test_exact_containment_on_circular_section():
    from fusion_baselines.realized_field import inside_target

    target = torus()  # R0 = 1, minor radius 0.1
    phi = 0.3
    points = [[r*np.cos(phi), r*np.sin(phi), z] for r, z in
              ((1.05, 0.0), (1.0999, 0.0), (1.1001, 0.0), (1.0, 0.0995), (1.0, -0.1005))]
    assert inside_target(target, points).tolist() == [True, True, False, True, False]


def test_classifier_stop_inside_target_is_not_reported_as_an_exit(monkeypatch):
    from simsopt import geo
    from simsopt.field import tracing

    from fusion_baselines.realized_field import trace

    target = torus()

    def compute(field, starts, z, **kwargs):
        paths, hits = [], []
        for radius in (1.09, 1.2):  # stop point inside, then truly outside the section
            xyz = helix(target, 0.5, turns=0.4)
            end = np.arctan2(xyz[-1, 1], xyz[-1, 0])
            stop = [radius*np.cos(end), radius*np.sin(end), 0.0]
            paths.append(np.column_stack((np.arange(len(xyz)), xyz)))
            hits.append(np.array([[len(xyz), -1, *stop]]))
        return paths, hits

    monkeypatch.setattr(tracing, "compute_fieldlines", compute)
    monkeypatch.setattr(tracing, "LevelsetStoppingCriterion", lambda value: value)
    monkeypatch.setattr(geo, "SurfaceClassifier", lambda *a, **k: type(
        "Classifier", (), {"dist": staticmethod(lambda *a: 1.)})())
    lines, _ = trace(None, target, None, transits=5, s_values=(0.5, 0.5))
    assert [line["termination"] for line in lines] == ["classifier_stop_inside_target", "boundary"]
    assert [line["left_target"] for line in lines] == [False, True]
    summary = summarize(lines, 5)
    assert summary["classifier_stops_inside_target"] == 1
    assert summary["lines_confined"] == 0 and not summary["all_confined_and_iota_matching"]
