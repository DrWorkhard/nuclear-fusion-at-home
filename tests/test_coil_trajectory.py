"""Portable controls for record fidelity, identity and failure preservation."""

import hashlib
import json
import time
from pathlib import Path

import pytest

from fusion_baselines.coil_trajectory import export


def save(run, name, value):
    (run/name).write_text(json.dumps(value, allow_nan=False), encoding="utf-8")


@pytest.fixture
def run(tmp_path):
    root = tmp_path/"run"
    root.mkdir()
    names = [f"coil[{i}]/{axis}{kind}({mode})" for i in range(6) for axis in "xyz"
             for kind, mode in [("c", 0)]+[(k, m) for m in range(1, 6) for k in "sc"]]
    save(root, "seed.json", dict(nbase=6, nfp=2, order=5, names=names,
                                base_coefficients=[[[0.]*11 for _ in range(3)] for _ in range(6)],
                                target_id="synthetic", target_flux=-.01, B2_scale=1.))
    save(root, "inputs.json", dict(kind="normalized-coil-fit", provenance=dict(
        repository=dict(commit="a"*40, dirty=False, path="/private/producer"),
        host=dict(python="synthetic", python_executable="/private/python")),
        sources_before={"/private/code.py": "b"*64}, solver_options=dict(ftol=0.)))
    for index, status in enumerate(("completed", "failed", "attempted")):
        row = dict(index=index, role="search", x=[float(index)]*198, status="attempted")
        save(root, f"trial-{index:05}-attempt.json", row)
        if status == "attempted":
            continue
        row["status"] = status
        if status == "completed":
            row.update(value=1., gradient=[0.]*198, metrics=dict(normal_rms=.2, lengths=[3.]*6))
        else:
            row.update(error="ValueError: invalid flux", rejected_value=2.)
        save(root, f"trial-{index:05}.json", row)
    return root


def read(output):
    return [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]


def test_complete_failed_and_incomplete_records_are_not_acceptance(run, tmp_path):
    output = tmp_path/"records.jsonl"
    summary = export(run, output, "https://example.invalid/immutable/run")
    header, complete, failed, incomplete, footer = read(output)
    assert summary["counts"] == dict(completed=1, failed=1, incomplete=1)
    assert complete["metrics"]["normal_rms"] == .2
    assert complete["selected"] is None  # No search summary: selection is unknown.
    assert failed["metrics"] is None and failed["objective"] is None
    assert failed["error"] == "ValueError: invalid flux" and failed["rejection_value"] == 2.
    assert incomplete["evaluation_status"] == "incomplete" and incomplete["gradient"] is None
    assert all(row["solver_step_status"] == "unknown" for row in (complete, failed, incomplete))
    assert header["producer"]["commit"] == "a"*40 and header["coefficient_unit"] == "m"
    assert header["search_resolution"] is None
    assert footer["artifacts"]["seed.json"]["uri"].endswith("/seed.json")
    assert "/private/" not in output.read_text(encoding="utf-8")
    assert footer["type"] == "export_complete" and not footer["physical_admission"]


def test_historical_v1_export_bytes_match_pre_recording_exporter(run, tmp_path):
    # Captured from the ce5794f exporter on this fixture, without an artifact base.
    output = tmp_path/'historical.jsonl'
    export(run, output)
    assert hashlib.sha256(output.read_bytes()).hexdigest() == (
        '41a142f21f7f6ffc3dfaccab0bda759cf053ac5b42080ac2cf09b8559397baee')


def test_stable_identity_is_independent_of_output_and_artifact_location(run, tmp_path):
    left, right = tmp_path/"left.jsonl", tmp_path/"right.jsonl"
    export(run, left)
    export(run, right, "https://example.invalid/other")
    assert read(left)[0]["run_id"] == read(right)[0]["run_id"]
    assert read(left)[1]["candidate_id"] == read(right)[1]["candidate_id"]
    assert read(left)[1]["candidate_id"] != read(left)[2]["candidate_id"]
    attempt = json.loads((run/"trial-00002-attempt.json").read_text(encoding="utf-8"))
    attempt["x"][0] = 99.
    save(run, "trial-00002-attempt.json", attempt)
    changed = tmp_path/"changed.jsonl"
    export(run, changed)
    assert read(left)[0]["run_id"] != read(changed)[0]["run_id"]


def test_verification_stays_separate_and_selected_identity_is_checked(run, tmp_path):
    selected = json.loads((run/"trial-00000.json").read_text(encoding="utf-8"))
    search = dict(selected=selected, status=dict(reason="budget"))
    save(run, "search.json", search)
    save(run, "result.json", dict(search=search, completed=True, physical_admission=False,
                                  fine=[dict(n=128, nodes=512, metrics=dict(normal_rms=.3))]))
    output = tmp_path/"records.jsonl"
    export(run, output)
    rows = read(output)
    assert rows[1]["selected"] and rows[1]["metrics"]["normal_rms"] == .2
    assert rows[-2]["type"] == "verification"
    assert rows[-2]["recorded"]["fine"][0]["metrics"]["normal_rms"] == .3
    assert rows[1]["verification_status"] == "not_evaluated"
    selected["x"][0] = 99.
    save(run, "search.json", search)
    save(run, "result.json", dict(search=search))
    with pytest.raises(ValueError, match="selected candidate"):
        export(run, tmp_path/"bad.jsonl")


@pytest.mark.parametrize("change", ["names", "length", "gradient", "attempt", "status"])
def test_malformed_identity_and_missing_completed_values_fail_closed(run, tmp_path, change):
    name = "seed.json" if change == "names" else "trial-00000.json"
    row = json.loads((run/name).read_text(encoding="utf-8"))
    if change == "names":
        row["names"].reverse()
    elif change == "length":
        row["x"].pop()
    elif change == "gradient":
        row.pop("gradient")
    elif change == "attempt":
        row["x"][0] = .1
    else:
        row["status"] = "accepted"
    save(run, name, row)
    with pytest.raises(ValueError):
        export(run, tmp_path/"bad.jsonl")


def test_output_ceiling_retains_partial_and_never_publishes_complete(run, tmp_path):
    output = tmp_path/"records.jsonl"
    with pytest.raises(ValueError, match="ceiling"):
        export(run, output, max_bytes=1)
    assert not output.exists() and Path(str(output)+".partial").exists()
    with pytest.raises(FileExistsError):
        export(run, output)


def test_existing_output_and_symlink_inputs_are_not_overwritten_or_followed(run, tmp_path):
    output = tmp_path/"records.jsonl"
    output.write_text("preserved", encoding="utf-8")
    with pytest.raises(ValueError, match="fresh"):
        export(run, output)
    assert output.read_text(encoding="utf-8") == "preserved"
    original = run/"trial-00000.json"
    original.rename(run/"hidden.json")
    original.symlink_to(run/"hidden.json")
    with pytest.raises(ValueError, match="regular"):
        export(run, tmp_path/"symlink.jsonl")


def test_order_eight_names_and_gradients_are_preserved(run, tmp_path):
    seed = json.loads((run/"seed.json").read_text(encoding="utf-8"))
    seed.update(order=8, names=[f"coil[{i}]/{axis}{kind}({mode})"
        for i in range(6) for axis in "xyz"
        for kind, mode in [("c", 0)]+[(k, m) for m in range(1, 9) for k in "sc"]],
        base_coefficients=[[[0.]*17 for _ in range(3)] for _ in range(6)])
    save(run, "seed.json", seed)
    for path in run.glob("trial-*.json"):
        row = json.loads(path.read_text(encoding="utf-8"))
        row["x"] = [float(row["index"])]*306
        if "gradient" in row:
            row["gradient"] = [0.]*306
        save(run, path.name, row)
    output = tmp_path/"order8.jsonl"
    export(run, output)
    assert len(read(output)[0]["coefficient_names"]) == 306
    assert len(read(output)[1]["gradient"]) == 306


def test_tiny_new_search_uses_existing_recorder_without_native_calls(run, tmp_path):
    np = pytest.importorskip("numpy")
    from fusion_baselines.coil_fit import Recorder, search

    class Model:
        x0 = np.zeros(198)

        def set_x(self, x):
            self.x = x.copy()

        def evaluate(self, x):
            self.set_x(x)
            if x[0] > .5:
                raise ValueError("synthetic invalid trial")
            return float(1+x.sum()+.5*x@x), 1+x, dict(
                normal_rms=float(1+x.sum()), lengths=[3.]*6,
                sampled_geometry_limits_met=True, current_limit_met=True)

    def minimize(function, x, **kwargs):
        from types import SimpleNamespace

        function(np.ones_like(x))
        function(x-.001)
        return SimpleNamespace(success=True, message="synthetic control")

    recorded = tmp_path/"recorded"
    report = search(Model(), Recorder(recorded, time.monotonic()+5), minimize)
    for name in ("seed.json", "inputs.json"):
        (recorded/name).write_bytes((run/name).read_bytes())
    save(recorded, "search.json", report)
    # A deliberately retained interrupted attempt, separate from the finished search.
    save(recorded, "trial-00012-attempt.json", dict(
        index=12, role="search", status="attempted", x=[0.]*198))
    output = tmp_path/"control.jsonl"
    result = export(recorded, output)
    assert result["counts"] == dict(completed=11, failed=1, incomplete=1)
    rows = read(output)
    assert rows[11]["error"] == "ValueError: synthetic invalid trial"
    assert rows[12]["selected"] and rows[13]["evaluation_status"] == "incomplete"


def prospective(run):
    """A minimal prospective record, including a known zero cost (not missing)."""
    inputs = json.loads((run/'inputs.json').read_text(encoding='utf-8'))
    inputs['recording'] = dict(format='fusion-coil-recording-v2', task_id='controlled-example',
                               objective_weights=dict(flux_per_area=1.))
    save(run, 'inputs.json', inputs)
    row = json.loads((run/'trial-00000.json').read_text(encoding='utf-8'))
    row.update(elapsed_s=0., elapsed_scope='controlled clock')
    save(run, 'trial-00000.json', row)
    save(run, 'iterate-00000.json', dict(format='fusion-coil-recording-v2', iteration=0,
        evaluation_index=0, x=row['x'], link_status='exact_latest_evaluation',
        solver_step_status='accepted', physical_admission=False))


def test_v2_links_callbacks_costs_and_settings_without_backfilling(run, tmp_path):
    prospective(run)
    output = tmp_path/'v2.jsonl'
    before = {p.name: p.read_bytes() for p in run.iterdir()}
    export(run, output)
    header, completed, failed, incomplete, step, footer = read(output)
    assert all(row['format'] == 'fusion-coil-trajectory-v2' for row in read(output))
    assert header['task_id'] == 'controlled-example'
    assert header['objective_weights'] == dict(flux_per_area=1.)
    assert completed['solver_step_status'] == 'accepted' and completed['elapsed_s'] == 0.
    assert step['candidate_id'] == completed['candidate_id'] and step['evaluation_index'] == 0
    assert failed['solver_step_status'] == incomplete['solver_step_status'] == 'unknown'
    assert failed['elapsed_s'] is None and incomplete['elapsed_s'] is None
    assert completed['elapsed_scope'] == 'controlled clock' and completed['selected'] is None
    assert footer['artifacts']['iterate-00000.json']['sha256']
    assert before == {p.name: p.read_bytes() for p in run.iterdir()}


@pytest.mark.parametrize('fault', ['coordinates', 'index', 'probe', 'version', 'count', 'gap',
                                  'negative_cost', 'missing_scope', 'link_status'])
def test_v2_rejects_inconsistent_solver_links_and_costs(run, tmp_path, fault):
    prospective(run)
    name = 'iterate-00000.json'
    step = json.loads((run/name).read_text(encoding='utf-8'))
    if fault == 'coordinates':
        step['x'][0] = 99.
    elif fault == 'index':
        step['evaluation_index'] = 2  # An attempt-only trial is not a returned evaluation.
    elif fault == 'version':
        step['format'] = 'unknown'
    elif fault == 'link_status':
        step['link_status'] = 'unknown'
    elif fault == 'gap':
        step['iteration'] = 2
    elif fault == 'count':
        save(run, 'search.json', dict(recording_format='fusion-coil-recording-v2',
                                     solver_iterations_recorded=2))
    else:
        row = json.loads((run/'trial-00000.json').read_text(encoding='utf-8'))
        if fault == 'probe':
            row['role'] = 'probe'
        elif fault == 'negative_cost':
            row['elapsed_s'] = -1.
        else:
            row.pop('elapsed_scope')
        save(run, 'trial-00000.json', row)
    save(run, name, step)
    with pytest.raises((ValueError, OSError)):
        export(run, tmp_path/'invalid.jsonl')


def test_v2_unlinked_callback_does_not_invent_candidate_identity(run, tmp_path):
    prospective(run)
    step = json.loads((run/'iterate-00000.json').read_text(encoding='utf-8'))
    step.update(evaluation_index=None, link_status='unknown')
    save(run, 'iterate-00000.json', step)
    output = tmp_path/'unknown.jsonl'
    export(run, output)
    rows = read(output)
    assert rows[1]['solver_step_status'] == 'unknown'
    assert rows[-2]['solver_step_status'] == 'accepted' and rows[-2]['candidate_id'] is None


def test_prospective_control_records_real_interruption_after_callback(run, tmp_path):
    np = pytest.importorskip('numpy')
    from fusion_baselines.coil_fit import Recorder, recording_settings, search

    class Model:
        x0 = np.zeros(198)

        def set_x(self, x):
            pass

        def evaluate(self, x):
            if x[0] == 1.:
                raise ValueError('controlled failed trial')
            if x[0] == 2.:
                raise KeyboardInterrupt
            return float(1+x.sum()+.5*x@x), 1+x, dict(
                normal_rms=float(1+x.sum()), lengths=[3.]*6,
                sampled_geometry_limits_met=True, current_limit_met=True)

    def minimize(function, x, callback, **kwargs):
        function(x-.001)
        callback(x-.001)
        function(np.ones_like(x))
        function(np.full_like(x, 2.))

    recorded = tmp_path/'prospective-control'
    recorder = Recorder(recorded, time.monotonic()+10)
    recorder.save('seed.json', (run/'seed.json').read_bytes())
    # The settings describe the control honestly; it has no native field grid or equilibrium.
    settings = recording_settings('synthetic-recording-control')
    settings.update(objective_weights=None, constraints=None, search_resolution=None,
                    current_convention=None, target_policy='synthetic fixed seed')
    recorder.save('inputs.json', dict(kind='normalized-coil-fit', recording=settings))
    with pytest.raises(KeyboardInterrupt):
        search(Model(), recorder, minimize)
    output = tmp_path/'prospective-control-v2.jsonl'
    result = export(recorded, output)
    rows = read(output)
    assert result['counts'] == dict(completed=11, failed=1, incomplete=1)
    accepted, failed, interrupted, step = rows[11:15]
    assert accepted['solver_step_status'] == 'accepted'
    assert accepted['candidate_id'] == step['candidate_id']
    assert failed['error'] == 'ValueError: controlled failed trial'
    assert failed['elapsed_s'] >= 0 and failed['metrics'] is None
    assert interrupted['evaluation_status'] == 'incomplete' and interrupted['elapsed_s'] is None
    assert all(row['selected'] is None for row in rows if row['type'] == 'evaluation')


def test_native_fixed_target_candidate_replays_from_recorded_inputs(tmp_path, monkeypatch):
    np = pytest.importorskip('numpy')
    pytest.importorskip('simsopt')
    from scipy.optimize import minimize

    from fusion_baselines import coil_check, coil_fit
    from fusion_baselines.provenance import build_run_record

    root = Path(__file__).resolve().parents[1]
    input_path = root/coil_check.TARGET
    candidate_path = root/'submissions/length-headroom-six-coil/candidate.json'
    data = json.loads(input_path.read_text(encoding='utf-8'))
    candidate = json.loads(candidate_path.read_text(encoding='utf-8'))
    seed = coil_check.candidate_snapshot(candidate, data)
    # A single native optimizer iteration is a recording/replay control, not a new fit study.
    monkeypatch.setattr(coil_fit, 'SOLVER_OPTIONS', dict(coil_fit.SOLVER_OPTIONS, maxiter=1))
    recorder = coil_fit.Recorder(tmp_path/'native-control', time.monotonic()+60)
    recorder.save('seed.json', seed)
    sources = [input_path, candidate_path, Path(coil_fit.__file__), Path(coil_check.__file__)]
    recorder.save('inputs.json', dict(kind='normalized-coil-fit',
        recording=coil_fit.recording_settings('native-fixed-target-recording-control'),
        solver_options=coil_fit.SOLVER_OPTIONS, search_seconds=60, check_seconds=None,
        provenance=build_run_record(root),
        sources_before={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    result = coil_fit.search(coil_fit.Model(seed, data, recorder), recorder, minimize)
    recorder.save('search.json', result)
    assert result['startup_pass'] and result['status']['reason'] == 'solver-return'
    assert result['solver_iterations_recorded'] == 1
    output = tmp_path/'native-control-v2.jsonl'
    export(recorder.output, output)
    rows = read(output)
    selected = next(row for row in rows if row['type'] == 'evaluation' and row['selected'])
    # New model and seed loaded from disk, using only committed target/candidate inputs.
    saved_seed = json.loads((recorder.output/'seed.json').read_text(encoding='utf-8'))
    replay = coil_fit.Model(saved_seed, data, recorder)
    value, gradient, metrics = replay.evaluate(np.asarray(selected['coefficients']))
    assert value == selected['objective'] and metrics == selected['metrics']
    np.testing.assert_array_equal(gradient, selected['gradient'])
    step = next(row for row in rows if row['type'] == 'solver_iterate')
    assert step['candidate_id'] in {row['candidate_id'] for row in rows
                                  if row['type'] == 'evaluation'}
