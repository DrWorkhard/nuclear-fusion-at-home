import numpy as np
import pytest

from fusion_baselines.bounce_action import bounce_wells
from fusion_baselines.radial_action import match_intervals, radial_sign_screen


def test_matching_uses_geometry_not_order():
    anchor = [[2, 3], [4, 5]]
    candidate = [[4.01, 5.01], [0, 1], [2.01, 3.01]]
    np.testing.assert_array_equal(match_intervals(anchor, candidate, [1.5, 5.5]), [2, 0])


@pytest.mark.parametrize("candidate", [
    [[2, 3]], [[2, 3], [2.01, 3.01], [4, 5]],
    [[2, 3], [3.1, 3.9], [4, 5]], [[2.3, 3.3], [4, 5]], [], [[2, np.nan]],
])
def test_ambiguous_missing_born_or_displaced_wells_fail(candidate):
    with pytest.raises(ValueError):
        match_intervals([[2, 3], [4, 5]], candidate, [1.5, 5.5])


@pytest.mark.parametrize("slope,sign", [(-0.7, "negative"), (0.4, "positive"), (0, "unresolved")])
def test_known_linear_radial_action(slope, sign):
    delta = np.array([0.04, 0.02, 0.01])[:, None] * [-1, 1]
    actions = np.tile(2 * (1 + slope * delta), (3, 1, 1))
    result = radial_sign_screen(actions, 2)
    assert result["sign"] == sign
    assert result["refinement_pass"]
    assert result["estimate"] == pytest.approx(slope)
    scaled = radial_sign_screen(actions * 10, 20)
    assert scaled["estimate"] == pytest.approx(slope)


def test_unstable_or_invalid_stencil_not_positive():
    actions = np.ones((3, 3, 2))
    actions[-1, -1, 1] += 0.1
    assert not radial_sign_screen(actions, 1)["refinement_pass"]
    assert radial_sign_screen(actions, 1)["sign"] == "unresolved"
    actions[0, 0, 0] = np.nan
    with pytest.raises(ValueError):
        radial_sign_screen(actions, 1)


def test_parabolic_well_end_to_end_radial_sign():
    # B(phi)=1+0.1(phi-pi)^2; dl/dphi=2*(1-0.6*(s-0.5)).
    # At fixed Bstar=1.5 the exact normalized radial derivative is -0.6.
    steps = np.array([0.04, 0.02, 0.01])
    actions = np.empty((3, 3, 2))
    for level, nphi in enumerate([801, 1601, 3201]):
        phi = np.linspace(0, 2 * np.pi, nphi)
        field = 1 + 0.1 * (phi - np.pi)**2
        for j, h in enumerate(steps):
            for side, delta in enumerate([-h, h]):
                length = 2 * (1 - 0.6 * delta) * phi
                wells = bounce_wells(length, field, 1.5)
                assert len(wells) == 1 and wells[0].complete
                interval = np.interp([wells[0].left, wells[0].right], length, phi)
                ideal = np.pi + np.array([-1, 1]) * np.sqrt(5)
                assert match_intervals([ideal], [interval], [1, 5]).tolist() == [0]
                actions[level, j, side] = wells[0].action
    a0 = bounce_wells(2 * phi, field, 1.5)[0].action
    assert a0 == pytest.approx(np.pi * 0.5 / np.sqrt(0.15), rel=1e-6)
    result = radial_sign_screen(actions, a0)
    assert result["sign"] == "negative" and result["refinement_pass"]
    assert result["estimate"] == pytest.approx(-0.6, abs=1e-10)
