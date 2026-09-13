import copy
import json
import sys
from pathlib import Path

import numpy as np
import pytest

from fusion_baselines import vacuum_scalar
from fusion_baselines.vacuum_bounce import vacuum_cell
from fusion_baselines.vacuum_drift_audit import audit_vacuum_cell
from fusion_baselines.vacuum_scalar import scalar_vacuum

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_vacuum_drift_control as auditor
import run_vacuum_drift_control as driver


def make_case():
    work = {}
    cell, arrays = vacuum_cell(0.02, 1.4, 0.4, 64, work=work)
    cell["work"] = work
    scalar = scalar_vacuum(0.02, 1.4, 0.4)
    differences = []
    for coord in ("psi", "alpha"):
        for step in (1e-4, 1e-5):
            h = 0.02 * step if coord == "psi" else step
            plus = scalar_vacuum(
                0.02 + h if coord == "psi" else 0.02, 1.4, 0.4 + h if coord == "alpha" else 0.4
            )
            minus = scalar_vacuum(
                0.02 - h if coord == "psi" else 0.02, 1.4, 0.4 - h if coord == "alpha" else 0.4
            )
            differences.append(
                dict(
                    coordinate=coord,
                    step=step,
                    derivative=(
                        plus["integrals"]["action"]["value"] - minus["integrals"]["action"]["value"]
                    )
                    / (2 * h),
                )
            )
    return cell, arrays, scalar, differences


def test_both_integrated_drifts_independent_scalar_and_fixed_fd_scales():
    cell, arrays, scalar, diffs = make_case()
    assert cell["all_pass"] and abs(cell["values"]["dpsi"]) > 1e-5
    result = audit_vacuum_cell(cell, arrays, scalar, diffs)
    assert result["all_pass"], result
    assert not scalar["warnings"]


def test_wrong_radial_sign_missing_phase_term_and_factor_two_rejected():
    cell, arrays, scalar, diffs = make_case()
    for key in ("dpsi", "dalpha", "action", "gauge_0_phase", "gauge_2_beta"):
        bad = copy.deepcopy(cell)
        bad["values"][key] *= -2
        assert not audit_vacuum_cell(bad, arrays, scalar, diffs)["all_pass"]
    for key in ("delta_psi_Wb_per_rad", "psi_rate_Wb_per_rad_s", "phase_rate_rad_per_s"):
        bad = copy.deepcopy(cell)
        bad["absolute"]["positive"][key] *= 2
        assert not audit_vacuum_cell(bad, arrays, scalar, diffs)["all_pass"]
    assert not audit_vacuum_cell(cell, arrays, scalar, diffs[:-1])["all_pass"]
    badarrays = {k: v.copy() for k, v in arrays.items()}
    badarrays["field_jacobian"][0, 0, 1] = 0.1
    assert not audit_vacuum_cell(cell, badarrays, scalar, diffs)["all_pass"]
    badarrays["weights"][0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        audit_vacuum_cell(cell, badarrays, scalar, diffs)


def test_small_complete_workflow_hashes_all_levels_and_work_mutation(tmp_path, monkeypatch):
    for module in (driver, auditor):
        monkeypatch.setattr(module, "LINES", [(0.02, 1.4, 0.4)])
        monkeypatch.setattr(module, "require_committed", lambda *_: None)
    path = tmp_path / "study.json"
    monkeypatch.setattr(sys, "argv", ["driver", str(path), str(tmp_path / "raw")])
    assert driver.main() == 0
    output = tmp_path / "audit.json"
    monkeypatch.setattr(sys, "argv", ["audit", str(path), str(output)])
    assert auditor.main() == 0
    result = json.loads(output.read_text())
    assert len(result["scalar_runs"]) == 9 and len(result["cells"]) == 3
    study = json.loads(path.read_text())
    study["cells"][1]["work"]["roots_completed"] -= 1
    path.write_text(json.dumps(study))
    monkeypatch.setattr(sys, "argv", ["audit", str(path), str(tmp_path / "bad.json")])
    assert auditor.main() == 2


def test_failed_cell_keeps_later_resolutions_and_scalar_failure_counts(tmp_path, monkeypatch):
    monkeypatch.setattr(driver, "LINES", [(0.02, 1.4, 0.4)])
    monkeypatch.setattr(driver, "require_committed", lambda *_: None)

    def broken(psi, bstar, alpha, nodes, **kwargs):
        if nodes == 128:
            raise ValueError("deliberate middle-cell failure")
        return vacuum_cell(psi, bstar, alpha, nodes, **kwargs)

    monkeypatch.setattr(driver, "vacuum_cell", broken)
    path = tmp_path / "study.json"
    monkeypatch.setattr(sys, "argv", ["driver", str(path), str(tmp_path / "raw")])
    assert driver.main() == 2
    result = json.loads(path.read_text())
    assert [r["status"] for r in result["cells"]] == ["completed", "error", "completed"]
    assert not result["all_cells_completed"]

    def broken_quad(func, *args, **kwargs):
        func(0.1)
        raise RuntimeError("deliberate scalar integration failure")

    monkeypatch.setattr(vacuum_scalar, "quad", broken_quad)
    record = {}
    with pytest.raises(RuntimeError, match="deliberate"):
        scalar_vacuum(0.02, 1.4, 0.4, record=record)
    assert record["status"] == "error" and record["calls"]["roots_completed"] == 2
    assert record["calls"]["action"] == 1 and not record["integrals"]
