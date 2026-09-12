import copy

import numpy as np
import pytest

from fusion_baselines.start_qualification_audit import audit_directions


def fixture():
    matrix = np.zeros((138, 207))
    matrix[:, 0] = 1
    direction = np.random.default_rng(46).normal(size=207)
    direction /= np.linalg.norm(direction)
    exact = matrix @ direction
    screens = []
    for eps in (1e-5, 1e-6, 1e-7, 1e-8):
        plus, minus = eps * exact, -eps * exact
        fd = (plus - minus) / (2 * eps)
        error = abs(fd - exact) / np.maximum(1, abs(exact))
        screens.append(dict(eps=eps, plus=plus.tolist(), minus=minus.tolist(),
                            finite_difference=fd.tolist(), normalized_errors=error.tolist(),
                            maximum_error=float(error.max())))
    return matrix, direction, screens


def test_complete_linear_control():
    assert all(audit_directions(*fixture()).values())


@pytest.mark.parametrize("key", ["plus", "finite_difference", "normalized_errors"])
def test_modified_report_rejected(key):
    matrix, direction, screens = fixture()
    screens = copy.deepcopy(screens)
    screens[-1][key][137] += 1
    assert not all(audit_directions(matrix, direction, screens).values())


def test_missing_step_and_row_rejected():
    matrix, direction, screens = fixture()
    with pytest.raises(ValueError):
        audit_directions(matrix, direction, screens[:-1])
    screens[-1]["plus"].pop()
    with pytest.raises(ValueError):
        audit_directions(matrix, direction, screens)
