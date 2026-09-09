from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import netCDF4
import pytest

from fusion_baselines.cli import main
from fusion_baselines.intake import summarize_equilibrium_manifest
from fusion_baselines.manifest import load_manifest, validate_manifest


def _digest(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_wout(path, *, free_boundary: bool) -> None:
    with netCDF4.Dataset(path, "w") as dataset:
        dataset.createDimension("radius", 5)
        for name, value in {"nfp": 4, "mpol": 8, "ntor": 7, "ns": 5}.items():
            dataset.createVariable(name, "i4").assignValue(value)
        for name, value in {
            "aspect": 10.5,
            "volume_p": 30.0,
            "betatotal": 0.02,
            "lfreeb__logical__": int(free_boundary),
            "version_": 8.52,
            "ier_flag": 0,
            "fsqr": 1e-12,
            "fsqz": 1e-12,
            "fsql": 1e-12,
        }.items():
            dataset.createVariable(name, "f8").assignValue(value)
        dataset.createVariable("iotaf", "f8", ("radius",))[:] = [0.82, 0.84, 0.86, 0.88, 0.9]


def _equilibrium(free_boundary: bool) -> dict:
    prefix = "free_boundary" if free_boundary else "fixed_boundary"
    return {
        "code": "VMEC",
        "version": "8.52",
        "free_boundary": free_boundary,
        "nfp": 4,
        "mpol": 8,
        "ntor": 7,
        "ns": 5,
        "convergence_tolerances": {"fsqr": 1e-10, "fsqz": 1e-10, "fsql": 1e-10},
        "input_role": f"{prefix}_vmec_input",
        "output_role": f"{prefix}_vmec_output",
    }


def _manifest(tmp_path) -> dict:
    fixed_wout = tmp_path / "wout_fixed.nc"
    free_wout = tmp_path / "wout_free.nc"
    _write_wout(fixed_wout, free_boundary=False)
    _write_wout(free_wout, free_boundary=True)
    paths = {
        "fixed_boundary_vmec_input": tmp_path / "input.fixed",
        "fixed_boundary_vmec_output": fixed_wout,
        "free_boundary_vmec_input": tmp_path / "input.free",
        "free_boundary_vmec_output": free_wout,
        "profiles": tmp_path / "profiles.json",
        "coils": tmp_path / "coils.json",
        "currents": tmp_path / "currents.json",
        "mgrid_recipe": tmp_path / "makegrid.json",
        "solver_controls": tmp_path / "controls.json",
        "metadata": tmp_path / "metadata.json",
    }
    for role, path in paths.items():
        if not path.exists():
            path.write_text(f"authoritative fixture for {role}\n")
    files = [
        {
            "role": role,
            "path": path.name,
            "bytes": path.stat().st_size,
            "sha256": _digest(path),
            "origin": "authoritative",
            "source_url": f"https://example.test/squid-c/{path.name}",
        }
        for role, path in paths.items()
    ]
    return {
        "schema_version": 2,
        "case_id": "squid-c-contract-fixture",
        "kind": "squid_c",
        "source": {
            "url": "https://doi.org/10.1017/S0022377825100974",
            "citation": "Goodman et al.",
            "authority": "Author data release",
            "license": "CC-BY-NC-SA-4.0",
            "retrieved_at": "2026-08-31T12:00:00Z",
        },
        "conventions": {
            "length_unit": "m",
            "field_unit": "T",
            "coordinate_system": "right-handed cylindrical R-phi-Z",
            "current_sign": "right-hand rule about increasing curve parameter",
            "toroidal_angle": "geometric phi in radians",
            "poloidal_angle": "VMEC theta",
            "minor_radius_definition": "sqrt(volume/(2*pi^2*major_radius))",
        },
        "scale": {
            "effective_minor_radius_m": 1.7,
            "on_axis_field_T": 5.0,
            "definition": "canonical coil-design scale",
        },
        "symmetry": {
            "nfp": 4,
            "stellarator_symmetry": True,
            "unique_coil_count": 5,
            "full_coil_count": 40,
            "expansion_rule": "reflect by stellarator symmetry, then rotate through four periods",
        },
        "equilibria": {
            "fixed_boundary": _equilibrium(False),
            "coil_generated_free_boundary": _equilibrium(True),
        },
        "files": files,
        "reference_metrics": {
            "volume_averaged_beta": {
                "value": 0.02,
                "acceptance_interval": [0.019, 0.021],
                "upper_exclusive": True,
                "acceptance_basis": "synthetic test",
            },
            "coil_normal_field_mean_abs": {
                "value": 0.0027,
                "acceptance_interval": [0.00265, 0.00275],
                "upper_exclusive": True,
                "definition": "synthetic mean abs",
                "acceptance_basis": "synthetic test",
            },
            "coil_normal_field_max_abs": {
                "value": 0.012,
                "acceptance_interval": [0.0115, 0.0125],
                "upper_exclusive": True,
                "definition": "synthetic max abs",
                "acceptance_basis": "synthetic test",
            },
            "pressure_profile": {"definition": "p(s) proportional to 1-s"},
            "coil_table": load_manifest(Path("manifests/squid-c.template.json"))[
                "reference_metrics"
            ]["coil_table"],
            "iota_profile": {"value": [0.82, 0.84, 0.86, 0.88, 0.9], "absolute_tolerance": 1e-8},
            "quasi_isodynamic_metric": {
                "definition": "fixture",
                "value": 0.0,
                "absolute_tolerance": 1e-8,
            },
        },
    }


def test_complete_squid_c_v2_contract_reaches_both_equilibria(tmp_path):
    manifest = _manifest(tmp_path)
    assert validate_manifest(manifest, tmp_path) == []

    result = summarize_equilibrium_manifest(manifest, tmp_path)
    assert result["expected_metadata_matches"] is True
    assert result["intake_checks_pass"] is True
    assert result["scientific_admission_pass"] is False
    assert result["equilibria"]["fixed_boundary"]["free_boundary"] is False
    assert result["equilibria"]["coil_generated_free_boundary"]["free_boundary"] is True
    assert len(result["files"]) == 10
    assert all(item["origin"] == "authoritative" for item in result["files"].values())


def test_squid_c_contract_rejects_missing_mgrid_and_wrong_size(tmp_path):
    manifest = _manifest(tmp_path)
    manifest["files"] = [item for item in manifest["files"] if item["role"] != "mgrid_recipe"]
    manifest["files"][0]["bytes"] += 1
    errors = validate_manifest(manifest, tmp_path)
    assert any("missing SQuID-C file roles: mgrid_recipe" in error for error in errors)
    assert any("bytes does not match" in error for error in errors)


def test_squid_c_contract_validates_derived_lineage(tmp_path):
    manifest = _manifest(tmp_path)
    metadata = next(item for item in manifest["files"] if item["role"] == "metadata")
    metadata.update(
        {
            "origin": "derived",
            "derived_from": ["profiles", "free_boundary_vmec_output"],
            "recipe": "uv run fusion-baselines summarize-equilibrium manifest.json",
        }
    )
    metadata.pop("source_url")
    assert validate_manifest(manifest, tmp_path) == []

    metadata["derived_from"].append("undeclared_role")
    errors = validate_manifest(manifest, tmp_path)
    assert any("derives from undeclared role undeclared_role" in error for error in errors)


def test_unfilled_squid_c_template_cannot_be_admitted():
    template = load_manifest(Path("manifests/squid-c.template.json"))
    errors = validate_manifest(template, Path("."), verify_files=False)
    assert errors
    assert any("must contain path and sha256" in error for error in errors)
    assert any(
        "scale.effective_minor_radius_m must be a positive number" in error for error in errors
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_version", []),
        ("kind", {}),
        ("source", "bad"),
        ("conventions", []),
    ],
)
def test_bad_top_level_types_rejected(tmp_path, field, value):
    manifest = _manifest(tmp_path)
    manifest[field] = value
    assert validate_manifest(manifest, tmp_path)


@pytest.mark.parametrize(
    "field,value",
    [
        ("path", 7),
        ("path", []),
        ("role", []),
        ("origin", []),
        ("source_url", "not a URL"),
        ("source_url", "https://["),
    ],
)
def test_bad_file_fields_rejected(tmp_path, field, value):
    manifest = _manifest(tmp_path)
    manifest["files"][0][field] = value
    assert validate_manifest(manifest, tmp_path)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1, 0, True])
def test_invalid_scale_and_tolerances_rejected(tmp_path, value):
    manifest = _manifest(tmp_path)
    manifest["scale"]["on_axis_field_T"] = value
    assert validate_manifest(manifest, tmp_path)
    manifest = _manifest(tmp_path)
    manifest["equilibria"]["fixed_boundary"]["convergence_tolerances"]["fsqr"] = value
    assert validate_manifest(manifest, tmp_path)


def test_lineage_cycles_and_alias_paths_rejected(tmp_path):
    manifest = _manifest(tmp_path)
    item = manifest["files"][-1]
    item.update(origin="derived", derived_from=[item["role"]], recipe="self")
    assert any("cycle" in e for e in validate_manifest(manifest, tmp_path))
    manifest = _manifest(tmp_path)
    fixed = next(i for i in manifest["files"] if i["role"] == "fixed_boundary_vmec_output")
    free = next(i for i in manifest["files"] if i["role"] == "free_boundary_vmec_output")
    free.update(path="./" + fixed["path"], sha256=fixed["sha256"], bytes=fixed["bytes"])
    assert any("distinct" in e for e in validate_manifest(manifest, tmp_path))


@pytest.mark.parametrize(
    "name", ["volume_averaged_beta", "coil_table", "iota_profile", "quasi_isodynamic_metric"]
)
def test_empty_metric_rejected(tmp_path, name):
    manifest = _manifest(tmp_path)
    manifest["reference_metrics"][name] = None
    assert validate_manifest(manifest, tmp_path)


@pytest.mark.parametrize(
    "variable,value",
    [
        ("betatotal", 0.9),
        ("iotaf", 9),
        ("version_", 9),
        ("ier_flag", 1),
        ("fsqr", 1e-2),
        ("lfreeb__logical__", 0),
        ("nfp", 99),
    ],
)
def test_bad_wout_is_a_failed_check_and_nonzero_cli(tmp_path, monkeypatch, variable, value):
    manifest = _manifest(tmp_path)
    item = next(i for i in manifest["files"] if i["role"] == "free_boundary_vmec_output")
    path = tmp_path / item["path"]
    with netCDF4.Dataset(path, "r+") as dataset:
        dataset[variable][...] = value
    item.update(sha256=_digest(path), bytes=path.stat().st_size)
    assert validate_manifest(manifest, tmp_path) == []
    assert not summarize_equilibrium_manifest(manifest, tmp_path)["intake_checks_pass"]
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))
    monkeypatch.setattr(
        sys, "argv", ["fusion-baselines", "summarize-equilibrium", str(manifest_path)]
    )
    assert main() == 1
