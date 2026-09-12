import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_current_holdouts as auditor
import holdout_fixed_currents as driver


def test_all_eight_holdouts_keep_physical_rejection_and_audit_it(tmp_path, monkeypatch):
    source_file = tmp_path / "field.json"
    source_file.write_text("{}")
    ref = driver.reference(source_file)
    original_flux = [
        dict(
            surface_resolution=n,
            coil_quadrature=q,
            unthresholded_quadratic_flux=3e-8,
            mean_B_magnitude_T=1.0,
        )
        for n, q in driver.GRIDS
    ]
    original_holdout = tmp_path / "original_holdout.json"
    original_holdout.write_text(json.dumps(dict(candidates=[dict(field=ref, flux=original_flux)])))
    original_summary = tmp_path / "original_summary.json"
    original_summary.write_text(
        json.dumps(dict(steps=[dict(result=driver.reference(original_holdout))]))
    )
    originals = [
        dict(label=label, field=ref, holdouts=driver.reference(original_summary))
        for label in ("al", "slsqp")
    ]
    qualification = tmp_path / "qualification.json"
    cases = [
        dict(
            field=ref,
            source=original,
            preparation=dict(surface=ref),
            fit=dict(objective_after=2e-8),
        )
        for original in originals
    ]
    qualification.write_text(
        json.dumps(dict(status="completed", all_pass=True, cases=cases, protocol=ref, code=[]))
    )
    audit_path = tmp_path / "qualification-audit.json"
    audit_path.write_text(
        json.dumps(
            dict(
                status="completed",
                all_pass=True,
                source=driver.reference(qualification),
                cases=[dict(field=ref)] * 2,
                code=[],
            )
        )
    )

    class Field:
        def __init__(self, quadrature=200):
            self.coils = [
                SimpleNamespace(curve=SimpleNamespace(quadpoints=np.arange(quadrature)))
            ] * 16

        def set_points(self, points):
            self.points = points

        def B(self):
            return np.tile([1, 0, 0.0002], (len(self.points), 1))

    def surface(_path, *, range, nphi, ntheta):
        normal = np.zeros((nphi, ntheta, 3))
        normal[..., 2] = 1
        return SimpleNamespace(normal=lambda: normal, gamma=lambda: np.zeros_like(normal))

    for module in (driver, auditor):
        monkeypatch.setattr(module, "sources", lambda _root: originals)
        monkeypatch.setattr(module, "require_committed", lambda *_args: None)
    monkeypatch.setattr(
        driver,
        "native_components",
        lambda: (
            lambda _path: Field(),
            SimpleNamespace(from_vmec_input=surface),
            lambda _field: Field(800),
        ),
    )
    output, raw = tmp_path / "holdouts.json", tmp_path / "raw"
    monkeypatch.setattr(
        sys, "argv", ["holdout", str(qualification), str(audit_path), str(output), str(raw)]
    )
    assert driver.main() == 2
    report = json.loads(output.read_text())
    assert report["status"] == "completed" and report["all_eight_grids_completed"]
    assert not report["all_pass"]
    result_path = tmp_path / "holdout-audit.json"
    monkeypatch.setattr(sys, "argv", ["audit", str(output), str(result_path)])
    assert auditor.main() == 0
    audit = json.loads(result_path.read_text())
    assert audit["all_pass"]
    assert all(not row["physics"]["flux_cut_in"] for row in audit["cases"])
    changed = copy.deepcopy(report["cases"][0])
    changed["checks"]["flux_cut_in"] = True
    assert not auditor.audit_case(changed, originals[0], cases[0])["all_pass"]
    changed["grids"].pop()
    with pytest.raises(ValueError, match="four-grid"):
        auditor.audit_case(changed, originals[0], cases[0])
