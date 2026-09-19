"""Mock-only block-reference workflow checks; no native kernels or project data."""

import copy
import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import qualify_block_native_reference as runner  # noqa: E402


def test_exact_four_cell_matrix_kernel_budgets_and_scope():
    assert [
        (case["nbase"], case["order"], case["ncoil"], case["backend"]) for case in runner.matrix()
    ] == [(n, m, q, "block-native") for n, m in ((6, 5), (8, 7)) for q in (256, 512)]
    for case in runner.matrix():
        factor = case["nbase"] // 2
        expected = dict(
            J=6656 * factor,
            position=2560 * factor,
            tangent=2560 * factor,
            minimum=1536 * factor,
            position_vjp=40 * factor,
            tangent_vjp=40 * factor,
        )
        assert runner.expected_kernel_work(case, 13) == {
            key: dict(attempted=value, completed=value) for key, value in expected.items()
        }
        assert runner.expected_kernel_work(case, 0) == runner.zero_kernel_work()
    assert runner.SCOPE["startup_pass"] is runner.SCOPE["step4_pass"] is False
    for bad in (True, -1, 14, 13.0):
        with pytest.raises(ValueError):
            runner.expected_kernel_work(runner.matrix()[0], bad)


@pytest.mark.parametrize("mutation", ["bool", "float", "negative", "extra", "missing"])
def test_kernel_counter_types_and_complete_keys_fail_closed(mutation):
    counts = runner.zero_kernel_work()
    original = copy.deepcopy(counts)
    if mutation == "bool":
        counts["J"]["attempted"] = False
    elif mutation == "float":
        counts["J"]["completed"] = 0.0
    elif mutation == "negative":
        counts["J"]["completed"] = -1
    elif mutation == "extra":
        counts["extra"] = dict(attempted=0, completed=0)
    else:
        counts["J"].pop("attempted")
    with pytest.raises(ValueError):
        runner.require_kernel_work(counts, original)


class FakeCurve:
    def __init__(self, names):
        self.local_dof_names = list(reversed(names))
        self.local_full_dof_names = self.local_dof_names.copy()
        self.local_full_x = np.arange(len(names), dtype=float) / 1000


class FakePhysical:
    def __init__(self, curve, count, flip):
        self.curve, self.count, self.sign = curve, count, -1 if flip else 1

    def gamma(self):
        value = self.curve.local_full_x[self.curve.local_dof_names.index("xc(0)")]
        return np.tile([self.sign * value, 0.2, 0.3], (self.count, 1))

    def gammadash(self):
        return np.tile([1.0, 0.2, 0.3], (self.count, 1))


class FakeObjective:
    def __init__(self, base, multiplier=1.0):
        self.base, self.multiplier = base, multiplier

    def J(self):
        return 1 + self.multiplier * sum(float(c.local_full_x @ c.local_full_x) for c in self.base)

    def dJ(self, partials=False):
        assert partials is True
        return lambda curve: 2 * self.multiplier * curve.local_full_x

    def shortest_distance(self):
        return 0.025


class FakeBlockObjective(FakeObjective):
    def __init__(self, base, progress, fail_call=None):
        super().__init__(base)
        self.progress, self.fail_call = progress, fail_call
        self.work, self.index, self.calls = runner.zero_kernel_work(), 0, 0

    def kernel_work(self):
        return copy.deepcopy(self.work)

    def phase(self, phase):
        self.calls += 1
        reserved = runner.reservation(phase)
        for curve_index in range(4 * len(self.base)):
            before = self.kernel_work()
            upper = {
                q: {kind: before[q][kind] + reserved[q] for kind in ("attempted", "completed")}
                for q in runner.QUANTITIES
            }
            event = dict(
                index=self.index,
                curve_index=curve_index,
                phase=phase,
                reservation=reserved,
                work_before=before,
                upper_work=upper,
            )
            self.progress(dict(event, status="reserved", work=self.kernel_work()))
            if self.fail_call == self.calls:
                q = next(q for q, count in reserved.items() if count)
                self.work[q]["attempted"] += 1
                self.progress(
                    dict(
                        event,
                        status="error",
                        work=self.kernel_work(),
                        error="injected kernel error",
                    )
                )
                raise ArithmeticError("injected kernel error")
            self.work = copy.deepcopy(upper)
            self.progress(dict(event, status="completed", work=self.kernel_work()))
            self.index += 1

    def J(self):
        self.phase("J")
        return super().J()

    def dJ(self, partials=False):
        self.phase("dJ")
        return super().dJ(partials=partials)

    def shortest_distance(self):
        self.phase("minimum")
        return super().shortest_distance()


def fake_model(case, callback, fail_call=None):
    names = runner.legacy.local_names(case["order"])
    base = [FakeCurve(names) for _ in range(case["nbase"])]
    physical = [
        FakePhysical(curve, case["ncoil"], flip)
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
        cp=FakeBlockObjective(base, callback, fail_call),
        cc=FakeObjective(base, 2.0),
    )


def run_fake_worker(monkeypatch, directory, *, fail_call=None):
    directory.mkdir()
    source = dict(matrix=runner.matrix(), unit_test_only=True)
    monkeypatch.setattr(runner, "sources", lambda root: source)
    monkeypatch.setattr(
        runner, "make_model", lambda case, progress: fake_model(case, progress, fail_call)
    )
    monkeypatch.setattr(runner.legacy, "peak_rss_bytes", lambda: 2000)
    for name in runner.THREADS:
        monkeypatch.setenv(name, "1")
    config = dict(
        case=runner.matrix()[0],
        output=str(directory),
        parent_pid=os.getppid(),
        source=source,
        started_monotonic=runner.time.monotonic(),
    )
    runner.save(directory / "config.json", config)
    return runner.worker(directory / "config.json")


def test_fake_worker_complete_raw_and_exact_progress_accounting(monkeypatch, tmp_path):
    directory = tmp_path / "worker"
    assert run_fake_worker(monkeypatch, directory) == 0
    document = runner.read(directory / "worker.json")
    assert runner.legacy.worker_checks(document)["all_pass"] is True
    checks = runner.kernel_checks(document)
    assert checks["all_pass"] and checks["progress_events"] == 1008
    assert checks["curve_phase_reservations"] == 504
    assert len(document["rows"]) == len(document["attempts"]) == 13
    assert document["kernel_work"]["J"] == dict(attempted=19968, completed=19968)
    first = runner.read(runner.checked(document["rows"][0]))
    arrays = runner.legacy.row_arrays(first)
    assert np.array_equal(arrays["cp_gradient"], 2 * arrays["x"])
    assert document["scope"]["startup_pass"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        "counts",
        "prefix",
        "truncated",
        "reservation",
        "state",
        "backward_time",
        "outside_attempt",
        "attempt_identity",
    ],
)
def test_bad_kernel_history_cannot_pass(monkeypatch, tmp_path, mutation):
    directory = tmp_path / "worker"
    assert run_fake_worker(monkeypatch, directory) == 0
    document = runner.read(directory / "worker.json")
    if mutation == "counts":
        document["kernel_work"]["position"]["completed"] -= 1
    elif mutation == "prefix":
        row = runner.read(runner.checked(document["rows"][1]))
        row["kernel_progress_events"] -= 2
        runner.save(directory / "bad-row.json", row)
        document["rows"][1] = runner.ref(directory / "bad-row.json")
    elif mutation == "attempt_identity":
        row = runner.read(runner.checked(document["rows"][0]))
        attempt = runner.read(runner.checked(row["attempt"]))
        attempt["gradient"] = 1
        runner.save(directory / "bad-attempt.json", attempt)
        document["attempts"][0] = runner.ref(directory / "bad-attempt.json")
        row["attempt"] = document["attempts"][0]
        runner.save(directory / "bad-row.json", row)
        document["rows"][0] = runner.ref(directory / "bad-row.json")
    else:
        records = [
            json.loads(line)
            for line in runner.checked(document["kernel_progress"]).read_text().splitlines()
        ]
        if mutation == "truncated":
            records = records[:-2]
        elif mutation == "reservation":
            records[0]["event"]["reservation"]["J"] -= 1
        elif mutation == "backward_time":
            records[1]["monotonic"] = records[0]["monotonic"] - 1.0
        elif mutation == "outside_attempt":
            records[0]["monotonic"] = document["ended_monotonic"] + 1.0
        else:
            records[0]["state_index"] = 1
        path = directory / "bad-progress.jsonl"
        path.write_text("".join(json.dumps(record) + "\n" for record in records))
        runner.save(directory / "bad-inflight.json", records[-1])
        document["kernel_progress"] = runner.ref(path)
        document["kernel_progress_events"] = len(records)
        document["kernel_inflight"] = runner.ref(directory / "bad-inflight.json")
    with pytest.raises(ValueError):
        runner.kernel_checks(document)


def test_failed_kernel_retains_prefix_and_conservative_reserved_upper(monkeypatch, tmp_path):
    directory = tmp_path / "worker"
    assert run_fake_worker(monkeypatch, directory, fail_call=4) == 1
    checkpoint = runner.read(directory / "checkpoint.json")
    error = runner.read(directory / "worker-error.json")
    inflight = runner.read(runner.checked(error["kernel_inflight"]))
    assert len(checkpoint["rows"]) == 1
    assert error["kernel_work"]["J"] == dict(attempted=1537, completed=1536)
    assert inflight["event"]["status"] == "error" and inflight["state_index"] == 1
    assert inflight["event"]["upper_work"]["J"] == dict(attempted=1600, completed=1600)
    assert (directory / "attempt-01.json").exists() and not (directory / "raw-01.json").exists()
    assert not (directory / "worker.json").exists()


def test_late_complete_raw_work_does_not_replace_checkpoint(monkeypatch, tmp_path):
    directory = tmp_path / "worker"

    def deadline(started):
        if (directory / "raw-01.json").exists():
            raise TimeoutError("injected late state")
        return 0.1

    monkeypatch.setattr(runner.legacy, "deadline", deadline)
    assert run_fake_worker(monkeypatch, directory) == 1
    assert len(runner.read(directory / "checkpoint.json")["rows"]) == 1
    assert (directory / "raw-01.json").exists() and (directory / "raw-01.npz").exists()
    assert not (directory / "worker.json").exists()
    error = runner.read(directory / "worker-error.json")
    assert error["error_type"] == "TimeoutError"
    assert error["kernel_work"] == runner.expected_kernel_work(runner.matrix()[0], 2)


def test_live_parent_loss_during_phase_stops_more_kernels_and_preserves_checkpoint(
    monkeypatch, tmp_path
):
    actual_parent, lost = os.getppid(), []
    original = runner.ProgressLog.__call__

    def lose_parent_after_one_curve_in_second_state(self, event):
        original(self, event)
        if self.state_index == 1 and event["curve_index"] == 0 and event["status"] == "completed":
            lost.append(True)

    monkeypatch.setattr(runner.ProgressLog, "__call__", lose_parent_after_one_curve_in_second_state)
    monkeypatch.setattr(runner.os, "getppid", lambda: actual_parent + 1 if lost else actual_parent)
    directory = tmp_path / "worker"
    assert run_fake_worker(monkeypatch, directory) == 1
    assert len(runner.read(directory / "checkpoint.json")["rows"]) == 1
    error = runner.read(directory / "worker-error.json")
    assert error["error_type"] == "RuntimeError" and "parent changed" in error["error"]
    assert error["kernel_work"]["J"] == dict(attempted=1600, completed=1600)
    assert not (directory / "raw-01.json").exists()


def test_append_history_keeps_reservation_when_atomic_inflight_save_fails(monkeypatch, tmp_path):
    progress = runner.ProgressLog(tmp_path)
    monkeypatch.setattr(runner, "save", lambda *args: (_ for _ in ()).throw(OSError("injected IO")))
    with pytest.raises(OSError):
        progress(dict(status="reserved", work=runner.zero_kernel_work()))
    assert len(progress.history.read_text().splitlines()) == 1
    assert not progress.inflight.exists()


def test_all_four_failed_processes_preserved_with_per_cell_reserve(monkeypatch, tmp_path):
    reserves, launches = [], []
    source = dict(matrix=runner.matrix(), old_reference={"unit_test_only": True})
    monkeypatch.setattr(runner, "sources", lambda root: source)
    monkeypatch.setattr(
        runner,
        "space_check",
        lambda path, reserve: reserves.append(reserve) or dict(free_bytes=4 * runner.GIB),
    )
    monkeypatch.setattr(
        runner,
        "run_process",
        lambda command, **kwargs: (
            launches.append(command) or dict(returncode=1, timed_out=False, elapsed_seconds=0.1)
        ),
    )
    result = runner.qualify(tmp_path / "run")
    assert len(launches) == len(result["rows"]) == 4
    assert reserves == [3 * runner.GIB] * 5
    assert result["bounded_reference_pass"] is result["independent_audit_pass"] is False
    assert result["all_pass"] is result["producer_checks_pass"] is False
    assert result["admission_status"] == "pending-independent-audit"
    for reference in result["rows"]:
        row = runner.read(runner.checked(reference))
        assert row["status"] == "failed"
        assert all(runner.checked(row[key]).exists() for key in ("config", "launch", "process"))


def test_source_mutation_prevents_even_mock_native_start(monkeypatch, tmp_path):
    directory = tmp_path / "worker"
    directory.mkdir()
    source = dict(matrix=runner.matrix(), original=True)
    runner.save(
        directory / "config.json",
        dict(
            case=runner.matrix()[0],
            output=str(directory),
            parent_pid=os.getppid(),
            started_monotonic=runner.time.monotonic(),
            source=source,
        ),
    )
    monkeypatch.setattr(runner, "sources", lambda root: dict(source, original=False))
    monkeypatch.setattr(
        runner, "make_model", lambda *args: pytest.fail("must not start native model")
    )
    for name in runner.THREADS:
        monkeypatch.setenv(name, "1")
    assert runner.worker(directory / "config.json") == 1
    assert runner.read(directory / "worker-error.json")["error_type"] == "ValueError"
    assert not (directory / "model-attempt.json").exists()


def test_parent_guards_preserve_legacy_strict_types_and_additional_scope():
    source, case = {}, runner.matrix()[0]
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
    runner.completed_worker(process, document, case, source, 10.0)
    with pytest.raises(ValueError):
        runner.completed_worker(dict(process, returncode=False), document, case, source, 10.0)
    with pytest.raises(ValueError):
        runner.completed_worker(
            process, dict(document, scope=dict(runner.SCOPE, startup_pass=True)), case, source, 10.0
        )


def test_fresh_output_and_terminal_failure_never_replace_checkpoint(monkeypatch, tmp_path):
    def fail(output):
        runner.save(output / "checkpoint.json", dict(rows=["last-success"]))
        raise OSError("injected IO")

    monkeypatch.setattr(runner, "_qualify", fail)
    directory = tmp_path / "run"
    with pytest.raises(OSError):
        runner.qualify(directory)
    old = (directory / "checkpoint.json").read_bytes()
    assert (directory / "terminal-error.json").exists()
    with pytest.raises(FileExistsError):
        runner.qualify(directory)
    assert (directory / "checkpoint.json").read_bytes() == old
    with pytest.raises(ValueError):
        runner.qualify(Path("relative"))


def test_successful_producer_cli_does_not_claim_independent_admission(
    monkeypatch, tmp_path, capsys
):
    result = dict(status="completed", producer_checks_pass=True, bounded_reference_pass=False)
    runner.save(tmp_path / "run.json", result)
    monkeypatch.setattr(runner, "qualify", lambda output: result)
    monkeypatch.setattr(runner.sys, "argv", ["runner", "--raw", str(tmp_path)])
    assert runner.main() == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["producer_checks_pass"] is True
    assert printed["bounded_reference_pass"] is False
