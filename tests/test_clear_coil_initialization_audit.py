"""Fail-closed whole-study accounting and selection, without target evaluations."""

import copy
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_clear_coil_initialization as audit
from current_diagnostic_inputs import reference


def write(path, document):
    path.write_text(json.dumps(document, allow_nan=False))
    return reference(path)


def basic_run():
    binding = dict(
        matrix=audit.independent.cases(),
        solver_configuration=dict(
            method="highs-ds",
            options=dict(
                time_limit=30.0,
                primal_feasibility_tolerance=1e-10,
                dual_feasibility_tolerance=1e-10,
                threads=1,
                parallel=False,
            ),
        ),
    )
    return dict(
        schema_version=1,
        phase="geometry_initialization",
        status="completed",
        source=binding,
        case_matrix=copy.deepcopy(binding["matrix"]),
        threads={
            k: "1" for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")
        },
        geometry_pass=False,
        selected=None,
        **audit.SCOPE,
    ), binding


def test_exact_registered_common_source_scope():
    run, binding = basic_run()
    audit.common(run, binding)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r.update(status="incomplete"),
        lambda r: r.update(schema_version=True),
        lambda r: r.update(phase="field_fit"),
        lambda r: r.update(field_calls=1),
        lambda r: r.update(field_calls=False),
        lambda r: r.update(gradient_calls=1),
        lambda r: r.update(equilibrium_solves=1),
        lambda r: r.update(field_pass=True),
        lambda r: r.update(transfer_pass=True),
        lambda r: r.update(step4_pass=True),
        lambda r: r.update(geometry_pass=True),
        lambda r: r.update(selected="pretend"),
        lambda r: r["threads"].update(OMP_NUM_THREADS="2"),
        lambda r: r["case_matrix"].pop(),
    ],
)
def test_common_rejects_unauthorized_work_or_producer_admission(mutation):
    run, binding = basic_run()
    mutation(run)
    with pytest.raises((ValueError, KeyError)):
        audit.common(run, binding)


def test_selection_needs_full_geometry_admission_then_fixed_ties():
    case = audit.independent.cases()
    rows = [dict(case=c, geometry_pass=False, sum_base_lengths=0.1) for c in case]
    assert audit.selected_sets(rows) == dict(n6=None, n8=None)
    for row in rows:
        row.update(geometry_pass=True, sum_base_lengths=20.0)
    assert audit.selected_sets(rows) == dict(n6="n6-circle-d100mm", n8="n8-circle-d100mm")
    rows[3]["sum_base_lengths"] = 19.0
    assert audit.selected_sets(rows)["n6"] == "n6-shape-d100mm"
    rows[3]["geometry_pass"] = False
    assert audit.selected_sets(rows)["n6"] == "n6-circle-d100mm"


def test_arrays_and_metadata_cannot_shadow_each_other(tmp_path):
    meta = write(tmp_path / "metadata.json", dict(value=2))
    path = tmp_path / "arrays.npz"
    with path.open("xb") as stream:
        np.savez_compressed(stream, value=np.array([3.0]))
    with pytest.raises(ValueError):
        audit.split(dict(metadata=meta, arrays=reference(path)))


def test_source_and_array_hashes_are_checked_before_use(tmp_path):
    path = tmp_path / "state.json"
    ref = write(path, dict(state=1))
    audit.bind_tree(dict(nested=[ref, ref]))
    path.write_text(json.dumps(dict(state=2)))
    with pytest.raises(ValueError):
        audit.bind_tree(dict(nested=[ref]))


def test_raw_reconstruction_rejects_masks_dtype_keys_and_absolute_error():
    expected = dict(ids=np.array([0, 2], dtype=int), cover=0.1, full_torus=True)
    audit.compare_tree(expected, expected, "control")
    for altered in (
        dict(expected, ids=np.array([0, 3])),
        dict(expected, cover=0.100000001),
        dict(expected, full_torus=1),
        dict(expected, hidden=0),
    ):
        with pytest.raises(ValueError):
            audit.compare_tree(altered, expected, "mutation")


def work_run(tmp_path):
    run, _ = basic_run()
    start, stop = 100.0, 500.0
    config = write(
        tmp_path / "config.json",
        dict(start_monotonic=start, source=run["source"], threads=run["threads"]),
    )
    run["terminal"] = dict(
        reason="matrix_complete",
        all_registered_attempts=True,
        parent_stop_monotonic=stop,
        process=dict(returncode=0),
    )
    terminal = write(tmp_path / "terminal.json", run["terminal"])
    run["execution_artifacts"] = {"config.json": config, "terminal.json": terminal}
    run["clock"] = dict(
        start_monotonic=start,
        parent_stop_monotonic=stop,
        timeout_seconds=1800,
        lp_timeout_seconds=30,
        check_interval=0.5,
        termination_grace_seconds=5,
    )
    run["attempts"] = []
    for case in audit.independent.cases():
        for base in range(case["nbase"]):
            for repeat in (False, True):
                i = len(run["attempts"])
                row = dict(
                    index=i,
                    case=case["label"],
                    base_index=base,
                    repeat=repeat,
                    problem={},
                    status="attempted",
                    started_monotonic=101.0 + 2 * i,
                )
                attempt = write(tmp_path / f"attempt-{i}.json", row)
                row = dict(
                    row, status="completed", completed_monotonic=102.0 + 2 * i, elapsed_seconds=1.0
                )
                outcome = write(tmp_path / f"outcome-{i}.json", row)
                run["attempts"].append(dict(row, attempt=attempt, outcome=outcome))
    run["attempted_lps"] = 168
    return run


def test_complete_84_plus_84_ordered_wall_guarded_ledger(tmp_path):
    report = audit.work_audit(work_run(tmp_path))
    assert report["attempted_lps"] == 168 and report["original_lps"] == report["repeated_lps"] == 84
    assert report["field_calls"] == report["gradient_calls"] == report["equilibrium_solves"] == 0


@pytest.mark.parametrize("returncode", [None, False, True, 1, -9, 0.0, "0"])
def test_completed_matrix_requires_exact_zero_process_exit(tmp_path, returncode):
    run = work_run(tmp_path)
    run["terminal"]["process"]["returncode"] = returncode
    run["execution_artifacts"]["terminal.json"] = write(tmp_path / "terminal.json", run["terminal"])
    with pytest.raises(ValueError, match="parent-guarded"):
        audit.work_audit(run)


@pytest.mark.parametrize(
    "mutation", ["none", "missing", "wrong_error", "early", "late", "elapsed", "over_budget"]
)
def test_failed_attempt_has_bound_exception_and_no_time_budget_waiver(tmp_path, mutation):
    run = work_run(tmp_path)
    row = run["attempts"][0]
    row.pop("completed_monotonic")
    row.update(status="failed", failed_end_monotonic=102.0, error="ValueError: synthetic")
    failure = dict(error=row["error"], raised_monotonic=101.5)
    if mutation == "wrong_error":
        failure["error"] = "ValueError: changed"
    if mutation == "early":
        failure["raised_monotonic"] = 100.9
    if mutation == "late":
        failure["raised_monotonic"] = 102.1
    if mutation == "elapsed":
        row["elapsed_seconds"] = 0.5
    if mutation == "over_budget":
        row.update(failed_end_monotonic=132.0, elapsed_seconds=31.0)
    if mutation != "missing":
        row["failure"] = write(tmp_path / "original-failure.json", failure)
    row["outcome"] = write(
        tmp_path / "outcome-0.json",
        {k: v for k, v in row.items() if k not in ("attempt", "outcome")},
    )
    if mutation == "none":
        assert audit.work_audit(run)["attempted_lps"] == 168
    else:
        with pytest.raises((ValueError, KeyError)):
            audit.work_audit(run)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r["attempts"].pop(),
        lambda r: r.update(attempted_lps=167),
        lambda r: r["attempts"][1].update(repeat=False),
        lambda r: r["attempts"][1].update(repeat=1),
        lambda r: r["attempts"][1].update(base_index=5),
        lambda r: r["attempts"][1].update(index=2),
        lambda r: r["attempts"][1].update(elapsed_seconds=31),
        lambda r: r["clock"].update(timeout_seconds=1900),
        lambda r: r["clock"].update(lp_timeout_seconds=31),
        lambda r: r["clock"].update(check_interval=1),
        lambda r: r["clock"].update(parent_stop_monotonic=2000),
    ],
)
def test_accounting_clock_or_identity_mutation_is_not_admitted(tmp_path, mutation):
    run = work_run(tmp_path)
    mutation(run)
    with pytest.raises((ValueError, KeyError)):
        audit.work_audit(run)


def test_primal_dual_repeat_is_exact_not_allclose():
    solution = dict(
        success=True,
        status=0,
        objective=1.0,
        method="highs-ds",
        options={},
        warnings=[],
        x=[1.0],
        slack=[0.0],
        inequality_marginals=[-1.0],
        lower_marginals=[0.0],
        upper_marginals=[0.0],
    )
    other = copy.deepcopy(solution)
    assert audit.exact_repeat(solution, other)
    other["x"][0] += 1e-15
    assert not audit.exact_repeat(solution, other)


def test_full_native_synthetic_worker_to_persisted_independent_cli(tmp_path, monkeypatch):
    """All12 cases/168 real LPs; only sources are synthetic, no project inputs."""
    import run_clear_coil_initialization as runner

    for name in runner.THREADS:
        monkeypatch.setenv(name, "1")
    run, binding = basic_run()
    targets = {}
    for label, rminor in (("reference", 0.035), ("selected", 0.03502)):
        data = dict(
            nfp=2,
            lasym=False,
            mpol=2,
            ntor=0,
            rbc=[dict(m=0, n=0, value=1.0), dict(m=1, n=0, value=rminor)],
            zbs=[dict(m=1, n=0, value=rminor)],
        )
        input_ref = write(tmp_path / f"synthetic-{label}.json", data)
        fake_wout = write(
            tmp_path / f"synthetic-{label}-not-a-wout.json", dict(synthetic_only=True)
        )
        targets[label] = dict(input=input_ref, wout=fake_wout)
    binding["targets"] = targets
    monkeypatch.setattr(runner, "sources", lambda root: binding)
    monkeypatch.setattr(audit, "sources", lambda root: binding)
    raw = tmp_path / "run"
    raw.mkdir()
    for name in ("surfaces", "sets", "attempts", "outcomes"):
        (raw / name).mkdir()
    start = time.monotonic()
    config = dict(
        schema_version=1,
        phase="geometry_initialization",
        source=binding,
        threads=run["threads"],
        parent_pid=os.getppid(),
        start_monotonic=start,
        **audit.SCOPE,
    )
    config_path = raw / "config.json"
    write(config_path, config)
    runner.worker(config_path)
    terminal_path = raw / "worker-terminal.json"
    terminal = json.loads(terminal_path.read_text())
    assert terminal["reason"] == "matrix_complete" and terminal["all_registered_attempts"] is True
    # Worker is invoked inline here; subprocess exit/kill behavior is separately
    # tested by the parent-guard tests in test_clear_coil_initialization_workflow.
    terminal["process"] = dict(returncode=0, synthetic_inline_worker=True)
    terminal["parent_stop_monotonic"] = time.monotonic()
    final_terminal = write(raw / "terminal.json", terminal)
    checkpoint = raw / "completed-checkpoint.json"
    state = json.loads(checkpoint.read_text())
    run.update(
        state,
        status="completed",
        threads=config["threads"],
        attempts=runner.collected_attempts(raw),
        attempted_lps=168,
        case_matrix=binding["matrix"],
        terminal=terminal,
        clock=dict(
            start_monotonic=start,
            parent_stop_monotonic=terminal["parent_stop_monotonic"],
            timeout_seconds=1800,
            lp_timeout_seconds=30,
            check_interval=0.5,
            termination_grace_seconds=5,
        ),
        execution_artifacts={
            "config.json": reference(config_path),
            "terminal.json": final_terminal,
            "completed-checkpoint.json": reference(checkpoint),
        },
    )
    run_path, output = raw / "run.json", tmp_path / "audit.json"
    write(run_path, run)
    monkeypatch.setattr(
        sys,
        "argv",
        ["audit_clear_coil_initialization.py", "--run", str(run_path), "--output", str(output)],
    )
    code = audit.main()
    result = json.loads(output.read_text())
    assert result["status"] == "completed", result.get("error")
    assert result["arithmetic_and_source_pass"] and result["all_twelve_sets_checked"]
    assert code == 0 and result["geometry_pass"] and result["both_classes_pass"]
    assert len(result["sets"]) == 12 and all(len(r["distances"]) == 6 for r in result["sets"])
    assert all(len(r["coils"]) == r["case"]["nbase"] for r in result["sets"])
    assert (
        result["field_pass"] is False
        and result["transfer_pass"] is False
        and result["step4_pass"] is False
    )
