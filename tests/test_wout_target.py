import json

import netCDF4
import numpy as np
import pytest

from fusion_baselines import wout_target
from fusion_baselines.coil_check import ROOT, TARGET


def write_wout(path, data, boundary_shift=0.0, ns=401, nfp=2):
    """Minimal Wout carrying only the input boundary on every surface."""
    modes = sorted({(r["m"], r["n"]) for key in ("rbc", "zbs") for r in data[key]})
    rbc = {(r["m"], r["n"]): r["value"] for r in data["rbc"]}
    zbs = {(r["m"], r["n"]): r["value"] for r in data["zbs"]}
    with netCDF4.Dataset(path, "w") as out:
        out.createDimension("radius", ns)
        out.createDimension("mn_mode", len(modes))
        out.createVariable("ns", "i4")[...] = ns
        out.createVariable("nfp", "i4")[...] = nfp
        out.createVariable("lasym__logical__", "i4")[...] = 0
        out.createVariable("xm", "f8", ("mn_mode",))[...] = [m for m, _ in modes]
        out.createVariable("xn", "f8", ("mn_mode",))[...] = [2*n for _, n in modes]
        phi = out.createVariable("phi", "f8", ("radius",))
        phi[...] = np.linspace(0, data["phiedge"], ns)
        for name, source in (("rmnc", rbc), ("zmns", zbs)):
            row = np.array([source.get(mode, 0.0) for mode in modes])
            row[0] += boundary_shift if name == "rmnc" else 0.0
            out.createVariable(name, "f8", ("radius", "mn_mode"))[...] = np.tile(row, (ns, 1))


@pytest.fixture
def data():
    return json.loads((ROOT/TARGET).read_text())


def test_archives_reject_boundary_and_resolution_mismatch(tmp_path, data):
    shifted, coarse = tmp_path/"shifted.nc", tmp_path/"coarse.nc"
    write_wout(shifted, data, boundary_shift=1e-9)
    write_wout(coarse, data, ns=101)
    with pytest.raises(ValueError, match="boundary differs"):
        wout_target.archives(shifted, data)
    with pytest.raises(ValueError, match="401-surface"):
        wout_target.archives(coarse, data)


def test_starter_errors_are_zero_for_published_samples_and_detect_changes():
    starter = json.loads((ROOT/wout_target.STARTER).read_text())
    inner = starter["groups"]["inner"]
    points = np.zeros((inner["original_count"], 3))
    target = np.zeros_like(points)
    points[inner["indices"]] = inner["points_m"]
    target[inner["indices"]] = inner["target_B_T"]
    exact = dict(inner_points=points, inner_target=target)
    assert wout_target.starter_errors(exact, starter) == dict(inner_points=0.0, inner_target=0.0)
    target[inner["indices"][5], 1] *= 1 + 1e-6
    assert wout_target.starter_errors(exact, starter)["inner_target"] > 1e-8


def test_candidate_snapshot_is_flux_normalized_and_rejects_relabelled_input(data):
    pytest.importorskip("simsopt")
    from fusion_baselines import coil_check

    seed = json.loads((ROOT/"examples/clear-coil-samples-v1/candidate.json").read_text())
    snapshot = coil_check.candidate_snapshot(seed, data)
    coil_check.snapshot_identity(snapshot)
    assert snapshot["scale"] == coil_check.TARGET_FLUX / snapshot["unit_flux"]
    # The public seed current is its own flux-normalized current.
    assert 1e5*snapshot["scale"] == pytest.approx(294966.46632221737, rel=1e-12)
    assert [row["current"] < 0 for row in snapshot["physical"]] == [
        row["flip"] for row in snapshot["physical"]]
    relabelled = dict(seed, parameter_names=list(reversed(seed["parameter_names"])))
    with pytest.raises(ValueError, match="Canonical"):
        coil_check.candidate_snapshot(relabelled, data)


def test_wrong_period_is_rejected_before_boundary_sampling(tmp_path, data):
    path = tmp_path / "wrong-period.nc"
    write_wout(path, data, nfp=3, boundary_shift=1e-3)
    with pytest.raises(ValueError, match="symmetric nfp2"):
        wout_target.archives(path, data)


@pytest.mark.parametrize("change", [
    {"case_id": "another-target"}, {"schema_version": 2}, {"extra": 1},
    {"base_coefficients": []}, {"base_coefficients": [[[float("nan")]*11]*3]*6},
    {"base_coefficients": [[[11.0]*11]*3]*6},
])
def test_candidate_snapshot_rejects_invalid_public_contract(data, change):
    from fusion_baselines.coil_check import candidate_snapshot

    seed = json.loads((ROOT/"examples/clear-coil-samples-v1/candidate.json").read_text())
    with pytest.raises(ValueError):
        candidate_snapshot(dict(seed, **change), data)


def test_selected_candidate_conversion_rejects_reference_input(data):
    from fusion_baselines import coil_check

    candidate = json.loads((ROOT/"submissions/length-headroom-six-coil/candidate.json").read_text())
    with pytest.raises(ValueError, match="exact target input"):
        coil_check.candidate_snapshot(candidate, data, target_id="selected401")
    spec = coil_check.target_spec("selected401")
    selected = coil_check.read_json(ROOT/spec["input"])
    snapshot = coil_check.candidate_snapshot(candidate, selected, target_id="selected401")
    coil_check.snapshot_identity(snapshot, "selected401")
    assert snapshot["target_id"] == "selected401"
    assert snapshot["B2_scale"] == spec["B2"]
    assert snapshot["base_coefficients"] == candidate["base_coefficients"]
