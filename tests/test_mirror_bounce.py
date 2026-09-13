import copy
import json
import sys
from pathlib import Path

import numpy as np
import pytest

from fusion_baselines import mirror_bounce, mirror_scalar_audit
from fusion_baselines.mirror_bounce import bounce_cell, refinement_checks
from fusion_baselines.mirror_scalar_audit import audit_values, scalar_action

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_absolute_drift_control as auditor
import run_absolute_drift_control as driver


def test_scalar_action_and_both_fd_scales_against_cartesian_drift():
    work = {}
    cell, arrays = bounce_cell(0.02, 1.4, 0.37, 48, work=work)
    cell["work"] = work
    assert cell["all_pass"]
    scalar = scalar_action(0.02, 1.4)
    differences = []
    for h in (1e-4, 1e-5):
        plus, minus = scalar_action(0.02 * (1 + h), 1.4), scalar_action(0.02 * (1 - h), 1.4)
        differences.append(
            dict(
                relative_step=h,
                derivative=(
                    plus["integrals"]["action"]["value"] - minus["integrals"]["action"]["value"]
                )
                / (0.04 * h),
            )
        )
    assert audit_values(cell, scalar, differences)["all_pass"]
    assert all(auditor.array_checks(cell, arrays).values())
    for key in ("action", "delta_alpha_reduced", "transit_length"):
        bad = copy.deepcopy(cell)
        bad["values"][key] *= 2
        assert not audit_values(bad, scalar, differences)["all_pass"]
    bad = copy.deepcopy(cell)
    bad["absolute"]["positive"]["time_s"] *= 2
    assert not audit_values(bad, scalar, differences)["all_pass"]
    assert not audit_values(cell, scalar, differences[:1])["all_pass"]


def test_small_workflow_all_resolutions_and_mutation(tmp_path, monkeypatch):
    monkeypatch.setattr(driver, "LINES", [(0.02, 1.4, 0.37)])
    monkeypatch.setattr(auditor, "PAIRS", [(0.02, 1.4)])
    monkeypatch.setattr(auditor, "ANGLES", (0.37,))
    for module in (driver, auditor):
        monkeypatch.setattr(module, "require_committed", lambda *_: None)
    path, raw = tmp_path / "study.json", tmp_path / "raw"
    monkeypatch.setattr(sys, "argv", ["driver", str(path), str(raw)])
    assert driver.main() == 0
    output = tmp_path / "audit.json"
    monkeypatch.setattr(sys, "argv", ["audit", str(path), str(output)])
    assert auditor.main() == 0
    result = json.loads(output.read_text())
    assert len(result["scalar_runs"]) == 5
    assert all(r["calls"]["action"] > 0 for r in result["scalar_runs"])
    study = json.loads(path.read_text())
    study["cells"][0]["values"]["delta_alpha_reduced"] *= -1
    path.write_text(json.dumps(study))
    monkeypatch.setattr(sys, "argv", ["audit", str(path), str(tmp_path / "bad.json")])
    assert auditor.main() == 2


def test_cell_failure_retained_without_skipping_later_resolutions(tmp_path, monkeypatch):
    monkeypatch.setattr(driver, "LINES", [(0.02, 1.4, 0.37)])
    monkeypatch.setattr(driver, "require_committed", lambda *_: None)

    def fail_middle(psi, bstar, alpha, nodes, **kwargs):
        if nodes == 128:
            raise ValueError("deliberate cell failure")
        return bounce_cell(psi, bstar, alpha, nodes, **kwargs)

    monkeypatch.setattr(driver, "bounce_cell", fail_middle)
    path = tmp_path / "study.json"
    monkeypatch.setattr(sys, "argv", ["driver", str(path), str(tmp_path / "raw")])
    assert driver.main() == 2
    result = json.loads(path.read_text())
    assert [r["status"] for r in result["cells"]] == ["completed", "error", "completed"]
    assert not result["all_cells_completed"] and not result["refinements"][0]["all_pass"]
    assert result["work"]["cell_attempts"] == 3 and result["work"]["cell_completed"] == 2


@pytest.mark.parametrize("args", [(0, 1.4, 0, 32), (0.02, 0.9, 0, 32), (0.02, 1.4, np.nan, 32)])
def test_invalid_bounce_inputs(args):
    with pytest.raises(ValueError):
        bounce_cell(*args)


def test_incomplete_refinement_rejected():
    with pytest.raises(ValueError):
        refinement_checks([])


def test_failed_scalar_integral_and_cartesian_field_keep_attempted_work(monkeypatch):
    def broken_quad(integrand, *args, **kwargs):
        integrand(0.1)
        raise RuntimeError("deliberate integration failure")

    monkeypatch.setattr(mirror_scalar_audit, "quad", broken_quad)
    record = {}
    with pytest.raises(RuntimeError, match="deliberate"):
        scalar_action(0.02, 1.4, record=record)
    assert record["status"] == "error" and record["failed_integral"] == "action"
    assert record["calls"]["root"] > 0 and record["calls"]["action"] == 1
    assert not record["integrals"]

    def broken_field(*args):
        raise RuntimeError("deliberate field failure")

    monkeypatch.setattr(mirror_bounce, "mirror_field", broken_field)
    work = {}
    with pytest.raises(RuntimeError, match="deliberate"):
        bounce_cell(0.02, 1.4, 0.37, 48, work=work)
    assert work["root_calls"] > 0 and work["cartesian_points_requested"] == 48
    assert work["cartesian_points_completed"] == 0
