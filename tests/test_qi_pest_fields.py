import netCDF4
import numpy as np
import pytest
from test_qi_field_grid import fixture

from fusion_baselines.qi_field_grid import sample as old_sample
from fusion_baselines.qi_pest_fields import evaluate, grid, read_coefficients, sample
from fusion_baselines.qi_pest_scalar import sample as scalar_sample


def toy_file(path):
    fixture(path)
    with netCDF4.Dataset(path, "r+") as ds:
        ds.createVariable("volume_p", "f8")[:] = 3.2
        ds["lmns"][:, 1] = .03 * np.arange(5)


@pytest.mark.parametrize("surface", [.25, .5, .75])
def test_old_array_replay_and_independent_changed_coordinate_fields(tmp_path, surface):
    path = tmp_path / "toy.nc"
    toy_file(path)
    c = read_coefficients(path, surface)
    theta, phi = grid(c["nfp"], 32)
    fields, old = evaluate(c, theta, phi), old_sample(path, surface, 32)
    assert fields.keys() == old.keys() | {"lam"}
    for k in old:
        np.testing.assert_allclose(fields[k], old[k], rtol=1e-14, atol=1e-14)
    roots, changed = sample(c, 32)
    audit = scalar_sample(path, surface, roots["u"], roots["phi"])
    assert roots["passed"].all() and audit["passed"].all()
    for k in ("theta", "lam", "lt", "lp"):
        np.testing.assert_allclose(roots[k], audit[k], rtol=1e-11, atol=1e-11)
    for k in ("radius", "height", "mod_b", "et", "ep", "eu", "ep_u", "iota"):
        np.testing.assert_allclose(changed[k], audit[k], rtol=1e-11, atol=1e-11)
    assert not np.array_equal(changed["height"], old["height"])
    np.testing.assert_allclose(changed["radius"], 3+.4*np.cos(roots["theta"]), atol=1e-14)
    np.testing.assert_allclose(changed["height"], .4*np.sin(roots["theta"]), atol=1e-14)


def test_inversion_failure_does_not_create_qualified_fields(tmp_path):
    path = tmp_path / "toy.nc"
    toy_file(path)
    c = read_coefficients(path, .5)
    c["lam"][1] = -1
    roots, fields = sample(c, 32)
    assert fields is None and not roots["passed"].all()


def test_nonzero_toroidal_modes_and_half_grid_weighting(tmp_path):
    path = tmp_path / "helical-toy.nc"
    toy_file(path)
    with netCDF4.Dataset(path, "r+") as ds:
        nfp = int(ds["nfp"][...])
        ds["xn"][1] = -nfp
        ds["xn_nyq"][1] = -nfp
        ds["bmnc"][:, 1] = .2
    c = read_coefficients(path, .25)
    assert abs(c["lam"][1] - .045) < 1e-16  # halfway between half-grid rows1 and2
    roots, fields = sample(c, 32)
    audited = scalar_sample(path, .25, roots["u"], roots["phi"])
    assert np.max(abs(roots["lp"])) > 0
    np.testing.assert_allclose(fields["mod_b"],
                               2+.2*np.cos(roots["theta"]+nfp*roots["phi"]), atol=1e-14)
    for k in ("mod_b", "ep_u", "eu", "radius", "height"):
        np.testing.assert_allclose(fields[k], audited[k], rtol=1e-11, atol=1e-11)


def test_bad_wout_coefficients_and_symmetry_rejected(tmp_path):
    path = tmp_path / "toy.nc"
    toy_file(path)
    with netCDF4.Dataset(path, "r+") as ds:
        ds["lmns"][2, 1] = np.nan
    with pytest.raises(ValueError, match="nonfinite"):
        read_coefficients(path, .5)
    with pytest.raises(ValueError, match="nonfinite"):
        scalar_sample(path, .5, np.array([.4]), np.array([.2]))
    with netCDF4.Dataset(path, "r+") as ds:
        ds["lmns"][2, 1] = .1
        ds["lasym__logical__"][:] = 1
    with pytest.raises(ValueError, match="symmetric"):
        read_coefficients(path, .5)


def test_invalid_grid_and_surface_rejected(tmp_path):
    path = tmp_path / "toy.nc"
    toy_file(path)
    with pytest.raises(ValueError):
        read_coefficients(path, .1)
    with pytest.raises(ValueError):
        grid(0, 32)
    with pytest.raises(ValueError):
        grid(2, 7)
