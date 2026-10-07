"""Scientific failure masks must not hide execution or individual-action failures."""

import copy
import importlib.util
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("interior_wells",
                                            ROOT / "scripts/compare_interior_wells.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_two_wells_and_censored_domain_are_distinct():
    phi = np.linspace(0, 2*np.pi, 1601)
    trace = dict(phi=phi, alpha=np.arange(16)*2*np.pi/16,
                 B=np.tile((1.2+0.2*np.cos(2*phi))[:, None], (1, 16)),
                 length=np.tile(phi[:, None], (1, 16)))
    rows = module.cells(trace)
    assert rows[0]["error"] is None
    assert np.shape(rows[0]["result"]["actions"]) == (16, 2)
    assert len(rows[-1]["failed_lines"]) == 16
    assert all(row["censored"] == 1 for row in rows[-1]["failed_lines"])
    with patch("fusion_baselines.coil_bounce.period_actions", side_effect=ValueError("bad solver")):
        with pytest.raises(ValueError, match="bad solver"):
            module.cells(trace)
    trace["length"][1] = trace["length"][0]
    with pytest.raises(ValueError, match="Malformed trace"):
        module.cells(trace)


def comparison(failures):
    rows = []
    for s in (0.1, 0.25, 0.5, 0.75, 0.9):
        cells = [dict(q=q, error="missing" if (s, q) in failures else None,
                      result=dict(actions=[[1.0, 2.0] for _ in range(16)]))
                 for q in (0.03, 0.1, 0.3, 0.5, 0.7, 0.9, 0.97)]
        rows.append(dict(s=s, **{"801": cells, "1601": copy.deepcopy(cells)}))
    return rows


def test_decision_retains_new_and_unstable_failures():
    ideal = comparison(set())
    reference = comparison(module.EXPECTED_FAILURES)
    for failure, expected in ((set(), "promising-association"),
                              ({(0.1, 0.03)}, "lower-interior-error-insufficient"),
                              ({(0.9, 0.97)}, "lower-interior-error-insufficient")):
        arms = dict(reference=reference, continuation=comparison(failure))
        result = module.compare(arms, ideal, 0.002)
        assert result["verdict"] == expected
        assert result["core_restored"] == (not (failure & module.EXPECTED_FAILURES))
    arms["continuation"][0]["1601"][0]["error"] = "missing"
    assert module.compare(arms, ideal, 0.002)["verdict"] == "inconclusive"


def test_one_action_cannot_hide_in_an_aggregate():
    ideal = comparison(set())
    arms = dict(reference=comparison(module.EXPECTED_FAILURES), continuation=comparison(set()))
    arms["continuation"][0]["1601"][0]["result"]["actions"][7][1] *= 1.002
    result = module.compare(arms, ideal, 0.002)
    assert result["verdict"] == "inconclusive"
    assert result["reason"] == "individual action refinement"
    arms["continuation"] = comparison(set())
    assert module.compare(arms, ideal, 0.009)["reason"] == "interior contrast not reproduced"


def test_failure_receipt_respects_cap_and_preserves_attempt(tmp_path, monkeypatch):
    from fusion_baselines.coil_fit import Recorder

    monkeypatch.setattr(module, "MAX_OUTPUT_BYTES", 8192)
    monkeypatch.setattr(module, "FAILURE_RESERVE", 4096)
    record = Recorder(tmp_path/"run", module.START+900)
    module.save_payload(record, "result.json", b"x"*4000)
    with pytest.raises(ValueError, match="output ceiling"):
        module.save_payload(record, "progress.json", b"x"*100)
    # Model an interrupted publication, which the shared recorder charges to storage.
    (record.output/"result.json.tmp").write_bytes(b"partial")
    record.storage[0] += 7
    receipt = module.save_failure(record, ValueError("x"*10000), "a"*40, "b"*64)
    assert receipt["completed"] is False
    assert receipt["decision"]["verdict"] == "inconclusive"
    assert (record.output/"attempted-result.json").read_bytes() == b"x"*4000
    assert (record.output/"result.json.tmp").read_bytes() == b"partial"
    assert record.storage[0] == sum(p.stat().st_size for p in record.output.iterdir())
    assert record.storage[0] <= module.MAX_OUTPUT_BYTES
    with pytest.raises(ValueError, match="output ceiling"):
        module.save_payload(record, "too-large.json", b"x"*8192, failure=True)
