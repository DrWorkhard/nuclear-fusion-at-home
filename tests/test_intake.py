from __future__ import annotations

import hashlib

import netCDF4
import numpy as np

from fusion_baselines.intake import summarize_equilibrium_manifest


def _digest(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest(wout, boozer) -> dict:
    return {
        "schema_version": 1,
        "case_id": "arbitrary-new-configuration",
        "kind": "open_qi",
        "source": {"url": "https://example.test/data", "citation": "Test et al."},
        "conventions": {
            "length_unit": "m",
            "field_unit": "T",
            "coordinate_system": "VMEC",
            "current_sign": "right-hand rule",
        },
        "equilibrium": {
            "nfp": 3,
            "mpol": 7,
            "ntor": 5,
            "ns": 4,
            "free_boundary": False,
        },
        "files": [
            {"role": "vmec_output", "path": wout.name, "sha256": _digest(wout)},
            {"role": "boozer_output", "path": boozer.name, "sha256": _digest(boozer)},
        ],
    }


def test_generic_equilibrium_intake_has_no_case_dispatch(tmp_path):
    wout = tmp_path / "wout.nc"
    with netCDF4.Dataset(wout, "w") as dataset:
        dataset.createDimension("radius", 4)
        for name, value in {"nfp": 3, "mpol": 7, "ntor": 5, "ns": 4}.items():
            dataset.createVariable(name, "i4").assignValue(value)
        for name, value in {
            "aspect": 8.0,
            "volume_p": 2.5,
            "betatotal": 0.01,
            "lfreeb": 0,
        }.items():
            dataset.createVariable(name, "f8").assignValue(value)
        dataset.createVariable("iotaf", "f8", ("radius",))[:] = [0.4, 0.5, 0.6, 0.7]
    boozer = tmp_path / "boozmn.nc"
    with netCDF4.Dataset(boozer, "w") as dataset:
        dataset.createDimension("mode", 3)
        dataset.createVariable("nfp_b", "i4").assignValue(3)
        dataset.createVariable("ns_b", "i4").assignValue(4)
        dataset.createVariable("ixm_b", "i4", ("mode",))[:] = [0, 1, 2]

    result = summarize_equilibrium_manifest(_manifest(wout, boozer), tmp_path)
    assert result["case_id"] == "arbitrary-new-configuration"
    assert result["expected_metadata_matches"] is True
    assert result["vmec"]["iota_edge"] == 0.7
    assert result["boozer"] == {"nfp": 3, "ns": 4, "mode_count": 3}
    assert np.isfinite(result["vmec"]["volume_m3"])
