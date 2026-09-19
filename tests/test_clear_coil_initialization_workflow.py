"""Synthetic persistence, source and orchestration checks; no target evaluations."""

import copy
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import clear_coil_initialization_inputs as binding  # noqa: E402
import run_clear_coil_initialization as runner  # noqa: E402

from fusion_baselines import clear_coil_geometry as producer  # noqa: E402


def negative_report():
    gates = {"geometry": False}
    return dict(
        status="completed",
        phase="validation",
        source={},
        case={"label": "reference-n6-N"},
        arithmetic_and_source_pass=True,
        validation_complete=True,
        all_pass=False,
        entry_pass=False,
        transfer_pass=False,
        step4_pass=False,
        gates=gates,
        run={"path": "same", "sha256": "same"},
        validation={"path": "same", "sha256": "same"},
        typed_gate_recheck=dict(
            identical=True, entry_pass=False, legacy_gates=gates, normalized_gates=gates
        ),
    )


def test_negative_predecessor_remains_negative():
    binding.negative_predecessor(negative_report(), {}, "reference-n6-N")


@pytest.mark.parametrize(
    "key,value",
    [
        ("arithmetic_and_source_pass", 1),
        ("validation_complete", False),
        ("entry_pass", True),
        ("step4_pass", True),
        ("transfer_pass", True),
        ("phase", "search"),
        ("status", "error"),
        ("source", {"changed": True}),
    ],
)
def test_negative_predecessor_mutations_fail(key, value):
    report = negative_report()
    report[key] = value
    with pytest.raises(ValueError, match="negative coil-pilot"):
        binding.negative_predecessor(report, {}, "reference-n6-N")


@pytest.mark.parametrize("mutation", ["label", "changed_gate", "run", "truthy_recheck"])
def test_negative_source_recheck_is_exact(mutation):
    report = copy.deepcopy(negative_report())
    if mutation == "label":
        report["case"]["label"] = "reference-n8-N"
    elif mutation == "changed_gate":
        report["typed_gate_recheck"]["normalized_gates"] = {"geometry": True}
    elif mutation == "run":
        report["run"] = {"different": True}
    else:
        report["typed_gate_recheck"]["identical"] = "true"
    with pytest.raises(ValueError):
        binding.negative_predecessor(report, {}, "reference-n6-N")


def test_historical_identity_exact_bytes(monkeypatch, tmp_path):
    path = tmp_path / "report.json"
    path.write_text("original\n")
    seen = []

    def previous(command, cwd):
        seen.append((command, cwd))
        return b"original\n"

    monkeypatch.setattr(binding.subprocess, "check_output", previous)
    binding.historical_identity(tmp_path, path)
    assert seen[0][0] == ["git", "show", "4f3c2fa:report.json"]
    path.write_text("changed\n")
    with pytest.raises(ValueError, match="historical"):
        binding.historical_identity(tmp_path, path)


def test_registered_matrix_and_levels():
    plan = runner.attempt_plan(producer.cases())
    assert len(producer.cases()) == 12 and len(plan) == 168
    assert [p["index"] for p in plan] == list(range(168))
    assert [p["repeat"] for p in plan] == [False, True] * 84
    for original, repeat in zip(plan[::2], plan[1::2], strict=True):
        assert (original["case"], original["base_index"]) == (repeat["case"], repeat["base_index"])
    assert [(p["target"], p["nphi"], p["offset"]) for p in runner.surface_levels()] == [
        (target, n, offset)
        for target in ("reference", "selected")
        for n, offset in ((256, 0), (512, 0), (512, 0.5))
    ]


@pytest.mark.parametrize("mutation", ["case", "base", "repeat", "missing", "truthy"])
def test_same_count_is_not_complete_registered_attempt_matrix(mutation):
    matrix = producer.cases()
    plan = runner.attempt_plan(matrix)
    assert runner.complete_plan(plan, matrix)
    if mutation == "case":
        plan[0]["case"] = plan[-1]["case"]
    elif mutation == "base":
        plan[0]["base_index"] = 1
    elif mutation == "repeat":
        plan[0]["repeat"] = True
    elif mutation == "truthy":
        plan[0]["repeat"] = 0
    else:
        plan.pop()
    assert not runner.complete_plan(plan, matrix)


@pytest.mark.parametrize("nbase,order", [(6, 5), (8, 7)])
def test_geometry_snapshot_has_no_invented_physics(nbase, order):
    case = next(c for c in producer.cases() if (c["nbase"], c["order"]) == (nbase, order))
    coefficients = np.zeros((nbase, 3, 2 * order + 1))
    snapshot = runner.geometry_snapshot(case, coefficients, {"targets": {"synthetic": True}})
    assert snapshot["kind"] == "geometry-only"
    assert len(snapshot["names"]) == coefficients.size
    assert snapshot["names"][:3] == ["coil[0]/xc(0)", "coil[0]/xs(1)", "coil[0]/xc(1)"]
    assert len(snapshot["physical"]) == 4 * nbase
    assert all(set(p) == {"base_index", "period", "flip", "matrix"} for p in snapshot["physical"])
    assert not any(
        k in snapshot for k in ("current", "scale", "B2_scale", "unit_flux", "field_calls")
    )
    for p in snapshot["physical"]:
        matrix = np.asarray(p["matrix"])
        np.testing.assert_allclose(matrix @ matrix.T, np.eye(3), atol=1e-15)
    json.dumps(snapshot, allow_nan=False)


@pytest.mark.parametrize("value", [np.nan, np.inf, complex(1, 2), object(), {1: "bad"}])
def test_typed_serialization_rejects_nonfinite_or_nonbuiltin(value):
    with pytest.raises(TypeError):
        runner.typed(value)


def test_typed_serialization_preserves_numpy_boolean():
    assert runner.typed({"flag": np.bool_(False), "values": np.array([1.0, 2.0])}) == {
        "flag": False,
        "values": [1.0, 2.0],
    }


def test_failed_and_interrupted_attempts_retained(tmp_path):
    for name in ("attempts", "outcomes"):
        (tmp_path / name).mkdir()
    for i in range(3):
        runner.save_json(tmp_path / "attempts" / f"{i:04d}.json", dict(index=i, status="attempted"))
    runner.save_json(tmp_path / "outcomes/0000.json", dict(index=0, status="completed"))
    runner.save_json(
        tmp_path / "outcomes/0001.json", dict(index=1, status="failed", error="synthetic")
    )
    before = (tmp_path / "outcomes/0000.json").read_bytes()
    rows = runner.collected_attempts(tmp_path)
    assert [r["status"] for r in rows] == ["completed", "failed", "attempted"]
    assert (tmp_path / "outcomes/0000.json").read_bytes() == before
    assert all(runner.checked(r["attempt"]).exists() for r in rows)


def test_parent_lp_wall_guard_uses_only_latest_unfinished_attempt(tmp_path):
    for folder in ("attempts", "outcomes"):
        (tmp_path / folder).mkdir()
    runner.save_json(tmp_path / "attempts/0000.json", dict(started_monotonic=1.0))
    runner.save_json(tmp_path / "outcomes/0000.json", dict(status="completed"))
    runner.save_json(tmp_path / "attempts/0001.json", dict(started_monotonic=100.0))
    runner.live_deadlines(tmp_path, 0.0, now=129.9)
    with pytest.raises(runner.LPBudgetExceeded, match="30s"):
        runner.live_deadlines(tmp_path, 0.0, now=130.0)
    runner.save_json(tmp_path / "outcomes/0001.json", dict(status="completed"))
    runner.live_deadlines(tmp_path, 0.0, now=1700.0)
    with pytest.raises(TimeoutError, match="1800s"):
        runner.live_deadlines(tmp_path, 0.0, now=1800.0)


@pytest.mark.parametrize("now", [float("nan"), float("inf"), -1.0])
def test_invalid_lp_clock_fails(now):
    with pytest.raises(ValueError, match="clock"):
        runner.lp_deadline(0.0, now)


@pytest.fixture
def synthetic_worker(monkeypatch, tmp_path):
    for name in runner.THREADS:
        monkeypatch.setenv(name, "1")
    root = tmp_path / "project"
    root.mkdir()
    targets = {}
    for label in ("reference", "selected"):
        path = root / f"{label}.json"
        path.write_text("{}\n")
        targets[label] = dict(input=runner.reference(path))
    source = dict(matrix=producer.cases(), targets=targets)
    monkeypatch.setattr(runner, "ROOT", root)
    monkeypatch.setattr(runner, "sources", lambda *_: source)
    monkeypatch.setattr(runner, "space_check", lambda *args: dict(free_bytes=10 * 1024**3))
    counter = dict(surface=0, solve=0)

    def surface(data, nphi, ntheta, offset):
        counter["surface"] += 1
        return dict(
            points=np.array([[[1.0, 0.0, 0.0]]]),
            bounds={"phi": 1.0, "theta": 1.0},
            cover=0.01,
            pad=1e-14,
            radius_lower=0.9,
            nphi=nphi,
            ntheta=ntheta,
            offset=offset,
            full_torus=True,
        )

    def envelope(*args):
        return dict(
            centers=np.array([[0.0, 0.0]]),
            radii=np.array([0.2]),
            target_index=np.array([0]),
            grid_index=np.array([0]),
            expansions=np.array([0.1, 0.1]),
        )

    def problem(disks, K, center_r, r_floor):
        return dict(
            c=np.zeros(4 * K + 1),
            A=np.zeros((1, 4 * K + 1)),
            b=np.ones(1),
            lower=np.zeros(4 * K + 1),
            upper=np.ones(4 * K + 1),
            K=K,
        )

    def solve(model):
        counter["solve"] += 1
        x = np.zeros(len(model["c"]))
        x[0] = 0.2
        return dict(
            x=x.tolist(),
            slack=[1.0],
            inequality_marginals=[0.0],
            lower_marginals=np.zeros_like(x).tolist(),
            upper_marginals=np.zeros_like(x).tolist(),
            success=True,
            status=0,
            message="synthetic, not a scientific solve",
            objective=0.0,
        )

    monkeypatch.setattr(producer, "surface", surface)
    monkeypatch.setattr(producer, "origin", lambda *_: np.array([1.0, 0.0]))
    monkeypatch.setattr(producer, "envelope", envelope)
    monkeypatch.setattr(producer, "problem", problem)
    monkeypatch.setattr(producer, "solve", solve)

    def prepare():
        raw = tmp_path / "raw"
        raw.mkdir()
        for name in ("surfaces", "sets", "attempts", "outcomes"):
            (raw / name).mkdir()
        config = dict(
            parent_pid=os.getppid(),
            phase="geometry_initialization",
            source=source,
            start_monotonic=time.monotonic(),
        )
        runner.save_json(raw / "config.json", config)
        return raw

    return dict(prepare=prepare, counter=counter, source=source, root=root)


def test_full_synthetic_matrix_retains168_attempts_and_six_grids(synthetic_worker):
    raw = synthetic_worker["prepare"]()
    runner.worker(raw / "config.json")
    state = runner.read(raw / "completed-checkpoint.json")
    assert synthetic_worker["counter"] == dict(surface=6, solve=168)
    assert len(state["surfaces"]) == 6 and len(state["sets"]) == 12
    assert len(runner.collected_attempts(raw)) == 168
    assert runner.read(raw / "worker-terminal.json")["all_registered_attempts"] is True
    assert all(r["status"] == "exported" for r in state["sets"])
    for candidate in state["sets"]:
        snap = runner.read(runner.checked(candidate["snapshot"]))
        assert len(snap["physical"]) == 4 * candidate["case"]["nbase"]
        for coil in candidate["coils"]:
            a, b = [
                runner.read(runner.checked(runner.read(runner.checked(v["outcome"]))["solution"]))
                for v in coil["attempts"]
            ]
            assert a == b
    assert all(state[key] == 0 for key in ("field_calls", "gradient_calls", "equilibrium_solves"))


@pytest.mark.parametrize("mutation", ["parent", "phase", "source", "thread"])
def test_worker_preflight_rejects_before_geometry(synthetic_worker, mutation, monkeypatch):
    raw = synthetic_worker["prepare"]()
    config = runner.read(raw / "config.json")
    if mutation == "parent":
        config["parent_pid"] = -1
    elif mutation == "phase":
        config["phase"] = "field_fit"
    elif mutation == "source":
        config["source"] = {}
    else:
        monkeypatch.setenv("OMP_NUM_THREADS", "2")
    runner.save_json(raw / "config.json", config)
    with pytest.raises(ValueError, match="launching parent"):
        runner.worker(raw / "config.json")
    assert synthetic_worker["counter"] == dict(surface=0, solve=0)


def test_expired_worker_stops_before_geometry(synthetic_worker):
    raw = synthetic_worker["prepare"]()
    config = runner.read(raw / "config.json")
    config["start_monotonic"] -= 2000
    runner.save_json(raw / "config.json", config)
    runner.worker(raw / "config.json")
    assert runner.read(raw / "worker-terminal.json")["reason"] == "wall_budget"
    assert synthetic_worker["counter"] == dict(surface=0, solve=0)


def test_worker_call_cap_preserves_last_checkpoint(synthetic_worker, monkeypatch):
    raw = synthetic_worker["prepare"]()
    monkeypatch.setattr(runner, "MAX_ATTEMPTS", 2)
    runner.worker(raw / "config.json")
    assert len(runner.collected_attempts(raw)) == 2
    assert synthetic_worker["counter"]["solve"] == 2
    assert runner.read(raw / "worker-terminal.json")["reason"] == "worker_failure"
    assert len(runner.read(raw / "completed-checkpoint.json")["attempts"]) == 2


def test_repeat_solver_input_unaffected_by_solver_mutation(synthetic_worker, monkeypatch):
    raw = synthetic_worker["prepare"]()
    monkeypatch.setattr(runner, "MAX_ATTEMPTS", 2)
    original = producer.solve

    def mutate(model):
        assert model["c"][0] == 0.0
        solution = original(model)
        model["c"][0] = 999.0
        return solution

    monkeypatch.setattr(producer, "solve", mutate)
    runner.worker(raw / "config.json")
    rows = runner.collected_attempts(raw)
    assert len(rows) == 2 and all(row["status"] == "completed" for row in rows)
    assert runner.read(runner.checked(rows[0]["solution"])) == runner.read(
        runner.checked(rows[1]["solution"])
    )


def test_iofailure_preserves_unfinished_attempt_and_checkpoint(synthetic_worker, monkeypatch):
    raw = synthetic_worker["prepare"]()
    original = producer.solve

    def fail_second(model):
        if synthetic_worker["counter"]["solve"] == 1:
            raise OSError("synthetic IO failure")
        return original(model)

    monkeypatch.setattr(producer, "solve", fail_second)
    runner.worker(raw / "config.json")
    rows = runner.collected_attempts(raw)
    assert [r["status"] for r in rows] == ["completed", "attempted"]
    assert len(runner.read(raw / "completed-checkpoint.json")["attempts"]) == 1
    assert "synthetic IO failure" in runner.read(raw / "worker-terminal.json")["error"]


def test_late_native_result_keeps_raw_but_is_not_completed(synthetic_worker, monkeypatch):
    raw = synthetic_worker["prepare"]()
    original = producer.solve
    now = time.monotonic()
    clock = [now]
    config = runner.read(raw / "config.json")
    config["start_monotonic"] = now
    runner.save_json(raw / "config.json", config)
    monkeypatch.setattr(runner.time, "monotonic", lambda: clock[0])

    def late(model):
        result = original(model)
        clock[0] += 30.01
        return result

    monkeypatch.setattr(producer, "solve", late)
    runner.worker(raw / "config.json")
    assert runner.read(raw / "worker-terminal.json")["reason"] == "lp_wall_budget"
    rows = runner.collected_attempts(raw)
    assert len(rows) == 1 and rows[0]["status"] == "attempted"
    assert runner.checked(rows[0]["retained_uncompleted_solution"]).exists()
    assert not (raw / "outcomes/0000.json").exists()
    first_case = producer.cases()[0]["label"]
    assert (raw / "sets" / first_case / "coil-00/original.json").exists()
    assert runner.read(raw / "completed-checkpoint.json")["attempts"] == []


def test_late_solver_exception_remains_uncompleted_and_stops_matrix(synthetic_worker, monkeypatch):
    raw = synthetic_worker["prepare"]()
    now = time.monotonic()
    clock = [now]
    config = runner.read(raw / "config.json")
    config["start_monotonic"] = now
    runner.save_json(raw / "config.json", config)
    monkeypatch.setattr(runner.time, "monotonic", lambda: clock[0])

    def late_exception(model):
        synthetic_worker["counter"]["solve"] += 1
        clock[0] += 30.01
        raise ValueError("synthetic late native exception")

    monkeypatch.setattr(producer, "solve", late_exception)
    runner.worker(raw / "config.json")
    assert runner.read(raw / "worker-terminal.json")["reason"] == "lp_wall_budget"
    assert synthetic_worker["counter"]["solve"] == 1
    rows = runner.collected_attempts(raw)
    assert len(rows) == 1 and rows[0]["status"] == "attempted"
    assert not (raw / "outcomes/0000.json").exists()
    failure = runner.read(runner.checked(rows[0]["retained_uncompleted_failure"]))
    assert failure["error"] == "ValueError: synthetic late native exception"
    assert runner.read(raw / "completed-checkpoint.json")["attempts"] == []


def test_failed_lp_still_gets_unchanged_repeat_and_remaining_slots(synthetic_worker, monkeypatch):
    raw = synthetic_worker["prepare"]()
    original = producer.solve
    first = True

    def fail_once(model):
        nonlocal first
        if first:
            first = False
            synthetic_worker["counter"]["solve"] += 1
            raise ValueError("synthetic native solver error")
        return original(model)

    monkeypatch.setattr(producer, "solve", fail_once)
    runner.worker(raw / "config.json")
    rows = runner.collected_attempts(raw)
    assert len(rows) == 168 and rows[0]["status"] == "failed" and rows[1]["status"] == "completed"
    assert rows[0]["started_monotonic"] <= rows[0]["failed_end_monotonic"]
    assert rows[0]["elapsed_seconds"] < 30.0
    assert rows[0]["elapsed_seconds"] == (
        rows[0]["failed_end_monotonic"] - rows[0]["started_monotonic"]
    )
    assert runner.read(runner.checked(rows[0]["failure"]))["error"].startswith("ValueError:")
    state = runner.read(raw / "completed-checkpoint.json")
    assert state["sets"][0]["snapshot"] is None
    assert len(state["sets"]) == 12 and len(state["surfaces"]) == 6


def test_parent_requires_fresh_absolute_directory_before_sources(tmp_path, monkeypatch):
    monkeypatch.setattr(
        runner, "sources", lambda *_: pytest.fail("source binding not yet permitted")
    )
    for raw in (Path("relative"), tmp_path):
        with pytest.raises(ValueError, match="absolute fresh"):
            runner.run(raw)


@pytest.mark.parametrize(
    "process",
    [
        None,
        {},
        {"returncode": False},
        {"returncode": 0.0},
        {"returncode": "0"},
        {"returncode": None},
        {"returncode": 7},
        {"returncode": -9},
    ],
)
def test_successful_process_requires_exact_integer_zero(process):
    assert runner.successful_process(process) is False
    assert runner.successful_process({"returncode": 0}) is True


def test_parent_preserves_complete_worker_data_but_rejects_nonzero_exit(
    synthetic_worker, tmp_path, monkeypatch
):
    monkeypatch.setattr(runner.os, "getppid", runner.os.getpid)

    def guarded(command, **kwargs):
        kwargs["check"](kwargs["space_root"], kwargs["reserve_bytes"])
        runner.worker(Path(command[-1]))
        return dict(returncode=7, minimum_observed_free_bytes=10 * 1024**3)

    monkeypatch.setattr(runner, "guarded_run", guarded)
    raw = tmp_path / "parent-nonzero-exit"
    report = runner.run(raw)
    assert report["status"] == "incomplete"
    assert report["terminal"]["reason"] == "worker_exit_failure"
    assert report["terminal"]["worker_reason"] == "matrix_complete"
    assert report["terminal"]["process"]["returncode"] == 7
    assert report["attempted_lps"] == 168
    assert len(report["surfaces"]) == 6 and len(report["sets"]) == 12
    assert all(runner.checked(row["snapshot"]).exists() for row in report["sets"])
    checkpoint = runner.read(raw / "completed-checkpoint.json")
    assert len(checkpoint["attempts"]) == 168 and len(checkpoint["sets"]) == 12
    assert all(runner.checked(ref).exists() for ref in report["execution_artifacts"].values())
    assert runner.read(raw / "run.json") == report
    assert report["selected"] is None
    assert all(
        report[key] is False
        for key in ("geometry_pass", "field_pass", "transfer_pass", "step4_pass")
    )


def test_parent_uses_registered_guard_and_binds_partial_artifacts(
    synthetic_worker, tmp_path, monkeypatch
):
    monkeypatch.setattr(runner.os, "getppid", runner.os.getpid)
    seen = {}

    def guarded(command, **kwargs):
        seen.update(kwargs)
        kwargs["check"](kwargs["space_root"], kwargs["reserve_bytes"])
        runner.worker(Path(command[-1]))
        return dict(returncode=0, minimum_observed_free_bytes=10 * 1024**3)

    monkeypatch.setattr(runner, "guarded_run", guarded)
    report = runner.run(tmp_path / "parent-run")
    assert report["status"] == "completed" and report["attempted_lps"] == 168
    assert seen["interval"] == 0.5 and seen["reserve_bytes"] == 2 * 1024**3
    assert report["clock"]["timeout_seconds"] == 1800
    assert report["clock"]["lp_timeout_seconds"] == 30
    assert report["clock"]["termination_grace_seconds"] == 5
    assert report["selected"] is None and report["geometry_pass"] is False
    assert all(runner.checked(ref).exists() for ref in report["execution_artifacts"].values())
