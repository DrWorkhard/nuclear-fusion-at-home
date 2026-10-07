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
