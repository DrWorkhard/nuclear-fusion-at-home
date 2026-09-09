"""Real-data numerical regressions; the dedicated integration command forbids skips."""

import json
import os
from pathlib import Path

import numpy as np
import pytest

from fusion_baselines.bounce_action import bounce_wells
from fusion_baselines.provenance import sha256_file
from fusion_baselines.vmec_trace import trace_geometry

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("case", ["nfp1", "nfp2", "nfp3"])
def test_frozen_real_data_actions(case):
    wout = ROOT / f"external/data/qifiles-v1/Files/configurations/{case}/vacuum/wout_QI_{case}.nc"
    if not wout.is_file():
        if os.environ.get("FUSION_REQUIRE_QI_DATA") == "1":
            pytest.fail(f"required scientific fixture missing: {wout}")
        pytest.skip("QI data not bootstrapped; run scripts/run_qi_integration.sh")
    hashes = json.loads((ROOT / "references/goodman_qi_transfer_cases.json").read_text())
    assert sha256_file(wout) == hashes["cases"][case]["wout_sha256"]
    # Use tracked numerical values, never the old machine's absolute raw paths.
    frozen = json.loads((ROOT / f"evidence/qi-measurement-v1/{case}.json").read_text())
    assert frozen["inputs"]["wout"]["sha256"] == sha256_file(wout)
    level = frozen["levels"][1]
    assert level["resolution"] == [801, 16, 2]
    trace = trace_geometry(wout, 0.5, 801, 16, 2)
    assert trace["coordinate_residual_max"] <= 1e-10
    cells = [cell for cell in level["cells"] if cell["s"] == 0.5]
    assert len(cells) == 5
    for cell in cells:
        assert len(cell["wells_by_alpha"]) == 16
        for alpha, old in enumerate(cell["wells_by_alpha"]):
            measured = [
                w.action
                for w in bounce_wells(
                    trace["length"][:, alpha],
                    trace["B"][:, alpha],
                    cell["bounce_field"],
                )
                if w.complete
            ]
            expected = [w["action"] for w in old if w["complete"]]
            assert len(measured) == len(expected) and len(expected) > 0
            np.testing.assert_allclose(measured, expected, rtol=1e-3, atol=0)
