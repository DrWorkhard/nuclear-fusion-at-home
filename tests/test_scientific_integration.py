"""Optional local raw-data regressions; core CI explicitly skips absent data."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from fusion_baselines.intake import summarize_equilibrium_manifest
from fusion_baselines.manifest import load_manifest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("manifest_name", ["qi-goodman-2022.json", "qi-goodman-2022-nfp2.json"])
def test_real_goodman_metadata(manifest_name):
    manifest = load_manifest(ROOT / "manifests" / manifest_name)
    if not all((ROOT / item["path"]).is_file() for item in manifest["files"]):
        pytest.skip("authoritative Goodman data not bootstrapped")
    result = summarize_equilibrium_manifest(manifest, ROOT)
    assert result["expected_metadata_matches"]
    assert result["vmec"]["free_boundary"] is False


def test_w7x_corrected_tolerances_and_retained_failures(tmp_path):
    test = ROOT / "artifacts/vmecpp/w7x-stellcoilbench/wout.nc"
    reference = ROOT / "artifacts/vmec2000/w7x-v852-reference/wout_w7xbaseline.nc"
    if not all(
        path.is_file()
        for path in (
            test,
            reference,
            ROOT / "external/vmecpp-validation/src/tolerances.py",
            ROOT
            / "external/vmecpp/src/vmecpp/cpp/vmecpp/vmec/output_quantities/output_quantities.cc",
            ROOT / "external/stellopt-v251/VMEC2000/Sources/Initialization_Cleanup/profil1d.f",
        )
    ):
        pytest.skip("version-matched W7-X raw outputs/source trees not bootstrapped")
    strict = tmp_path / "comparison.json"
    audit = tmp_path / "audit.json"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/compare_wout_core.py"),
            str(test),
            str(reference),
            str(strict),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1, result.stderr
    comparison = json.loads(strict.read_text())
    assert (comparison["variables_passed"], comparison["variables_checked"]) == (60, 63)
    assert {check["variable"] for check in comparison["failed"]} == {"pres", "presf", "chipf"}
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/audit_w7x_equilibrium.py"),
            str(test),
            str(reference),
            str(strict),
            str(audit),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    evidence = json.loads(audit.read_text())
    assert evidence["assessment"]["project_w7x_regression_gate_pass"]
    radial = evidence["realspace"]["refined_diagnostic_grid"]["checks"]["b_r"]
    assert radial["fixed_boundary_tolerance"] == 1e-7
    assert 16 < radial["fixed_boundary_tolerance"] / radial["max_normalized_error"] < 18
    strict_data = json.loads(strict.read_text())
    strict_data["under_test_sha256"] = "0" * 64
    strict.write_text(json.dumps(strict_data))
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/audit_w7x_equilibrium.py"),
            str(test),
            str(reference),
            str(strict),
            str(audit),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "not bound" in result.stderr
