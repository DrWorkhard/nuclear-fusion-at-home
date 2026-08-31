from __future__ import annotations

import hashlib
from pathlib import Path

import netCDF4

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
            "lfreeb": int(free_boundary),
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
            "volume_averaged_beta": {"value": 0.02},
            "coil_normal_field_mean_abs": {"value": 0.0027},
            "coil_normal_field_max_abs": {"value": 0.012},
            "pressure_profile": {"definition": "p(s) proportional to 1-s"},
            "coil_table": {"rows": []},
            "iota_profile": {"value": [0.82, 0.9]},
            "quasi_isodynamic_metric": {"definition": "fixture", "value": 0.0},
        },
    }


def test_complete_squid_c_v2_contract_reaches_both_equilibria(tmp_path):
    manifest = _manifest(tmp_path)
    assert validate_manifest(manifest, tmp_path) == []

    result = summarize_equilibrium_manifest(manifest, tmp_path)
    assert result["expected_metadata_matches"] is True
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
    assert any("sha256 must be 64 lowercase" in error for error in errors)
    assert any(
        "scale.effective_minor_radius_m must be a positive number" in error for error in errors
    )
