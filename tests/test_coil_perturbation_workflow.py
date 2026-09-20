"""Small mocked geometry workflow controls; no registered project matrix runs."""

import copy
import os
import sys
import time
from pathlib import Path

import numpy as np
import pytest
from test_coil_perturbation import fixture
from test_coil_perturbation_samples import torus

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_coil_perturbation as runner  # noqa: E402


def old_ref(path):
    return {key: value for key, value in runner.ref(path).items() if key != "bytes"}


def source_fixture(path):
    seeds, sets = {}, [{} for _ in range(10)]
    target, audit = path / "target.json", path / "audit.json"
    runner.save(target, torus())
    for case in runner.matrix():
        snapshot, report = fixture(case["nbase"])
        snapshot["sources"] = {
            key: dict(input=old_ref(target), wout=old_ref(target)) for key in runner.TARGETS
        }
        file = path / f"seed-{case['nbase']}.json"
        runner.save(file, snapshot)
        seeds[case["label"]] = dict(
            snapshot=old_ref(file), geometry_report_index=case["geometry_report_index"]
        )
        sets[case["geometry_report_index"]] = report
    runner.save(audit, dict(sets=sets))
    return dict(
        matrix=runner.matrix(),
        seeds=seeds,
        geometry=dict(audit=old_ref(audit)),
        targets={key: old_ref(target) for key in runner.TARGETS},
    )


def check_reference_graph(document, seen=None):
    """Hash every reachable old/new reference, recursively including raw JSON."""
    seen = set() if seen is None else seen
    if isinstance(document, dict):
        if set(document) in ({"path", "sha256"}, {"path", "sha256", "bytes"}):
            path = runner.checked_source(document)
            identity = (str(path), document["sha256"])
            if identity not in seen:
                seen.add(identity)
                if path.suffix == ".json":
                    check_reference_graph(runner.read(path), seen)
        else:
            for value in document.values():
                check_reference_graph(value, seen)
    elif isinstance(document, list):
        for value in document:
            check_reference_graph(value, seen)
    return seen


class FakeSampler:
    """Only metadata work, never asserts a physical/direct geometry pass."""

    def __init__(self, snapshot, targets, check=None):
        self.nphysical = 4 * snapshot["nbase"]
        self._work = runner.empty_work()
        self.check = check

    def work(self):
        return copy.deepcopy(self._work)

    def sample(self, coefficients, level):
        self.check()
        for kind, counts in runner.grid_budget(self.nphysical, level["ncoil"]).items():
            for key, value in counts.items():
                self._work[kind][key] += value
        return dict(mock_only=np.array([1.0]))


def fake_certificate(seed, report, coefficients):
    return dict(
        status="uncertified",
        certified=False,
        calculation_complete=True,
        mock_only=True,
        checksum=float(np.sum(coefficients)),
    )


def setup_fake(monkeypatch, tmp_path):
    source = source_fixture(tmp_path)
    monkeypatch.setattr(runner, "sources", lambda root: copy.deepcopy(source))
    monkeypatch.setattr(runner, "Sampler", FakeSampler)
    monkeypatch.setattr(runner, "candidate_certificate", fake_certificate)
    monkeypatch.setattr(
        runner, "surface_points", lambda data: np.tile([1.0, 0.0, 0.0], (256**2, 1))
    )
    monkeypatch.setattr(
        runner,
        "space_check",
        lambda path, reserve: dict(
            path=str(path), required_bytes=reserve, free_bytes=4 * runner.GIB, sufficient=True
        ),
    )
    for key in runner.THREADS:
        monkeypatch.setenv(key, "1")
    return source


def worker_config(raw, source, index=0, registry=None):
    case = runner.matrix()[index]
    output = raw / case["label"]
    output.mkdir(parents=True)
    config = dict(
        case=case,
        source=source,
        output=str(output),
        parent_pid=os.getppid(),
        started_monotonic=time.monotonic(),
        build_surfaces=index == 0,
        surface_directory=str(raw / "surfaces"),
        surface_registry=registry,
        start_space=dict(required_bytes=3 * runner.GIB, free_bytes=4 * runner.GIB),
    )
    runner.save(output / "config.json", config)
    return output


def run_fake(monkeypatch, tmp_path):
    source = setup_fake(monkeypatch, tmp_path)
    output = worker_config(tmp_path / "raw", source)
    assert runner.worker(output / "config.json") == 0
    return runner.read(output / "worker.json"), output, source


def test_complete_fake_worker_negative_certificates_are_completed_and_pending(
    monkeypatch, tmp_path
):
    worker, output, source = run_fake(monkeypatch, tmp_path)
    assert worker["status"] == "completed"
    assert worker["work"] == {
        key: dict(attempted=n, completed=n)
        for key, n in dict(states=26, certificates=52, direct_grids=104, surfaces=2).items()
    }
    assert len(worker["states"]) == 26 and len(worker["operations"]) == 158
    assert len(worker["operation_attempts"]) == 158
    assert worker["source_before"] == worker["source_after"] == source
    assert worker["elapsed_seconds"] == worker["ended_monotonic"] - worker["started_monotonic"]
    for item in worker["states"]:
        state = runner.read(runner.checked(item))
        assert state["status"] == "completed" and state["repeat_exact"] is True
        assert len(state["direct"]) == 4 and len(state["certificates"]) == 2
        assert all(
            runner.read(runner.checked(c))["certified"] is False for c in state["certificates"]
        )
    first = runner.read(runner.checked(worker["states"][0]))
    repeat = runner.read(runner.checked(worker["states"][-1]))
    np.testing.assert_array_equal(
        runner.load_arrays(first["candidate"])["coefficients"],
        runner.load_arrays(repeat["candidate"])["coefficients"],
    )
    assert worker["scope"] == runner.SCOPE and worker["scope"]["qualification_pass"] is False
    assert runner.read(output / "checkpoint.json")["states"] == worker["states"]


def test_second_worker_reads_exact_shared_surfaces_without_rebuilding(monkeypatch, tmp_path):
    first, output, source = run_fake(monkeypatch, tmp_path)
    reference = first["surface_registry"]
    monkeypatch.setattr(runner, "surface_points", lambda data: pytest.fail("second surface build"))
    second = worker_config(output.parent, source, 1, reference)
    assert runner.worker(second / "config.json") == 0
    worker = runner.read(second / "worker.json")
    assert worker["fixed_surfaces"] == first["fixed_surfaces"]
    assert worker["surface_registry"] == reference
    assert worker["work"]["surfaces"] == dict(attempted=0, completed=0)
    assert len(worker["operations"]) == 156


@pytest.mark.parametrize("failure", [OSError("synthetic IO"), TimeoutError("synthetic deadline")])
def test_failed_next_state_preserves_last_successful_checkpoint(monkeypatch, tmp_path, failure):
    source = setup_fake(monkeypatch, tmp_path)
    output = worker_config(tmp_path / "raw", source)
    calls = 0
    checkpoint_bytes = []
    save = runner.save

    def capture(path, document):
        save(path, document)
        if path == output / "checkpoint.json":
            checkpoint_bytes.append(path.read_bytes())

    def fail_after_first_state(seed, report, coefficients):
        nonlocal calls
        calls += 1
        if calls == 3:
            raise failure
        return fake_certificate(seed, report, coefficients)

    monkeypatch.setattr(runner, "candidate_certificate", fail_after_first_state)
    monkeypatch.setattr(runner, "save", capture)
    assert runner.worker(output / "config.json") == 1
    checkpoint = runner.read(output / "checkpoint.json")
    assert len(checkpoint["states"]) == 1
    assert checkpoint["work"]["states"] == dict(attempted=1, completed=1)
    assert checkpoint_bytes == [(output / "checkpoint.json").read_bytes()]
    assert Path(checkpoint["inflight"]["path"]) == output / "state-00" / "checkpoint-inflight.json"
    assert runner.read(runner.checked(checkpoint["inflight"])) == dict(
        attempt=checkpoint["operation_attempts"][-1]
    )
    assert len(check_reference_graph(checkpoint)) > 20
    error = runner.read(output / "worker-error.json")
    assert error["work"]["certificates"] == dict(attempted=3, completed=2)
    assert error["error_type"] == type(failure).__name__
    assert error["elapsed_seconds"] == error["ended_monotonic"] - error["started_monotonic"]
    assert (output / "state-01" / "attempt.json").exists()
    assert not (output / "state-01" / "state.json").exists()


@pytest.mark.parametrize("failure_point", ["marker", "publication"])
def test_checkpoint_write_failure_preserves_previous_transitive_graph(
    monkeypatch, tmp_path, failure_point
):
    source = setup_fake(monkeypatch, tmp_path)
    output = worker_config(tmp_path / "raw", source)
    save, checkpoint_bytes = runner.save, []

    def fail_second_checkpoint(path, document):
        if (
            failure_point == "marker" and path == output / "state-01" / "checkpoint-inflight.json"
        ) or (
            failure_point == "publication"
            and path == output / "checkpoint.json"
            and checkpoint_bytes
        ):
            raise OSError("synthetic checkpoint IO failure")
        save(path, document)
        if path == output / "checkpoint.json":
            checkpoint_bytes.append(path.read_bytes())

    monkeypatch.setattr(runner, "save", fail_second_checkpoint)
    assert runner.worker(output / "config.json") == 1
    checkpoint = runner.read(output / "checkpoint.json")
    assert checkpoint_bytes == [(output / "checkpoint.json").read_bytes()]
    assert len(checkpoint["states"]) == 1
    assert len(check_reference_graph(checkpoint)) > 20
    assert runner.read(runner.checked(checkpoint["inflight"])) == dict(
        attempt=checkpoint["operation_attempts"][-1]
    )
    error = runner.read(output / "worker-error.json")
    assert error["work"]["states"] == dict(attempted=2, completed=2)
    assert error["work"]["certificates"] == dict(attempted=4, completed=4)
    assert error["work"]["direct_grids"] == dict(attempted=8, completed=8)
    assert error["error_type"] == "OSError"
    assert error["inflight"] != checkpoint["inflight"]
    assert runner.read(runner.checked(error["inflight"])) == dict(
        attempt=error["operation_attempts"][-1]
    )


def test_unfinished_direct_grid_preserves_lower_and_upper_work_prefix(monkeypatch, tmp_path):
    source = setup_fake(monkeypatch, tmp_path)
    output = worker_config(tmp_path / "raw", source)

    class Partial(FakeSampler):
        def sample(self, coefficients, level):
            self._work["fourier"].update(
                attempted=1, completed=0, points_attempted=self.nphysical * level["ncoil"]
            )
            raise TimeoutError("interrupted grid")

    monkeypatch.setattr(runner, "Sampler", Partial)
    assert runner.worker(output / "config.json") == 1
    error = runner.read(output / "worker-error.json")
    row = runner.read(runner.checked(error["operations"][-1]))
    assert row["sampling_work_before"] == runner.empty_work()
    assert row["sampling_reservation"] == runner.grid_budget(24, 256)
    assert row["sampling_work_after"]["fourier"]["attempted"] == 1
    assert row["sampling_work_after"]["fourier"]["completed"] == 0
    assert error["work"]["direct_grids"] == dict(attempted=1, completed=0)


def test_numerical_operation_error_preserves_all_later_registered_states(monkeypatch, tmp_path):
    source = setup_fake(monkeypatch, tmp_path)
    output = worker_config(tmp_path / "raw", source)
    calls = 0

    def bad_once(seed, report, coefficients):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise ValueError("synthetic invalid certificate")
        return fake_certificate(seed, report, coefficients)

    monkeypatch.setattr(runner, "candidate_certificate", bad_once)
    assert runner.worker(output / "config.json") == 1
    worker = runner.read(output / "worker.json")
    assert len(worker["states"]) == 26
    assert worker["work"]["certificates"] == dict(attempted=52, completed=51)
    assert worker["work"]["direct_grids"] == dict(attempted=104, completed=104)
    assert worker["work"]["states"] == dict(attempted=26, completed=25)


def test_source_change_prevents_any_geometric_attempt(monkeypatch, tmp_path):
    source = setup_fake(monkeypatch, tmp_path)
    output = worker_config(tmp_path / "raw", source)
    monkeypatch.setattr(runner, "sources", lambda root: dict(source, mutated=True))
    assert runner.worker(output / "config.json") == 1
    assert not (output / "operations").exists()
    assert runner.read(output / "worker-error.json")["states"] == []


def test_surface_partial_failure_prevents_registry_and_states(monkeypatch, tmp_path):
    source = setup_fake(monkeypatch, tmp_path)
    output = worker_config(tmp_path / "raw", source)
    calls = 0

    def failing(data):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ValueError("second surface failed")
        return np.tile([1.0, 0.0, 0.0], (256**2, 1))

    monkeypatch.setattr(runner, "surface_points", failing)
    assert runner.worker(output / "config.json") == 1
    assert (output.parent / "surfaces" / "reference.json").exists()
    assert not (output.parent / "surfaces" / "registry.json").exists()
    error = runner.read(output / "worker-error.json")
    assert error["work"]["surfaces"] == dict(attempted=2, completed=1)
    assert error["work"]["states"]["attempted"] == 0


def test_ledger_cap_prevents_callback_and_new_attempt(monkeypatch, tmp_path):
    ledger = runner.Ledger(tmp_path, lambda: None, False)
    ledger.work["certificates"]["attempted"] = 52
    with pytest.raises(runner.BudgetExceeded):
        ledger.perform("certificates", {}, lambda path: pytest.fail("dispatch"))
    assert list((tmp_path / "operations").iterdir()) == []


def test_attempt_is_saved_before_callback(tmp_path):
    ledger = runner.Ledger(tmp_path, lambda: None, False)

    def inspect(path):
        assert path.with_suffix(".attempt.json").exists()
        assert (tmp_path / "inflight.json").exists()
        assert ledger.work["certificates"] == dict(attempted=1, completed=0)
        return dict(result="synthetic")

    record, _ = ledger.perform("certificates", {}, inspect)
    assert record["status"] == "completed"


def test_parent_loss_stops_before_disk_or_work(monkeypatch, tmp_path):
    monkeypatch.setattr(runner.os, "getppid", lambda: 20)
    monkeypatch.setattr(runner, "space_check", lambda *args: pytest.fail("disk after parent loss"))
    with pytest.raises(runner.ParentLost):
        runner.Guard(tmp_path, 21, time.monotonic())()


@pytest.mark.parametrize("now", [1800.0, 1801.0, float("nan"), -1.0])
def test_clock_limit_is_fail_closed(now):
    with pytest.raises((ValueError, TimeoutError)):
        runner.deadline(0.0, now)


def test_guarded_process_uses_parent_deadline_poll_and_live_reserve(monkeypatch, tmp_path):
    seen = {}

    def guarded(command, **kwargs):
        seen.update(kwargs)
        assert kwargs["check"](tmp_path, 2 * runner.GIB)["free_bytes"] == 4 * runner.GIB
        return dict(returncode=0, minimum_observed_free_bytes=4 * runner.GIB)

    monkeypatch.setattr(runner, "guarded_run", guarded)
    monkeypatch.setattr(
        runner, "space_check", lambda path, reserve: dict(free_bytes=4 * runner.GIB)
    )
    process = runner.run_process(["synthetic"], tmp_path, {}, time.monotonic())
    assert process["returncode"] == 0
    assert seen["interval"] == 0.5 and seen["reserve_bytes"] == 2 * runner.GIB


def test_parent_keeps_failed_first_and_marks_second_unexecuted(monkeypatch, tmp_path):
    source = setup_fake(monkeypatch, tmp_path)
    launches = []

    def failed(command, directory, env, started):
        launches.append(command)
        return dict(returncode=1, timed_out=False, elapsed_seconds=0.1)

    monkeypatch.setattr(runner, "run_process", failed)
    result = runner.run(tmp_path / "result")
    assert len(launches) == 1
    assert result["source_before"] == source
    assert result["producer_complete"] is False
    assert [runner.read(runner.checked(r))["status"] for r in result["rows"]] == [
        "error",
        "not-executed",
    ]
    first = runner.read(runner.checked(result["rows"][0]))
    assert (
        runner.read(runner.checked(first["config"]))["start_space"]["required_bytes"]
        == 3 * runner.GIB
    )


def test_parent_reuses_completed_surfaces_after_first_class_failure(monkeypatch, tmp_path):
    setup_fake(monkeypatch, tmp_path)
    monkeypatch.setattr(runner.os, "getppid", runner.os.getpid)
    execute = runner.execute_state
    launches = []

    def fail_first_class(output, state, seed, *args):
        if seed["nbase"] == 6 and state["index"] == 1:
            raise OSError("synthetic first-class state failure")
        return execute(output, state, seed, *args)

    def child(command, directory, env, started):
        launches.append(runner.read(directory / "config.json"))
        code = runner.worker(directory / "config.json")
        return dict(
            returncode=code,
            timed_out=False,
            elapsed_seconds=time.monotonic() - started,
            minimum_observed_free_bytes=4 * runner.GIB,
        )

    monkeypatch.setattr(runner, "execute_state", fail_first_class)
    monkeypatch.setattr(runner, "run_process", child)
    result = runner.run(tmp_path / "serial")
    assert len(launches) == 2
    assert launches[0]["surface_registry"] is None
    assert launches[1]["surface_registry"] == result["surface_registry"]
    assert launches[1]["build_surfaces"] is False
    rows = [runner.read(runner.checked(item)) for item in result["rows"]]
    assert [row["status"] for row in rows] == ["error", "completed"]
    second = runner.read(runner.checked(rows[1]["worker"]))
    assert second["work"]["surfaces"] == dict(attempted=0, completed=0)
    assert result["producer_complete"] is False and result["all_pass"] is False
    assert runner.read(runner.checked(result["checkpoint"])) == dict(rows=result["rows"])


def test_parent_guard_timeout_records_unknown_return_code(monkeypatch, tmp_path):
    def interrupted(*args, **kwargs):
        raise TimeoutError("synthetic parent guard")

    monkeypatch.setattr(runner, "guarded_run", interrupted)
    record = runner.run_process(["mock"], tmp_path, {}, time.monotonic())
    assert record["returncode"] is None and record["timed_out"] is True
    assert record["error_type"] == "TimeoutError"


@pytest.mark.parametrize("path", ["relative", None])
def test_output_must_be_fresh_absolute(tmp_path, path):
    output = Path(path) if path else tmp_path
    with pytest.raises((ValueError, FileExistsError)):
        runner.run(output)


@pytest.mark.parametrize(
    "mutation",
    [
        dict(returncode=False),
        dict(elapsed_seconds=float("nan")),
        dict(returncode=-15),
        dict(timed_out=True),
    ],
)
def test_parent_rejects_false_successful_process(mutation):
    source, case = {}, runner.matrix()[0]
    document = dict(
        status="completed",
        case=case,
        source_before=source,
        source_after=source,
        threads={key: "1" for key in runner.THREADS},
        scope=runner.SCOPE,
        started_monotonic=1.0,
        ended_monotonic=2.0,
        elapsed_seconds=1.0,
    )
    process = dict(returncode=0, timed_out=False, elapsed_seconds=1.0)
    process.update(mutation)
    with pytest.raises(ValueError):
        runner.process_complete(process, document, case, source, 1.0)


@pytest.mark.parametrize("elapsed", [0.5, 1.5])
def test_parent_rejects_inconsistent_worker_clocks(elapsed):
    case, source = runner.matrix()[0], {}
    document = dict(
        status="completed",
        case=case,
        source_before=source,
        source_after=source,
        threads={key: "1" for key in runner.THREADS},
        scope=runner.SCOPE,
        started_monotonic=1.0,
        ended_monotonic=2.0,
        elapsed_seconds=elapsed,
    )
    process = dict(returncode=0, timed_out=False, elapsed_seconds=2.0)
    with pytest.raises(ValueError, match="timely"):
        runner.process_complete(process, document, case, source, 1.0)


def test_parent_rejects_worker_end_after_process_return():
    case, source = runner.matrix()[0], {}
    document = dict(
        status="completed",
        case=case,
        source_before=source,
        source_after=source,
        threads={key: "1" for key in runner.THREADS},
        scope=runner.SCOPE,
        started_monotonic=1.0,
        ended_monotonic=2.0,
        elapsed_seconds=1.0,
    )
    process = dict(returncode=0, timed_out=False, elapsed_seconds=0.5)
    with pytest.raises(ValueError, match="timely"):
        runner.process_complete(process, document, case, source, 1.0)
