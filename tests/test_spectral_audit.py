import importlib.util
from pathlib import Path

import numpy as np

from fusion_baselines.spectral_projection import mode_mask, project


def test_direct_dft_against_known_and_random_modes(monkeypatch):
    scripts = Path(__file__).resolve().parents[1] / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location(
        "spectrum_audit", scripts / "audit_clebsch_spectrum.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    values = np.random.default_rng(23).normal(size=(2, 16, 16))
    mask = mode_mask(16, [0, 1, 2], [0, 4, -6], 2)
    expected = project(values, mask)[1] * mask
    actual = module.direct_coefficients(values, mask)
    assert module.close(actual, expected)
    actual[0, 0, 0] += 1e-6
    assert not module.close(actual, expected)
