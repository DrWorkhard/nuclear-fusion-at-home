"""Replay archived numerical diagnostics without local Wouts or SIMSOPT (NumPy/SciPy)."""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]/"src"))
from fusion_baselines.boundary_control_metrics import boundary_metrics  # noqa: E402
from fusion_baselines.coil_bounce import measure  # noqa: E402
from fusion_baselines.coil_check import field_metrics  # noqa: E402

for name, expected in json.loads((HERE/"manifest.json").read_text()).items():
    actual = hashlib.sha256((HERE/name).read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError("archive identity changed: "+name)

for target in ("reference401", "selected401"):
    arm = HERE/target
    snapshot = json.loads((arm/"fit/selected-snapshot.json").read_text())
    for shift in (0.0, 0.5):
        row = json.loads((arm/"fit"/f"fine-{shift}.json").read_text())
        with np.load(arm/"fit"/f"fine-{shift}.npz", allow_pickle=False) as arrays:
            normal = arrays["normals"]
            result = boundary_metrics(arrays["B"].reshape(normal.shape), normal)
        for metric in ("normal_rms", "normal_max"):
            assert abs(result[metric]-row["metrics"][metric]) <= 1e-14
    for level in range(3):
        row = json.loads((arm/"fit/interior"/f"level-{level}.json").read_text())
        with np.load(arm/"fit/interior"/f"level-{level}.npz", allow_pickle=False) as arrays:
            result = field_metrics(arrays["inner_B"], arrays["inner_target"], arrays["loop_A"],
                                   arrays["loop_tangent"], snapshot, row["ninner"], target)
        assert abs(result["vector_rms"]-row["metrics"]["vector_rms"]) <= 1e-14
    diagnostic = json.loads((arm/"bounce/result.json").read_text())
    for surface in diagnostic["surfaces"]:
        for label in ("ideal", "coil"):
            with np.load(arm/"bounce"/f"{label}-s{surface['s']}.npz", allow_pickle=False) as arrays:
                result = measure(arrays)
            expected = surface[label]
            assert result["errors"] == expected["errors"]
            assert [r["q"] for r in result["cells"]] == [r["q"] for r in expected["cells"]]
            for actual, stored in zip(result["cells"], expected["cells"], strict=True):
                assert abs(actual["score"]-stored["score"]) <= 1e-14
    print(target+": field metrics and all action cells/failures reproduced")
print("Numerical array replay only; no independent physics or native-input reproduction.")
