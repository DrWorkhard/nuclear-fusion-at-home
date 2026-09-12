import pytest

from fusion_baselines import jac_scaled_solver as solver
from fusion_baselines.staged_auglag import LS_OPTIONS


def test_only_scale_changes_and_callbacks_are_identical(monkeypatch):
    fun, jac, point, answer = object(), object(), object(), object()
    received = {}

    def fake(f, x, *, jac, **options):
        received.update(fun=f, x=x, jac=jac, options=options)
        return answer

    original = LS_OPTIONS.copy()
    monkeypatch.setattr(solver, "least_squares", fake)
    assert solver.jac_scaled_least_squares(fun, point, jac=jac, **LS_OPTIONS) is answer
    assert received["fun"] is fun and received["x"] is point and received["jac"] is jac
    assert received["options"] == {**original, "x_scale": "jac"}
    assert LS_OPTIONS == original


@pytest.mark.parametrize(
    "changes", [{"x_scale": 2.0}, {"gtol": 1e-5}, {"loss": "huber"}, {"unregistered_option": 1}]
)
def test_unregistered_option_changes_rejected(changes):
    with pytest.raises(ValueError, match="complete original"):
        solver.jac_scaled_least_squares(None, None, jac=None, **{**LS_OPTIONS, **changes})
