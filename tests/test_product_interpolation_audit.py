import importlib.util
import sys
from pathlib import Path

import numpy as np

from fusion_baselines.product_interpolation import decompose


def test_separate_product_replay_and_changed_terms(monkeypatch):
    scripts = Path(__file__).resolve().parents[1] / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location(
        "product_audit", scripts / "audit_clebsch_interpolation.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rng = np.random.default_rng(102)
    g, b, h = [rng.normal(size=(2, 11)) for _ in range(3)]
    values = decompose(g, b, h, 0.5, -0.005)
    stored = dict(zip(("nodes", "average", "correction", "prediction"), values, strict=True))
    assert module.verify_terms(g, b, h, 0.5, -0.005, stored)
    stored["correction"][0] += 1e-5
    assert not module.verify_terms(g, b, h, 0.5, -0.005, stored)
    # Do not keep a test-specific helper module path in global module cache.
    sys.modules.pop("product_audit", None)
