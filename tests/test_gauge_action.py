import numpy as np
import pytest

from fusion_baselines.gauge_action import gauge_chain_rule


@pytest.mark.parametrize("amplitude", [0.0, 0.1])
@pytest.mark.parametrize("slope", [-1, 1])
def test_known_chain_rule_sign_and_omnigenous_invariance(amplitude, slope):
    alpha = 0.3
    a0 = 1.5 + amplitude * np.sin(alpha)
    stencil = np.array(
        [
            [1.5 + amplitude * np.sin(alpha - h), 1.5 + amplitude * np.sin(alpha + h)]
            for h in (0.01, 0.005)
        ]
    )
    exact = -1 + slope * amplitude * np.cos(alpha)
    result = gauge_chain_rule(-1.0, exact, stencil, a0, slope)
    assert result["chain_pass"] and result["alpha_refinement_pass"]
    assert abs(result["predicted_derivative"] - exact) <= 5e-7
    if amplitude == 0:
        assert result["predicted_derivative"] == -1.0


def test_detect_wrong_chain_rule_and_invalid_domain():
    result = gauge_chain_rule(-1.0, 1.0, [[1.0, 1.0], [1.0, 1.0]], 1.0, 1)
    assert not result["chain_pass"]
    with pytest.raises(ValueError):
        gauge_chain_rule(-1.0, -1.0, [[0.0, 1.0], [1.0, 1.0]], 1.0, 1)
