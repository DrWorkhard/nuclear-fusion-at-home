"""Budget, process cleanup and provenance-boundary counterexamples; no VMEC solves."""
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from fusion_baselines import joint_equilibrium as solver


def test_both_clocks_and_clock_disagreement_control_eligibility(tmp_path, monkeypatch):
    monkeypatch.setattr(solver.time, 'monotonic', lambda: 100.)
    monkeypatch.setattr(solver.time, 'time', lambda: 1000.)
    assert solver.stop_reason(tmp_path, 101., 1001.) is None
    assert solver.stop_reason(tmp_path, 100., 1000.) == 'deadline'
    assert solver.stop_reason(tmp_path, 104., 999.) == 'deadline'
    assert solver.stop_reason(tmp_path, 200., 1200.) == 'clock disagreement'
    with pytest.raises(ValueError, match='finite'):
        solver.stop_reason(tmp_path, float('nan'), 1200.)


def test_shared_sibling_outputs_count_against_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(solver, 'MAX_BYTES', 32)
    monkeypatch.setattr(solver, 'REPORT_RESERVE', 8)
    (tmp_path/'other-proposal').mkdir()
    (tmp_path/'other-proposal'/'output').write_bytes(b'x'*25)
    assert solver.stop_reason(tmp_path, time.monotonic()+10, time.time()+10) == (
        'aggregate storage ceiling')


def test_zero_exit_is_rejected_after_deadline(tmp_path):
    folder = tmp_path/'cell'
    folder.mkdir()
    record = solver.supervise([sys.executable, '-I', '-c', 'import time; time.sleep(5)'],
        folder, tmp_path, time.monotonic()+.15, time.time()+.15)
    assert not record['completed'] and record['stop_reason'] == 'deadline'
    assert (folder/'solver.log').exists()


def test_success_is_serial_and_has_minimal_environment(tmp_path, monkeypatch):
    monkeypatch.setenv('FUSION_TEST_SECRET', 'not-for-child')
    folder = tmp_path/'cell'
    folder.mkdir()
    command = [sys.executable, '-I', '-c',
        "import os; assert 'FUSION_TEST_SECRET' not in os.environ; "
        "assert os.environ['OMP_NUM_THREADS']=='1'; print('finished')"]
    record = solver.supervise(command, folder, tmp_path,
                               time.monotonic()+5, time.time()+5)
    assert record['completed'] and record['returncode'] == 0
    assert (folder/'solver.log').read_text().strip() == 'finished'


def test_descendant_is_killed_even_after_leader_exits(tmp_path):
    folder = tmp_path/'cell'
    folder.mkdir()
    code = ("import subprocess,sys; p=subprocess.Popen([sys.executable,'-I','-c',"
            "'import time; time.sleep(30)']); print(p.pid,flush=True)")
    record = solver.supervise([sys.executable, '-I', '-c', code], folder, tmp_path,
                              time.monotonic()+5, time.time()+5)
    assert record['completed']
    pid = int((folder/'solver.log').read_text())
    # Allow the host init process to reap the orphan; no unrestricted process scan.
    for _ in range(50):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            break
        time.sleep(.02)
    else:
        pytest.fail('descendant still exists after process-group cleanup')


def test_cleanup_failure_is_not_reported_as_success(tmp_path, monkeypatch):
    folder = tmp_path/'cell'
    folder.mkdir()
    original_stop = solver.stop

    def failed(process):
        original_stop(process)
        raise solver.CleanupError('uncertain cleanup')
    monkeypatch.setattr(solver, 'stop', failed)
    with pytest.raises(solver.CleanupError):
        solver.supervise([sys.executable, '-I', '-c', 'pass'], folder, tmp_path,
                         time.monotonic()+5, time.time()+5)


def receipt(tmp_path):
    folder = tmp_path/'cell'
    folder.mkdir()
    for name in ('request.json', 'solver.json'):
        solver.save(folder/name, {'original': True})
    r = dict(completed=True, proposal='plus', wout_sha256='a'*64,
             sources_before={}, sources_after={}, environment_sha256='b'*64,
             request_sha256=solver.digest(folder/'request.json'),
             solver_report_sha256=solver.digest(folder/'solver.json'))
    solver.save(folder/'parent.json', r)
    r['record_sha256'] = solver.digest(folder/'parent.json')
    return folder, r


@pytest.mark.parametrize('changed', ['parent.json', 'solver.json', 'request.json', 'incomplete'])
def test_bad_receipt_cannot_enter_numerical_intake(tmp_path, monkeypatch, changed):
    from fusion_baselines import joint_target

    folder, record = receipt(tmp_path)
    if changed == 'incomplete':
        record['completed'] = False
    else:
        (folder/changed).write_text('{"changed":true}')
    monkeypatch.setattr(joint_target, 'intake',
                        lambda *args: pytest.fail('untrusted target admitted'))
    with pytest.raises(ValueError):
        solver.intake_result(folder, record, lambda: None)


def test_receipt_is_rechecked_after_independent_intake(tmp_path, monkeypatch):
    from fusion_baselines import joint_target

    folder, record = receipt(tmp_path)

    def changed(*args):
        (folder/'solver.json').write_text('{"changed":true}')
        return {}, {}, {}, {'physical_admission': False}
    monkeypatch.setattr(joint_target, 'intake', changed)
    with pytest.raises(ValueError, match='changed'):
        solver.intake_result(folder, record, lambda: None)


def test_provenance_does_not_change_execution_or_physical_status(tmp_path, monkeypatch):
    from fusion_baselines import joint_target

    folder, record = receipt(tmp_path)
    monkeypatch.setattr(joint_target, 'intake', lambda *args: ({}, {}, {}, dict(
        solver_provenance_verified=False, full_joint_execution_enabled=False,
        physical_admission=False, B2_scale=joint_target.check.B2)))
    _, _, _, numerical = solver.intake_result(folder, record, lambda: None)
    assert numerical['solver_provenance_verified']
    assert not numerical['full_joint_execution_enabled'] and not numerical['physical_admission']
    assert numerical['B2_scale'] == joint_target.check.B2


def test_bound_source_mutation_is_rejected(tmp_path):
    p = tmp_path/'source'
    p.write_text('original')
    sources = {str(p): solver.digest(p)}
    p.write_text('changed')
    with pytest.raises(ValueError, match='changed'):
        solver.check_sources(sources)


@pytest.mark.parametrize('fault', ['none', 'converted_input', 'returned_input', 'solver_file',
                                  'failed_convergence', 'nan_residual', 'override'])
def test_worker_cold_call_and_input_environment_binding(tmp_path, monkeypatch, fault):
    import copy
    import types

    from fusion_baselines import joint_target

    document = {'return_outputs_even_if_not_converged': False, 'ftol_array': [1e-12]}
    fake_source = tmp_path/'vmecpp.py'
    fake_source.write_text('frozen solver')
    extension = tmp_path/'vmecpp.so'
    extension.write_bytes(b'frozen extension')
    input_path = tmp_path/'input.json'
    solver.save(input_path, document)
    lock = tmp_path/'environment.json'
    solver.save(lock, {'frozen': True})
    request = dict(proposal='plus', input_sha256=solver.digest(input_path),
        environment=str(lock), environment_sha256=solver.digest(lock),
        sources={str(input_path): solver.digest(input_path), str(lock): solver.digest(lock)},
        arm_root=str(tmp_path), deadline_monotonic=time.monotonic()+5,
        deadline_wall=time.time()+5)
    solver.save(tmp_path/'request.json', request)
    monkeypatch.setattr(solver, 'identity', lambda: {'frozen': True})
    monkeypatch.setattr(joint_target, 'registered_input', lambda *args: (document, document))
    monkeypatch.setattr(solver.importlib.metadata, 'distribution', lambda _: types.SimpleNamespace(
        locate_file=lambda _: tmp_path))
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS',
                'MKL_NUM_THREADS'):
        monkeypatch.setenv(key, '1')
    parsed = types.SimpleNamespace(
        model_dump=lambda **_: dict(document, unexpected=1) if fault == 'converted_input'
        else copy.deepcopy(document), return_outputs_even_if_not_converged=fault == 'override')
    calls = []

    def run(value, **kwargs):
        calls.append(kwargs)
        if fault == 'solver_file':
            fake_source.write_text('changed solver')
        wout = types.SimpleNamespace(ier_flag=0, ns=401, niter=3, fsqz=1e-13, fsql=1e-13,
            fsqr=float('nan') if fault == 'nan_residual' else (
                1e-8 if fault == 'failed_convergence' else 1e-13),
            save=lambda p: p.write_bytes(b'retained output'))
        output_input = types.SimpleNamespace(model_dump=lambda **_: dict(document, changed=True))
        return types.SimpleNamespace(wout=wout, input=output_input if fault == 'returned_input'
                                     else parsed)

    module = types.SimpleNamespace(__file__=str(fake_source), run=run,
        VmecInput=types.SimpleNamespace(model_validate=lambda _: parsed))
    monkeypatch.setitem(sys.modules, 'vmecpp', module)
    monkeypatch.setitem(sys.modules, 'vmecpp.cpp._vmecpp', types.SimpleNamespace(
        __file__=str(extension)))
    status = solver.worker(tmp_path/'request.json')
    report = solver.read(tmp_path/'solver.json')
    assert status == (0 if fault == 'none' else 1)
    if fault in ('converted_input', 'override'):
        assert not calls and not (tmp_path/'wout.nc').exists()
    else:
        assert calls == [dict(max_threads=1, verbose=True, restart_from=None, magnetic_field=None)]
        assert (tmp_path/'wout.nc').read_bytes() == b'retained output'
    if fault == 'none':
        assert report['completed'] and report['converged'] and report['output_input_exact']
    else:
        assert not (report['completed'] and report['converged'])


def test_sigterm_of_supervisor_cleans_live_native_group(tmp_path):
    folder = tmp_path/'cell'
    folder.mkdir()
    source = str(Path(__file__).resolve().parents[1]/'src')
    child = "import os,time; print(os.getpid(),flush=True); time.sleep(30)"
    code = (f"import sys,time;sys.path.insert(0,{source!r});from pathlib import Path;"
            "from fusion_baselines.joint_equilibrium import supervise;"
            f"r=supervise([sys.executable,'-I','-c',{child!r}],Path({str(folder)!r}),"
            f"Path({str(tmp_path)!r}),time.monotonic()+20,time.time()+20);"
            "sys.exit(0 if r['completed'] else 1)")
    process = subprocess.Popen([sys.executable, '-I', '-c', code],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        env=dict(PATH='/usr/bin:/bin', PYTHONDONTWRITEBYTECODE='1'))
    pid = None
    try:
        deadline = time.monotonic()+5
        while time.monotonic() < deadline:
            log = folder/'solver.log'
            if log.exists() and log.read_text().strip():
                pid = int(log.read_text().strip())
                break
            assert process.poll() is None
            time.sleep(.02)
        assert pid is not None, 'surrogate did not start'
        process.terminate()
        assert process.wait(timeout=5) != 0
        for _ in range(50):
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
            time.sleep(.02)
        else:
            pytest.fail('native group survived supervisor SIGTERM')
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        if pid is not None:
            try:
                os.killpg(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


def test_sigterm_handler_is_restored(tmp_path):
    folder = tmp_path/'cell'
    folder.mkdir()
    before = signal.getsignal(signal.SIGTERM)
    solver.supervise([sys.executable, '-I', '-c', 'pass'], folder, tmp_path,
                     time.monotonic()+5, time.time()+5)
    assert signal.getsignal(signal.SIGTERM) == before


def test_sigterm_during_cleanup_does_not_interrupt_cleanup(tmp_path, monkeypatch):
    folder = tmp_path/'cell'
    folder.mkdir()
    original_stop = solver.stop

    def interrupted_cleanup(process):
        try:
            os.kill(os.getpid(), signal.SIGTERM)
        finally:
            original_stop(process)
    monkeypatch.setattr(solver, 'stop', interrupted_cleanup)
    result = solver.supervise([sys.executable, '-I', '-c', 'pass'], folder, tmp_path,
                              time.monotonic()+5, time.time()+5)
    assert not result['completed'] and result['stop_reason'] == 'supervisor SIGTERM'
