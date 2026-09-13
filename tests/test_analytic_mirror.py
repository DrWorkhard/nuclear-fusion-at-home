import numpy as np
import pytest

from fusion_baselines.analytic_mirror import absolute_quantities, mirror_field, reduced_drift


def test_clebsch_divergence_and_pressure_force_balance():
    points = np.array([[0.1, 0.2, -0.4], [0.3, -0.1, 0], [0.2, 0.2, 0.7]])
    field = mirror_field(points)
    np.testing.assert_allclose(
        np.cross(field["grad_psi"], field["grad_alpha"]), field["B"], atol=1e-14
    )
    assert np.array_equal(field["divergence"], np.zeros(3))
    assert abs(field["force_balance_residual"]).max() < 1e-14
    assert abs(np.sum(field["unit"] * field["curvature"], axis=-1)).max() < 1e-14


@pytest.mark.parametrize("h", [1e-5, 1e-6])
def test_independent_cartesian_differences_and_fieldline_curvature(h):
    points = np.array([[0.1, 0.2, -0.4], [0.3, -0.1, 0], [0.2, 0.2, 0.7]])
    source = mirror_field(points)
    for j in range(3):
        offset = np.eye(3)[j] * h
        plus, minus = mirror_field(points + offset), mirror_field(points - offset)
        np.testing.assert_allclose(
            (plus["B"] - minus["B"]) / (2 * h), source["jacobian"][..., j], atol=1e-9
        )
        np.testing.assert_allclose(
            (plus["magnitude"] - minus["magnitude"]) / (2 * h),
            source["grad_magnitude"][..., j],
            atol=1e-9,
        )
    plus, minus = (
        mirror_field(points + h * source["unit"]),
        mirror_field(points - h * source["unit"]),
    )
    np.testing.assert_allclose(
        (plus["unit"] - minus["unit"]) / (2 * h), source["curvature"], atol=1e-9
    )


def test_radial_drift_zero_and_azimuth_covariance_without_vacuum_simplification():
    alpha = np.array([0, 0.37, 1.2])
    points = np.stack((0.2 * np.cos(alpha), 0.2 * np.sin(alpha), np.full(3, 0.4)), axis=1)
    field = mirror_field(points)
    drift = reduced_drift(field, 1.6)
    assert abs(drift["psi"]).max() < 1e-15
    np.testing.assert_allclose(drift["alpha"], np.full(3, drift["alpha"][0]), atol=1e-14)
    vacuum = (
        np.cross(field["unit"], field["grad_magnitude"])
        * (1 - field["magnitude"] / 3.2)[:, None]
        / field["magnitude"][:, None] ** 2
    )
    assert np.linalg.norm(vacuum - drift["total"]) > 0.01


def test_absolute_charge_energy_mass_and_one_way_scalings():
    args = dict(mass=2e-27, charge=1.602176634e-19, energy_j=1e4 * 1.602176634e-19)
    base = absolute_quantities(0.2, 2.0, -0.1, **args)
    minus = absolute_quantities(0.2, 2.0, -0.1, **dict(args, charge=-args["charge"]))
    energy = absolute_quantities(0.2, 2.0, -0.1, **dict(args, energy_j=2 * args["energy_j"]))
    mass = absolute_quantities(0.2, 2.0, -0.1, **dict(args, mass=2 * args["mass"]))
    assert minus["omega_alpha_rad_per_s"] == -base["omega_alpha_rad_per_s"]
    np.testing.assert_allclose(
        energy["omega_alpha_rad_per_s"], 2 * base["omega_alpha_rad_per_s"], rtol=1e-14
    )
    np.testing.assert_allclose(
        mass["omega_alpha_rad_per_s"], base["omega_alpha_rad_per_s"], rtol=1e-14
    )
    np.testing.assert_allclose(mass["time_s"], np.sqrt(2) * base["time_s"], rtol=1e-14)
    full = absolute_quantities(0.4, 4.0, -0.2, **args)
    assert full["omega_alpha_rad_per_s"] == base["omega_alpha_rad_per_s"]
    assert full["delta_alpha_rad"] == 2 * base["delta_alpha_rad"]


@pytest.mark.parametrize("point", [[0, 0, 1], [np.nan, 1, 0], [1, 2]])
def test_invalid_mirror_domain_rejected(point):
    with pytest.raises(ValueError):
        mirror_field(point)


def test_inaccessible_pitch_and_invalid_absolute_units_rejected():
    with pytest.raises(ValueError, match="accessible"):
        reduced_drift(mirror_field([0.1, 0.2, 1]), 1.1)
    with pytest.raises(ValueError):
        absolute_quantities(0.2, 2.0, -0.1, mass=2e-27, charge=0, energy_j=1e-15)
