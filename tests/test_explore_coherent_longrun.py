"""Only changed experiment settings; shared search/physics retain their own tests."""

import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
with pytest.MonkeyPatch.context() as patch:
    patch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "longrun", ROOT / "scripts/explore_coherent_longrun.py")
    study = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(study)


def test_boxes_preserve_center_and_expand_declared_modes():
    center = np.sin(np.arange(198))
    a, b = study.bounds(center, "same-box")
    c, d = study.bounds(center, "wider-box")
    assert np.all(c < a) and np.all(d > b)
    low = study.restart.previous.active_indices("low2")
    np.testing.assert_allclose((b-a)[low], .24)
    np.testing.assert_allclose((d-c)[low], .32)
    high = np.setdiff1d(np.arange(198), low)
    np.testing.assert_allclose((b-a)[high], .04)
    np.testing.assert_allclose((d-c)[high], .08)


def test_runtime_bundle_cap_removed_and_restored_even_on_failure():
    with pytest.raises(RuntimeError), study.wall_clock_search():
        assert study.restart.BUNDLES == math.inf
        raise RuntimeError("simulated failed experiment")
    assert study.restart.BUNDLES == 1200


def test_solver_adapter_preserves_method_bounds_and_tolerances():
    def solve(function, initial, **kwargs):
        assert function == "objective" and initial == "seed"
        assert kwargs["bounds"] == "fixed" and kwargs["method"] == "L-BFGS-B"
        assert kwargs["options"] == study.SOLVER_OPTIONS
        return "done"
    assert study.solver_adapter(solve)("objective", "seed", bounds="fixed",
        method="L-BFGS-B", options={"maxiter": 1190}) == "done"


def test_geometry_result_serializes_numpy_scalars_without_changing_gates(monkeypatch):
    from fusion_baselines import coupled_coil_audit, curvature_bounds

    g = dict(length_upper=[np.float64(3.)], coil_lower=np.float64(.07),
             plasma_lower=np.float64(.09), coil_pairs=[dict(sampled=.08)],
             plasma_distances=[dict(sampled=.10)],
             self_nearness=[dict(exact_repeated_node=np.bool_(False))])
    monkeypatch.setattr(coupled_coil_audit, "geometry_certificates", lambda *args: g)
    monkeypatch.setattr(curvature_bounds, "curvature_enclosure", lambda *args:
        dict(maximum_lower_bound=10., maximum_upper_bound=11., regularity_resolved=True))
    result = study.geometry(dict(base_coefficients=[[]]), {}, lambda: None)
    assert json.loads(json.dumps(result)) == result and result["status"] == "pass"
    g["coil_lower"] = np.float64(.05)
    assert study.geometry(dict(base_coefficients=[[]]), {}, lambda: None)["status"] == "unresolved"
    g["coil_pairs"][0]["sampled"] = .04
    assert study.geometry(dict(base_coefficients=[[]]), {}, lambda: None)["status"] == "fail"
