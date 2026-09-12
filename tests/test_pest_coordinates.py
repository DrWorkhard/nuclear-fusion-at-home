import numpy as np
import pytest

from fusion_baselines.pest_coordinates import invert_theta, lambda_series, transform_tangents
from fusion_baselines.pest_root_audit import scalar_root


def test_identity_and_periodic_unwrapped_angles():
    u = np.array([-13., -0.4, 0., 2., 19.])
    result = invert_theta(u, 0.7, [0], [0], [0.])
    assert np.array_equal(result["theta"], u)
    assert result["passed"].all() and not result["iterations"].any()


def test_known_shift_and_independent_bracketed_inverse():
    theta = np.linspace(-2, 8, 29)
    phi = np.linspace(0, 1, 29)
    m, n, lam = [1, 2, 0], [0, -2, 2], [.14, -.08, .02]
    u = theta + .14*np.sin(theta) - .08*np.sin(2*theta+2*phi) - .02*np.sin(2*phi)
    result = invert_theta(u, phi, m, n, lam)
    assert result["passed"].all()
    assert np.max(abs(result["theta"] - theta)) <= 2e-12
    for k in range(len(u)):
        other = scalar_root(u[k], phi[k], m, n, lam)
        assert other["passed"]
        for key in ("theta", "lam", "lt", "lp"):
            assert abs(result[key][k] - other[key]) <= 2e-12
    shifted = invert_theta(u+2*np.pi, phi+np.pi, m, n, lam)
    assert shifted["passed"].all()
    assert np.max(abs(shifted["theta"]-result["theta"]-2*np.pi)) <= 2e-12


def test_nested_points_use_identical_updates():
    phi, u = np.meshgrid(np.arange(32)*np.pi/32, np.arange(32)*2*np.pi/32, indexing="ij")
    fine = invert_theta(u, phi, [1, 2], [2, -2], [.1, -.03])
    coarse = invert_theta(u[::2, ::2], phi[::2, ::2], [1, 2], [2, -2], [.1, -.03])
    assert fine["passed"].all() and coarse["passed"].all()
    for key in fine:
        assert np.array_equal(fine[key][::2, ::2], coarse[key])


def test_clipped_iteration_cap_retains_nonconvergence():
    result = invert_theta(0., np.pi/2, [0], [1], [100.])
    assert not result["passed"] and not result["encountered_nonpositive_jacobian"]
    assert result["iterations"] == 50 and result["theta"] == 25.
    assert result["residual"] == -75.
    other = scalar_root(0., np.pi/2, [0], [1], [100.])
    assert other["passed"] and abs(other["theta"]-100) < 1e-12


def test_tangent_chain_rule_against_cartesian_finite_differences():
    u, phi = np.array([.2, 1.4, 3.7]), np.array([.3, .8, 1.1])
    m, n, lam = [1, 2], [2, -2], [.12, -.03]

    def positions(uu, pp):
        solved = invert_theta(uu, pp, m, n, lam)
        assert solved["passed"].all()
        t = solved["theta"]
        r = 3 + .4*np.cos(t)
        return np.stack((r*np.cos(pp), r*np.sin(pp), .4*np.sin(t)), axis=-1)

    solved = invert_theta(u, phi, m, n, lam)
    theta = solved["theta"]
    r = 3 + .4*np.cos(theta)
    et = np.stack((-.4*np.sin(theta)*np.cos(phi), -.4*np.sin(theta)*np.sin(phi),
                   .4*np.cos(theta)), axis=-1)
    ep = np.stack((-r*np.sin(phi), r*np.cos(phi), np.zeros_like(phi)), axis=-1)
    eu, ep_u = transform_tangents(et, ep, solved["lt"], solved["lp"])
    h = 1e-5
    assert np.max(abs(eu - (positions(u+h, phi)-positions(u-h, phi))/(2*h))) < 1e-9
    assert np.max(abs(ep_u - (positions(u, phi+h)-positions(u, phi-h))/(2*h))) < 1e-9


@pytest.mark.parametrize("lam", [[-1.], [-1.1]])
def test_singular_or_reversed_jacobian_never_passes(lam):
    result = invert_theta(0., 0., [1], [0], lam)
    assert not result["passed"] and result["encountered_nonpositive_jacobian"]
    assert result["iterations"] == 0
    with pytest.raises(ValueError, match="positive sampled"):
        transform_tangents(np.ones(3), np.ones(3), result["lt"], result["lp"])


@pytest.mark.parametrize("m,n,lam", [([1], [0], [np.nan]), ([.2], [0], [.1]),
                                    ([1, 1], [0, 0], [.1, .2]), ([], [], [])])
def test_malformed_modes_fail(m, n, lam):
    with pytest.raises(ValueError):
        lambda_series(0., 0., m, n, lam)
    with pytest.raises(ValueError):
        scalar_root(0., 0., m, n, lam)


def test_invalid_angles_and_tangent_shapes_fail():
    with pytest.raises(ValueError):
        invert_theta(np.nan, 0., [1], [0], [.1])
    with pytest.raises(ValueError):
        invert_theta([], [], [1], [0], [.1])
    with pytest.raises(ValueError):
        transform_tangents(np.ones((2, 3)), np.ones((2, 3)), .1, .2)
