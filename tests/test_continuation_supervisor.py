"""A receipt published after the budget cannot claim scientific completion."""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('continuation_supervisor',
                                             ROOT/'scripts/run_continuation_labels.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_late_publication_retains_attempt_but_fails_completion(tmp_path, monkeypatch):
    def exhausted(output):
        raise ValueError('1800 s total budget exhausted')

    monkeypatch.setattr(module, 'guard', exhausted)
    receipt = module.finish_receipt(tmp_path, dict(completed=True, revision='a'*40))
    assert receipt['completed'] is False
    assert json.loads((tmp_path/'receipt.json').read_bytes()) == receipt
    assert json.loads((tmp_path/'attempted-receipt.json').read_bytes())['completed'] is True
    assert receipt['retained_attempt'] == 'attempted-receipt.json'


def test_exited_leader_still_gets_group_cleanup_after_watchdog_failure(tmp_path, monkeypatch):
    import types

    import pytest

    process = types.SimpleNamespace(returncode=0, poll=lambda: 0)
    stopped, checks = [], []
    monkeypatch.setattr(module.subprocess, 'Popen', lambda *a, **k: process)
    monkeypatch.setattr(module, 'stop', lambda child: stopped.append(child))

    def resources():
        checks.append(True)
        if len(checks) == 2:
            raise ValueError('clock mismatch after leader exit')

    receipt = dict(completed=False)
    with pytest.raises(ValueError, match='clock mismatch'):
        module.supervise([], {}, tmp_path, receipt, resources)
    assert stopped == [process]
    assert receipt['cleanup_confirmed'] is True


def test_cleanup_denial_is_explicit_and_fails_closed(tmp_path, monkeypatch):
    import types

    import pytest

    process = types.SimpleNamespace(returncode=0, poll=lambda: 0)
    monkeypatch.setattr(module.subprocess, 'Popen', lambda *a, **k: process)

    def denied(child):
        raise PermissionError('cannot signal owned process group')

    monkeypatch.setattr(module, 'stop', denied)
    receipt = dict(completed=True)
    with pytest.raises(RuntimeError, match='cleanup failed'):
        module.supervise([], {}, tmp_path, receipt, lambda: None)
    assert receipt['completed'] is False
    assert receipt['cleanup_confirmed'] is False
    assert 'PermissionError' in receipt['cleanup_error']


def test_sigterm_cleans_owned_child_and_restores_handler(tmp_path, monkeypatch):
    import os
    import signal
    import sys

    original_popen = module.subprocess.Popen
    previous_handler = signal.getsignal(signal.SIGTERM)
    children = []
    config = {}
    for name in ('snapshot', 'wout', 'environment'):
        path = tmp_path/name
        path.write_text(name, encoding='utf-8')
        config[name] = str(path)
        monkeypatch.setattr(module, name.upper(), module.digest(path))
    config_path = tmp_path/'config.json'
    config_path.write_text(json.dumps(config), encoding='utf-8')
    monkeypatch.setattr(module, 'clean_head', lambda revision: None)
    monkeypatch.setattr(module, 'guard', lambda output: None)
    monkeypatch.setattr(module, 'verify_environment', lambda path, resources: 0)

    def start_then_signal(command, **kwargs):
        child = original_popen([sys.executable, '-c', 'import time; time.sleep(60)'], **kwargs)
        children.append(child)
        os.kill(os.getpid(), signal.SIGTERM)
        return child

    monkeypatch.setattr(module.subprocess, 'Popen', start_then_signal)
    output = tmp_path/'output'
    try:
        assert module.run(config_path, module.digest(config_path), output, 'a'*40) == 1
        assert signal.getsignal(signal.SIGTERM) == previous_handler
        assert len(children) == 1 and children[0].poll() is not None
        final = json.loads((output/'receipt.json').read_bytes())
        attempted = json.loads((output/'attempted-receipt.json').read_bytes())
        assert final['completed'] is False
        assert attempted['termination_requested'] is True
        assert attempted['cleanup_confirmed'] is True
    finally:
        # Retain test ownership if a regression breaks the production cleanup.
        for child in children:
            if child.poll() is None:
                module.stop(child)
        signal.signal(signal.SIGTERM, previous_handler)
