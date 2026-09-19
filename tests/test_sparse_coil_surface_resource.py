"""Light orchestration/accounting tests; never execute the registered resource matrix."""

import copy
import os
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import qualify_sparse_coil_surface as runner  # noqa: E402


def test_registered_matrix_and_exact_attempt_plan():
    matrix = runner.matrix()
    assert [(cell["nbase"], cell["order"], cell["ncoil"], cell["backend"]) for cell in matrix] == [
        (nbase, order, ncoil, backend)
        for nbase, order in ((6, 5), (8, 7))
        for ncoil in (256, 512)
        for backend in ("native", "sparse")
    ]
    seed = np.arange(198, dtype=float) / 1000
    plan = runner.states(seed)
    assert len(plan) == 13
    assert sum(item["gradient"] for item in plan) == 5
    for plus, minus in zip(plan[1:9:2], plan[2:9:2], strict=True):
        assert plus["step"] == minus["step"] and plus["sign"] == 1 and minus["sign"] == -1
        assert np.allclose(plus["x"] + minus["x"], 2 * seed, rtol=0, atol=1e-16)
        assert np.isclose(np.linalg.norm(plus["x"] - seed), plus["step"], rtol=1e-10)
    assert np.array_equal(plan[0]["x"], plan[9]["x"])
    assert np.array_equal(plan[0]["x"], plan[12]["x"])
    assert np.array_equal(plan[10]["x"], plan[11]["x"])
    assert plan[10]["x"][0] == seed[0] + 0.002
    assert np.array_equal(plan[10]["x"][1:], seed[1:])
    assert runner.SCOPE["field_calls"] == 0 and runner.SCOPE["step4_pass"] is False


@pytest.mark.parametrize(
    "platform,raw,expected", [("darwin", 1536, 1536), ("linux", 1536, 1572864)]
)
def test_platform_correct_peak_rss(platform, raw, expected):
    assert runner.peak_rss_bytes(raw, platform) == expected
    assert runner.MAX_RSS_BYTES == 1610612736


@pytest.mark.parametrize("raw,platform", [(-1, "darwin"), (np.nan, "linux"), (10, "win32")])
def test_unknown_or_invalid_rss_is_not_a_resource_pass(raw, platform):
    with pytest.raises(ValueError):
        runner.peak_rss_bytes(raw, platform)


def test_deadline_fails_at_boundary_and_invalid_clocks():
    assert runner.deadline(5.0, 124.999) < 120
    with pytest.raises(TimeoutError):
        runner.deadline(5.0, 125.0)
    for now in (4.0, np.nan):
        with pytest.raises(ValueError):
            runner.deadline(5.0, now)


def test_tolerance_cannot_hide_large_nearzero_component():
    assert runner.tolerance([1.0, 0.0], [1.0 + 1e-11, 1e-13])["pass_"]
    assert not runner.tolerance([1.0, 0.0], [1.0, 1e-10])["pass_"]
    assert not runner.tolerance([1.0], [1.0, 2.0])["pass_"]
    assert not runner.tolerance([np.nan], [1.0])["pass_"]


def test_references_bind_bytes_and_json_rejects_nonfinite(tmp_path):
    path = tmp_path / "value.json"
    runner.save(path, dict(value=np.float64(0.25)))
    reference = runner.ref(path)
    assert runner.checked(reference) == path
    path.write_text("changed")
    with pytest.raises(ValueError, match="bytes changed"):
        runner.checked(reference)
    for invalid in (np.inf, np.array([np.nan]), {1: "integer key"}):
        with pytest.raises(TypeError):
            runner.save(tmp_path / "invalid.json", invalid)


class FakeCurve:
    def __init__(self, names):
        self.local_dof_names = list(reversed(names))
        self.local_full_dof_names = self.local_dof_names.copy()
        self.local_full_x = np.arange(len(names), dtype=float) / 1000


class FakePhysical:
    def __init__(self, curve, ncoil, sign):
        self.curve, self.ncoil, self.sign = curve, ncoil, sign

    def gamma(self):
        value = self.curve.local_full_x[self.curve.local_full_dof_names.index("xc(0)")]
        return np.tile([self.sign * value, 0.2, 0.3], (self.ncoil, 1))

    def gammadash(self):
        return np.tile([1.0, 0.2, 0.3], (self.ncoil, 1))


class FakeObjective:
    def __init__(self, base, multiplier=1.0):
        self.base, self.multiplier = base, multiplier

    def J(self):
        return 1.0 + self.multiplier * sum(
            float(c.local_full_x @ c.local_full_x) for c in self.base
        )

    def dJ(self, partials=False):
        assert partials is True
        return lambda curve: 2 * self.multiplier * curve.local_full_x

    def shortest_distance(self):
        return 0.025


def fake_model(case):
    names = runner.local_names(case["order"])
    base = [FakeCurve(names) for _ in range(case["nbase"])]
    physical = [
        FakePhysical(curve, case["ncoil"], -1 if flip else 1)
        for period in range(2)
        for flip in (False, True)
        for curve in base
    ]
    return dict(
        base=base,
        physical=physical,
        points=np.ones((128**2, 3)),
        normals=np.ones((128**2, 3)),
        local_names=names,
        cp=FakeObjective(base),
        cc=FakeObjective(base, 2.0),
    )


def fake_worker(monkeypatch, tmp_path, *, evaluate=None):
    case = runner.matrix()[0]
    directory = tmp_path / "worker"
    directory.mkdir()
    source = dict(fake_unit_test_only=True)
    monkeypatch.setattr(runner, "sources", lambda: source)
    monkeypatch.setattr(runner, "make_model", fake_model)
    monkeypatch.setattr(runner, "peak_rss_bytes", lambda: 12345)
    for name in runner.THREADS:
        monkeypatch.setenv(name, "1")
    if evaluate is not None:
        monkeypatch.setattr(runner, "evaluate", evaluate)
    config = dict(
        case=case,
        output=str(directory),
        parent_pid=os.getppid(),
        started_monotonic=runner.time.monotonic(),
        source=source,
    )
    runner.save(directory / "config.json", config)
    code = runner.worker(directory / "config.json")
    return directory, code


def test_fake_worker_complete_accounting_and_named_not_positional_vjps(monkeypatch, tmp_path):
    directory, code = fake_worker(monkeypatch, tmp_path)
    assert code == 0
    document = runner.read(directory / "worker.json")
    assert runner.worker_checks(document)["all_pass"]
    assert len(document["rows"]) == 13
    assert len(list(directory.glob("attempt-*.json"))) == 13
    assert document["work"]["cp"] == dict(
        J_calls=13,
        dJ_calls=5,
        named_local_extractions=30,
        requested_physical_curve_vjp_pairs=120,
        shortest_distance_calls=3,
    )
    first = runner.read(runner.checked(document["rows"][0]))
    data = runner.row_arrays(first)
    assert np.array_equal(data["cp_gradient"], 2 * data["x"])
    assert np.array_equal(data["cc_gradient"], 4 * data["x"])
    assert runner.compare_pair(document, copy.deepcopy(document))["all_pass"]


@pytest.mark.parametrize("mutation", ["missing", "reorder", "work", "gradient"])
def test_fake_complete_sequence_mutations_fail(monkeypatch, tmp_path, mutation):
    directory, _ = fake_worker(monkeypatch, tmp_path)
    document = runner.read(directory / "worker.json")
    if mutation == "missing":
        document["rows"].pop()
    elif mutation == "reorder":
        document["rows"][1], document["rows"][2] = document["rows"][2], document["rows"][1]
    elif mutation == "work":
        document["work"]["cp"]["J_calls"] -= 1
    else:
        row = runner.read(runner.checked(document["rows"][0]))
        row["gradient"] = 1
        runner.save(directory / "tampered-row.json", row)
        document["rows"][0] = runner.ref(directory / "tampered-row.json")
    if mutation == "work":
        assert not runner.worker_checks(document)["all_pass"]
    else:
        with pytest.raises(ValueError):
            runner.worker_checks(document)


def test_worker_failure_preserves_last_checkpoint_and_attempt(monkeypatch, tmp_path):
    original = runner.evaluate
    calls = []

    def fail_second(model, state, work, case, record_work):
        calls.append(state["label"])
        if len(calls) == 2:
            raise RuntimeError("injected synthetic failure")
        return original(model, state, work, case, record_work)

    directory, code = fake_worker(monkeypatch, tmp_path, evaluate=fail_second)
    assert code == 1
    assert len(runner.read(directory / "checkpoint.json")["rows"]) == 1
    assert (directory / "attempt-01.json").exists()
    assert not (directory / "raw-01.json").exists()
    assert not (directory / "worker.json").exists()
    assert runner.read(directory / "worker-error.json")["error_type"] == "RuntimeError"


def test_late_numerical_output_retained_but_not_checkpointed(monkeypatch, tmp_path):
    checks = []

    def expire_after_second_numeric_result(started):
        checks.append(started)
        if len(checks) == 5:
            raise TimeoutError("injected late completion")
        return 0.1

    monkeypatch.setattr(runner, "deadline", expire_after_second_numeric_result)
    directory, code = fake_worker(monkeypatch, tmp_path)
    assert code == 1
    assert len(runner.read(directory / "checkpoint.json")["rows"]) == 1
    assert (directory / "raw-01.npz").exists()
    assert (directory / "raw-01.json").exists()
    assert not (directory / "worker.json").exists()
    assert runner.read(directory / "worker-error.json")["error_type"] == "TimeoutError"


def test_cache_repeat_does_not_reset_coefficients(monkeypatch):
    model = fake_model(runner.matrix()[0])
    x = runner.get_x(model)
    changed = runner.states(x)[10]
    runner.set_x(model, changed["x"])
    monkeypatch.setattr(
        runner, "set_x", lambda *args: pytest.fail("cached repeat reset coefficients")
    )
    work = {
        name: dict(
            J_calls=0,
            dJ_calls=0,
            named_local_extractions=0,
            requested_physical_curve_vjp_pairs=0,
            shortest_distance_calls=0,
        )
        for name in ("cp", "cc")
    }
    runner.evaluate(model, runner.states(x)[11], work, runner.matrix()[0])
    assert work["cp"]["J_calls"] == work["cp"]["dJ_calls"] == 1


def test_parent_timeout_stops_only_owned_child_and_keeps_files(monkeypatch, tmp_path):
    class Process:
        returncode = None
        pid = 76543

        def poll(self):
            return None

    process = Process()
    launches, stopped = [], []
    monkeypatch.setattr(
        runner.subprocess,
        "Popen",
        lambda command, **kwargs: launches.append((command, kwargs)) or process,
    )
    monkeypatch.setattr(runner, "space_check", lambda *args: dict(free_bytes=4 * runner.GIB))
    monkeypatch.setattr(runner.time, "monotonic", lambda: 121.0)

    def stop(child):
        stopped.append(child)
        child.returncode = -15

    monkeypatch.setattr(runner, "stop_owned_process", stop)
    runner.save(tmp_path / "checkpoint.json", dict(last_success=2))
    before = (tmp_path / "checkpoint.json").read_bytes()
    outcome = runner.run_process(["fake", "--worker"], output=tmp_path, env={}, started=0.0)
    assert outcome["timed_out"] and outcome["returncode"] == -15
    assert stopped == [process] and launches[0][1]["start_new_session"] is True
    assert (tmp_path / "checkpoint.json").read_bytes() == before


def test_parent_tries_all_eight_failed_workers_without_admission(monkeypatch, tmp_path):
    launches, reserves = [], []
    monkeypatch.setattr(runner, "sources", lambda: dict(fake_unit_test_only=True))
    monkeypatch.setattr(
        runner,
        "space_check",
        lambda path, reserve: reserves.append(reserve) or dict(free_bytes=4 * runner.GIB),
    )

    def fail(command, **kwargs):
        launches.append(command)
        return dict(returncode=1, timed_out=False, elapsed_seconds=0.01)

    monkeypatch.setattr(runner, "run_process", fail)
    result = runner.qualify(tmp_path / "fresh")
    assert len(launches) == 8 and len(result["rows"]) == 8
    assert reserves == [3 * runner.GIB] * 9  # Initial matrix + every cell independently.
    assert result["status"] == "completed" and result["all_pass"] is False
    assert result["scope"]["search_allowed"] is False
    assert all(runner.read(runner.checked(row))["status"] == "failed" for row in result["rows"])
    assert len(result["pairs"]) == 4 and not any(pair["all_pass"] for pair in result["pairs"])


def valid_completion():
    case, source = runner.matrix()[0], {"unit_test_only": True}
    process = dict(returncode=0, timed_out=False, elapsed_seconds=2.0)
    document = dict(
        status="completed",
        case=case,
        elapsed_seconds=1.9,
        ended_monotonic=11.9,
        source_before=source,
        source_after=source,
        scope=runner.SCOPE,
        threads={key: "1" for key in runner.THREADS},
        peak_rss_bytes=100,
        rss_pass=True,
    )
    return process, document, case, source


@pytest.mark.parametrize(
    "container,key,value",
    [
        ("process", "returncode", False),
        ("process", "returncode", 0.0),
        ("process", "returncode", 1),
        ("process", "timed_out", 0),
        ("process", "elapsed_seconds", -1.0),
        ("process", "elapsed_seconds", np.nan),
        ("process", "elapsed_seconds", np.inf),
        ("process", "elapsed_seconds", True),
        ("process", "elapsed_seconds", 120.0),
        ("document", "elapsed_seconds", -1.0),
        ("document", "elapsed_seconds", np.nan),
        ("document", "elapsed_seconds", 120.0),
        ("document", "elapsed_seconds", False),
        ("document", "ended_monotonic", np.inf),
        ("document", "ended_monotonic", 9.0),
        ("document", "ended_monotonic", 130.0),
        ("document", "peak_rss_bytes", -1),
        ("document", "peak_rss_bytes", 100.0),
        ("document", "peak_rss_bytes", False),
        ("document", "peak_rss_bytes", np.nan),
        ("document", "peak_rss_bytes", np.inf),
        ("document", "rss_pass", 1),
    ],
)
def test_strict_source_bound_completion_types_and_ranges(container, key, value):
    process, document, case, source = valid_completion()
    runner.completed_worker(process, document, case, source, 10.0)
    (process if container == "process" else document)[key] = value
    with pytest.raises(ValueError):
        runner.completed_worker(process, document, case, source, 10.0)


def test_oversize_worker_is_preserved_but_not_resource_qualified():
    process, document, case, source = valid_completion()
    document["peak_rss_bytes"] = runner.MAX_RSS_BYTES + 1
    document["rss_pass"] = False
    runner.completed_worker(process, document, case, source, 10.0)
    assert document["rss_pass"] is False


def test_parent_source_mutation_or_io_failure_never_overwrites_existing_results(
    monkeypatch, tmp_path
):
    directory = tmp_path / "fresh"
    monkeypatch.setattr(
        runner, "_qualify", lambda output: (_ for _ in ()).throw(OSError("injected IO"))
    )
    with pytest.raises(OSError):
        runner.qualify(directory)
    terminal = (directory / "terminal-error.json").read_bytes()
    with pytest.raises(FileExistsError):
        runner.qualify(directory)
    assert (directory / "terminal-error.json").read_bytes() == terminal
    with pytest.raises(ValueError, match="absolute"):
        runner.qualify(Path("relative-path"))
