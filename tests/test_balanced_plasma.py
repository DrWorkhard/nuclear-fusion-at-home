"""Control two-domain selection and local LP, including deliberately false certificates."""

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pytest

from fusion_baselines.balanced_plasma import (
    FD_STEP,
    construction,
    dual_certificate,
    proposal,
    select,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_balanced_plasma as audit
import balanced_plasma_inputs as inputs
import run_balanced_plasma as runner
from current_diagnostic_inputs import reference


def measured(score=1.0, mean=1.0, envelope=0.1):
    return dict(
        score=score,
        cells=[
            dict(s=s, q=q, mean=[mean] * 2, envelope=[envelope] * 2)
            for s in (0.1, 0.25, 0.5, 0.75, 0.9)
            for q in (0.03, 0.1, 0.3, 0.5, 0.7, 0.9, 0.97)
        ],
    )


def model_data():
    points = [sign * FD_STEP * np.eye(4)[k] for k in range(4) for sign in (1, -1)]
    n = [1 - 200 * x[0] - 20 * x[1] for x in points]
    w = [1 - 20 * x[0] - 200 * x[1] for x in points]
    means = np.array([np.full((35, 2), 1 + 50 * x[0] + 40 * x[1]) for x in points])
    return n, w, means


def test_common_descent_model_has_independent_primal_dual_certificate():
    n, w, means = model_data()
    result = proposal(n, w, means, 1.0, 1.0, np.ones((35, 2)))
    assert result["success"]
    assert result["solution"][-1] == pytest.approx(0.022)
    assert dual_certificate(result)["passed"]
    rows = [dict(native=dict(measurement=dict(score=v))) for v in n]
    values = [dict(score=v, mean=m) for v, m in zip(w, means, strict=True)]
    assert audit.model_check(
        result,
        rows,
        values,
        dict(native=dict(measurement=dict(score=1.0))),
        dict(score=1.0, mean=np.ones((35, 2))),
    )["passed"]


@pytest.mark.parametrize(
    "field", ["solution", "fun", "inequality_marginals", "lower_marginals", "matrix"]
)
def test_fake_model_certificate_rejected(field):
    n, w, means = model_data()
    result = proposal(n, w, means, 1.0, 1.0, np.ones((35, 2)))
    if field == "fun":
        result[field] -= 0.1
    elif field == "matrix":
        result[field][0][0] += 100
    else:
        result[field][0] += 100
    assert not dual_certificate(result)["passed"]


@pytest.mark.parametrize("bad", ["missing", "nan", "zero_mean"])
def test_incomplete_derivative_model_cannot_optimise(bad):
    n, w, means = model_data()
    if bad == "missing":
        n = n[:-1]
    elif bad == "nan":
        means[2, 0, 0] = np.nan
    else:
        means[2, 0, 0] = 0.0
    if bad == "zero_mean":
        with pytest.raises(ValueError):
            proposal(n, w, means, 1.0, 1.0, np.zeros((35, 2)))
    else:
        with pytest.raises(ValueError):
            proposal(n, w, means, 1.0, 1.0, np.ones((35, 2)))


@pytest.mark.parametrize("bad", ["wide", "narrow", "mean", "envelope", "geometry", "nonfinite"])
def test_only_both_domains_and_local_guards_admit(bad):
    meta = dict(volume=1.0, iota=[0.5] * 3)
    n, wide, current = 0.99, measured(0.97), copy.deepcopy(meta)
    if bad == "wide":
        wide["score"] = 1.01
    elif bad == "narrow":
        n = 0.999
    elif bad == "mean":
        wide["cells"][0]["mean"][0] = 1.03
    elif bad == "envelope":
        wide["cells"][0]["envelope"][1] = 0.12
    elif bad == "geometry":
        current["volume"] = 1.02
    else:
        wide["score"] = float("nan")
    assert not all(construction(n, wide, 1.0, measured(), current, meta).values())


def test_selection_stable_ties_and_independent_classification():
    meta = dict(volume=1.0, iota=[0.5] * 3)
    base = dict(native=dict(measurement=dict(score=1.0), metadata=meta))
    bv = dict(score=1.0, mean=np.ones((35, 2)), envelope=np.full((35, 2), 0.1))
    rows, values = [], []
    for score in (0.97, 0.97, 1.01):
        wide = measured(score)
        flags = construction(0.99, wide, 1.0, measured(), meta, meta)
        rows.append(
            dict(
                native=dict(measurement=dict(score=0.99), metadata=meta),
                wide_score=score,
                construction=flags,
            )
        )
        values.append(dict(bv, score=score))
    assert select(rows) == audit.selection(rows, values, base, bv) == 0
    rows[2]["construction"]["wide"] = True
    with pytest.raises(ValueError):
        audit.selection(rows, values, base, bv)
    assert select([dict(error="failed")]) is None


def test_new_followup_sources_bind_preserved_failed_admission():
    _, binding, predecessor = inputs.sources(Path(__file__).resolve().parents[1], committed=False)
    assert len(predecessor["cells"]) == 16
    audit.old.bind_tree(binding)
    assert binding["audit"] == reference(Path("evidence/plasma-design-v2-audit.json"))


def setup_runner(tmp_path, monkeypatch):
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        monkeypatch.setenv(name, "1")
    monkeypatch.setattr(runner, "root_path", lambda: tmp_path)
    monkeypatch.setattr(runner, "space_check", lambda *a: {})
    monkeypatch.setattr(
        runner,
        "sources",
        lambda root: ({}, {"legacy": {}}, {"cells": [dict(index=i) for i in range(16)]}),
    )


def test_archive_visits_every_state_and_does_not_run_a_solver(tmp_path, monkeypatch):
    setup_runner(tmp_path, monkeypatch)
    calls = []

    def broad(native, folder, baseline=None):
        i = native["index"]
        calls.append(i)
        result = dict(native=native, wide_score=1.0, construction=dict(allowed=i == 2))
        if i == 0:
            result.pop("construction")
        if i == 3:
            result = dict(native=native, error="synthetic missing well")
        return result

    monkeypatch.setattr(runner, "broad", broad)
    monkeypatch.setattr(
        runner, "solve", lambda *a: pytest.fail("archive must reuse existing solves")
    )
    monkeypatch.setattr(
        sys, "argv", ["runner", "archive", str(tmp_path / "out"), str(tmp_path / "raw")]
    )
    assert runner.main() == 0
    record = json.loads((tmp_path / "out/archive.json").read_text())
    assert calls == list(range(16)) and record["selected"] == 2 and record["new_solves"] == 0
    assert "error" in record["rows"][3] and record["step3_pass"] is False
    with pytest.raises(FileExistsError):
        runner.main()


def test_existing_archive_candidate_prevents_extra_differences(tmp_path, monkeypatch):
    setup_runner(tmp_path, monkeypatch)
    output = tmp_path / "out"
    output.mkdir()
    (output / "archive.json").write_text(
        json.dumps(dict(status="completed", source={"legacy": {}}, selected=1, rows=[{}]))
    )
    monkeypatch.setattr(runner, "solve", lambda *a: pytest.fail("unregistered extra cold solves"))
    monkeypatch.setattr(sys, "argv", ["runner", "propose", str(output), str(tmp_path / "raw")])
    assert runner.main() == 2
    record = json.loads((output / "propose.json").read_text())
    assert record["status"] == "error" and record["new_solves"] == 0
    assert "not authorized" in record["error"] and record["step3_pass"] is False
