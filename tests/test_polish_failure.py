import copy
import hashlib
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_polish_failure import startup_checks


def fixture():
    x = np.arange(207, dtype=float)
    d = np.random.default_rng(46).normal(size=len(x))
    d /= np.linalg.norm(d)
    arm = dict(status="error", stop_reason="error", gradient_screen_pass=False,
               error="ValueError: initial physical gradient screen failed",
               evaluations=[], gradient_checks=[])
    def append(v, values):
        arm["evaluations"].append(dict(x_sha256=hashlib.sha256(v.tobytes()).hexdigest(),
                                       values=values.tolist()))
    append(x, np.zeros(138))
    for h in (1e-5, 1e-6, 1e-7, 1e-8):
        plus = np.ones(138) * h
        append(x + h * d, plus)
        append(x - h * d, -plus)
        fd = (plus - (-plus)) / (2*h)
        arm["gradient_checks"].append(dict(eps=h, analytic=np.zeros(138).tolist(),
                                           finite_difference=fd.tolist(),
                                           normalized_errors=abs(fd).tolist()))
    return arm, x


def test_postmortem_preserves_negative_gate_and_checks_all_hashes():
    arm, x = fixture()
    checks, rows = startup_checks(arm, x, list(map(str, range(138))))
    assert all(checks.values()) and rows[-1]["maximum_error"] > 1e-6
    arm["evaluations"][4]["x_sha256"] = "0" * 64
    assert not startup_checks(arm, x, list(map(str, range(138))))[0]["physical_startup_hashes"]


def test_postmortem_detects_arithmetic_mutation_and_missing_bundle():
    arm, x = fixture()
    mutated = copy.deepcopy(arm)
    mutated["gradient_checks"][2]["normalized_errors"][6] = 0
    assert not startup_checks(mutated, x, list(map(str, range(138))))[0]["step_2_arithmetic"]
    arm["evaluations"].pop()
    with pytest.raises(ValueError):
        startup_checks(arm, x, list(map(str, range(138))))
