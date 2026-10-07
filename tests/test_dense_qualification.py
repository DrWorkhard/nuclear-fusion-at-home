"""A plausible numerical result must not hide a changed qualification control."""

import importlib.util
import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from fusion_public.data import canonical, sha

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("dense_qualification",
                                            ROOT / "scripts/qualify_dense_interior.py")
qualifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualifier)


def test_rejects_unverified_revision():
    with pytest.raises(ValueError, match="Exact clean"):
        qualifier.clean_revision("0" * 40)


def test_changed_control_demotes_numerically_matching_result(tmp_path):
    candidate = ROOT / "examples/clear-coil-interior-v1/reference401-candidate.json"
    expected = dict(target_id="reference401", candidate_sha256=sha(candidate.read_bytes()),
                    packet_sha256="0" * 64, original_current_A=1, native_B_T=[[1, 2, 3]],
                    original_metrics=dict(vector_rms=0.02, surface_vector_rms=[0.02]*3))
    control = tmp_path / "control.json"
    control.write_bytes(canonical(expected))
    control_sha = sha(control.read_bytes())
    report = dict(packet_sha256="0" * 64, flux_normalized_max_abs_current_A=1,
                  dense_inner_vector_rms=0.02, surface_vector_rms=[0.02]*3,
                  interior_metric_below_limit=False)

    def changed_during_evaluation(*args, **kwargs):
        control.write_bytes(control.read_bytes() + b" ")
        return report, [[1, 2, 3]]

    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                       text=True).strip()
    output = tmp_path / "result"
    with patch("fusion_public.dense_interior.evaluate_dense", changed_during_evaluation):
        with pytest.raises(ValueError, match="Source/input changed"):
            qualifier.run("reference401", control, control_sha, output, revision)
    receipt = json.loads((output / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["completed"] is False
    assert receipt["physical_admission"] is False
