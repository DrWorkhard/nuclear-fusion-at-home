import numpy as np
import pytest

from fusion_baselines.analytic_mirror import reduced_drift
from fusion_baselines.vacuum_mirror import (
    gauge_projections,
    turning_points,
    vacuum_field,
    vacuum_line,
    vacuum_units,
)


def test_exact_vacuum_clebsch_and_fieldline_tangent():
    z = np.array([-0.7, -0.3, 0.1])
    p = vacuum_line(0.02, 0.4, z)
    f = vacuum_field(p)
    np.testing.assert_allclose(np.cross(f["grad_psi"], f["grad_alpha"]), f["B"], atol=1e-14)
    np.testing.assert_allclose(f["psi"], 0.02, atol=1e-15)
    np.testing.assert_allclose(f["alpha"], 0.4, atol=1e-15)
    assert abs(f["divergence"]).max() == 0 and abs(f["curl"]).max() == 0
    h = 1e-6
    tangent = (vacuum_line(0.02, 0.4, z + h) - vacuum_line(0.02, 0.4, z - h)) / (2 * h)
    np.testing.assert_allclose(tangent, f["B"] / f["B"][:, 2, None], atol=1e-9)


@pytest.mark.parametrize("h", [1e-5, 1e-6])
def test_all_cartesian_derivatives_independent_fd(h):
    p = vacuum_line(0.02, 0.4, np.array([-0.7, -0.3, 0.1]))
    field = vacuum_field(p)
    for i in range(3):
        d = h * np.eye(3)[i]
        plus, minus = vacuum_field(p + d), vacuum_field(p - d)
        np.testing.assert_allclose(
            (plus["B"] - minus["B"]) / (2 * h), field["jacobian"][..., i], atol=1e-9
        )
        for key, grad in (
            ("psi", "grad_psi"),
            ("alpha", "grad_alpha"),
            ("magnitude", "grad_magnitude"),
        ):
            np.testing.assert_allclose(
                (plus[key] - minus[key]) / (2 * h), field[grad][..., i], atol=2e-8
            )
    plus, minus = vacuum_field(p + h * field["unit"]), vacuum_field(p - h * field["unit"])
    np.testing.assert_allclose(
        (plus["unit"] - minus["unit"]) / (2 * h), field["curvature"], atol=1e-8
    )


def test_two_asymmetric_roots_and_general_vacuum_drift_agree():
    work = {}
    roots = turning_points(0.02, 1.4, 0.4, work=work)
    f = vacuum_field(vacuum_line(0.02, 0.4, roots))
    np.testing.assert_allclose(f["magnitude"], 1.4, atol=1e-12)
    assert not np.isclose(roots[0], -roots[1])
    assert work["roots_requested"] == work["roots_completed"] == 2 and work["root_calls"] > 4
    f = vacuum_field(vacuum_line(0.02, 0.4, np.linspace(roots[0], roots[1], 11)[1:-1]))
    direct = reduced_drift(f, 1.4)
    vacuum = (
        np.cross(f["unit"], f["grad_magnitude"])
        * (1 - f["magnitude"] / 2.8)[:, None]
        / f["magnitude"][:, None] ** 2
    )
    np.testing.assert_allclose(direct["total"], vacuum, atol=1e-13)
    assert abs(direct["psi"]).max() > 1e-5
    for row in gauge_projections(f, direct):
        np.testing.assert_allclose(
            row["beta"], direct["alpha"] - row["c"] * direct["psi"] / 0.03, atol=1e-13
        )
        np.testing.assert_allclose(row["phase"], row["original_phase"], atol=1e-13)


def test_radial_si_scalings_and_fixed_phase():
    params = dict(mass=2e-27, charge=1.602176634e-19, energy_j=1e4 * 1.602176634e-19)
    base = vacuum_units(0.4, 2, 0.02, -0.1, **params)
    negative = vacuum_units(0.4, 2, 0.02, -0.1, **dict(params, charge=-params["charge"]))
    doubled = vacuum_units(0.4, 2, 0.02, -0.1, **dict(params, energy_j=2 * params["energy_j"]))
    mass = vacuum_units(0.4, 2, 0.02, -0.1, **dict(params, mass=2 * params["mass"]))
    for key in ("psi_rate_Wb_per_rad_s", "omega_alpha_rad_per_s", "phase_rate_rad_per_s"):
        assert negative[key] == -base[key]
        np.testing.assert_allclose(doubled[key], 2 * base[key], rtol=1e-14)
        np.testing.assert_allclose(mass[key], base[key], rtol=1e-14)


@pytest.mark.parametrize("point", [[0, 0, 0], [0.2, 0.1, -1], [np.nan, 0.1, 0]])
def test_invalid_vacuum_points_rejected(point):
    with pytest.raises(ValueError):
        vacuum_field(point)


def test_root_outside_registered_brackets_rejected_and_counted():
    work = {}
    with pytest.raises(ValueError, match="bracket"):
        turning_points(20, 1.2, 0.4, work=work)
    assert work["roots_requested"] == 0 and work["root_calls"] == 2
