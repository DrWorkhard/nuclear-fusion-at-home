import numpy as np
import pytest

from fusion_baselines.bounce_action import action_envelope, bounce_wells, linear_segment_action


def test_triangular_well_and_exact_turning_points():
    wells = bounce_wells([-1, 0, 1], [3, 1, 3], 3)
    assert len(wells) == 1 and wells[0].complete
    assert wells[0].action == pytest.approx(4 / 3 * np.sqrt(2 / 3), rel=1e-12)


def test_parabolic_well_converges_to_analytic_integral():
    exact = np.pi / (2 * np.sqrt(2))  # B=1+l^2, Bstar=2
    errors = []
    for points in (257, 1025, 4097):
        length = np.linspace(-1.2, 1.2, points)
        well = bounce_wells(length, 1 + length**2, 2)[0]
        assert well.complete
        errors.append(abs(well.action / exact - 1))
    assert errors[2] < errors[1] < errors[0]
    assert errors[2] <= 2e-5


@pytest.mark.parametrize("q0,q1", [(0, 0.8), (0.8, 0), (0.2, 0.2), (1e-5, 0.99)])
def test_independent_gauss_legendre_quadrature(q0, q1):
    nodes, weights = np.polynomial.legendre.leggauss(128)
    quadrature = np.dot(weights, np.sqrt(q0 + (q1 - q0) * (nodes + 1) / 2)) / 2
    assert linear_segment_action(1, q0, q1) == pytest.approx(quadrature, rel=1e-6)


def test_censoring_contacts_and_no_well():
    assert bounce_wells([0, 1, 2], [3, 3, 3], 2) == []
    assert not bounce_wells([0, 1, 2], [1, 1, 1], 2)[0].complete
    wells = bounce_wells([0, 1, 2, 3, 4], [3, 1, 3, 1, 3], 3)
    assert len(wells) == 2 and all(w.complete for w in wells)
    partial = bounce_wells([0, 1, 2, 3, 4], [1, 3, 1, 3, 1], 2)
    assert [w.complete for w in partial] == [False, True, False]


def test_scaling_and_alpha_modulation_are_detected():
    length = np.array([-1, 0, 1])
    field = np.array([3, 1, 3])
    nominal = bounce_wells(length, field, 3)[0].action
    assert bounce_wells(5 * length, 7 * field, 21)[0].action == pytest.approx(5 * nominal)
    by_alpha = [
        bounce_wells(length * (1 + 0.01 * np.cos(a)), field, 3)
        for a in np.linspace(0, 2 * np.pi, 16, endpoint=False)
    ]
    assert action_envelope(by_alpha)["envelope"] == pytest.approx(0.02, abs=1e-12)
    by_alpha.append([])
    summary = action_envelope(by_alpha)
    assert summary["complete_alpha_coverage"] < 1 and summary["envelope"] is None


@pytest.mark.parametrize(
    "length,field", [([0, 0], [1, 2]), ([1, 0], [1, 2]), ([0, 1], [1, np.nan]), ([0, 1], [1, -1])]
)
def test_invalid_traces_fail(length, field):
    with pytest.raises(ValueError):
        bounce_wells(length, field, 2)
