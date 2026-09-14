"""Output recovery is lossless and must not silently change admission."""

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import serialize_coupled_coil_audit as adapter
from test_coupled_coil_audit import snapshot


def test_exact_nested_numpy_scalar_roundtrip_and_paths():
    original = dict(geometry=dict(rows=[dict(flag=np.bool_(False), value=np.float64(1.234)),
                                        dict(flag=np.bool_(True), value=np.int64(2))]),
                    values=np.array([0.1, 0.2], dtype=float))
    with pytest.raises(TypeError):
        json.dumps(original)
    conversions = []
    normalized = adapter.typed(original, conversions=conversions)
    assert normalized["geometry"]["rows"][0]["flag"] is False
    assert normalized["geometry"]["rows"][1]["flag"] is True
    assert normalized["geometry"]["rows"][0]["value"] == original["geometry"]["rows"][0]["value"]
    assert json.loads(json.dumps(normalized, allow_nan=False)) == normalized
    assert len(conversions) == 4
    assert conversions[0]["path"] == "$.geometry.rows[0].flag"
    assert conversions[0]["legacy_json_unsupported"] is True
    assert original["geometry"]["rows"][0]["flag"] is not False  # Original untouched.


@pytest.mark.parametrize("value", [np.nan, np.float64(np.inf), -np.inf, complex(1, 2),
                                  object(), {1: False}, np.array([np.nan]), {np.str_("a"): 1},
                                  np.longdouble(1.0)])
def test_nonfinite_unsupported_or_key_coercion_rejected(value):
    with pytest.raises(TypeError):
        adapter.typed(value)


def fake_report():
    return dict(status="completed", phase="validation", validation_complete=True,
                arithmetic_and_source_pass=True, entry_pass=False,
                all_pass=False, transfer_pass=False, step4_pass=False,
                gates=dict(geometry=False, independent=True),
                field_rows=[{} for _ in range(7)],
                refinements=[dict(coarse=1.0, fine=1.0) for _ in range(5)],
                flux=dict(checks=[{} for _ in range(6)]),
                geometry=dict(self_nearness=[dict(exact_repeated_node=np.bool_(False))]))


def test_normalization_precedes_gate_recheck_and_preserves_negative_decision(monkeypatch):
    monkeypatch.setattr(adapter.legacy, "read", lambda _: {})
    original = fake_report()

    def gates(snapshot, boundary, interior, flux, geometry, pairs, independent):
        assert geometry["self_nearness"][0]["exact_repeated_node"] is False
        assert len(boundary) == 4 and len(interior) == 3 and len(flux) == 6
        assert len(pairs) == 5 and independent == [True] * 7
        return dict(checks=dict(geometry=False, independent=True), entry_pass=False)

    monkeypatch.setattr(adapter.legacy.independent, "entry_gates", gates)
    result = adapter.recover(original, {"snapshot": {}})
    assert result["entry_pass"] is False
    assert result["typed_gate_recheck"]["identical"] is True
    assert result["scalar_normalization"]["legacy_unsupported_count"] == 1
    assert original["geometry"]["self_nearness"][0]["exact_repeated_node"] is not False
    assert json.loads(json.dumps(result, allow_nan=False)) == result


@pytest.mark.parametrize("mutation", ["geometry", "entry", "overall", "phase", "arithmetic"])
def test_changed_or_unqualified_decision_is_never_silently_written(monkeypatch, mutation):
    monkeypatch.setattr(adapter.legacy, "read", lambda _: {})
    original = fake_report()
    checks = copy.deepcopy(original["gates"])
    entry = False
    if mutation == "geometry":
        checks["geometry"] = True
    elif mutation == "entry":
        entry = True
    elif mutation == "overall":
        original["all_pass"] = True
    elif mutation == "phase":
        original["phase"] = "search"
    else:
        original["arithmetic_and_source_pass"] = False
    monkeypatch.setattr(adapter.legacy.independent, "entry_gates",
                        lambda *_: dict(checks=checks, entry_pass=entry))
    with pytest.raises(ValueError):
        adapter.recover(original, {"snapshot": {}})


def test_python_and_numpy_false_semantics_after_conversion():
    assert np.bool_(False) is not False
    assert adapter.typed(np.bool_(False)) is False
    assert adapter.typed(np.bool_(True)) is True
    assert adapter.typed(False) is False


@pytest.mark.parametrize("key,value", [("status", "running"), ("validation_complete", False),
                                     ("step4_pass", True), ("transfer_pass", True),
                                     ("arithmetic_and_source_pass", 1)])
def test_incomplete_or_out_of_scope_report_rejected(key, value):
    original = fake_report()
    original[key] = value
    with pytest.raises(ValueError):
        adapter.recover(original, {})


def test_actual_legacy_entry_false_negative_is_detected_not_silently_fixed(monkeypatch):
    original = fake_report()
    original["field_rows"] = ([dict(normal_rms=1e-5, normal_max=1e-4)] * 4
                              + [dict(vector_rms=1e-3)] * 3)
    original["flux"]["checks"] = [dict(relative_error=1e-8, stokes_error=1e-8,
                                      angular_error=1e-8)] * 6
    original["geometry"] = dict(
        ncoil=1024, nphi=256, ntheta=256, full_torus=True,
        length_upper=[3.0] * 24, curvature_upper=[8.0] * 24, speed_lower=[1.0] * 24,
        coil_pairs=[dict(i=i, j=j, lower=0.07) for i in range(24) for j in range(i + 1, 24)],
        plasma_distances=[dict(i=i, lower=0.09) for i in range(24)],
        self_nearness=[dict(i=i, exact_repeated_node=np.bool_(False),
                            sampled_nonlocal_minimum=0.1) for i in range(24)])
    physical = snapshot()

    def decide(geometry):
        return adapter.legacy.independent.entry_gates(
            physical, original["field_rows"][:4], original["field_rows"][4:],
            original["flux"]["checks"], geometry, [(1.0, 1.0)] * 5, [True] * 7)

    legacy = decide(original["geometry"])
    normalized = decide(adapter.typed(original["geometry"]))
    assert legacy["checks"]["geometry"] is False and legacy["entry_pass"] is False
    assert normalized["checks"]["geometry"] is True and normalized["entry_pass"] is True
    original["gates"] = legacy["checks"]
    monkeypatch.setattr(adapter.legacy, "read", lambda _: physical)
    with pytest.raises(ValueError, match="classification differs"):
        adapter.recover(original, {"snapshot": {}})
    original["geometry"]["plasma_distances"][0]["lower"] = 0.01
    assert adapter.recover(original, {"snapshot": {}})["entry_pass"] is False
