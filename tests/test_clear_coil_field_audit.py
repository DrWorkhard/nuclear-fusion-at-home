"""Qualified archive identity and normalization controls."""

import json

import numpy as np
import pytest

from fusion_baselines import clear_coil_field_audit as audit


def archives():
    phi, theta = np.meshgrid(
        np.pi * np.arange(64) / 64, 2 * np.pi * np.arange(64) / 64, indexing="ij"
    )
    rows = []
    for s in (0.25, 0.5, 0.75):
        radius = 1 + 0.3 * np.sqrt(s) * np.cos(theta)
        height = 0.3 * np.sqrt(s) * np.sin(theta)
        et = np.stack((np.zeros_like(phi), np.zeros_like(phi), np.ones_like(phi)), axis=-1)
        ep = np.stack((-np.sin(phi), np.cos(phi), np.zeros_like(phi)), axis=-1)
        bt = np.full_like(phi, 0.02 * s)
        bp = 1 + 0.1 * np.cos(32 * theta)
        native = bt[..., None] * et + bp[..., None] * ep
        rows.append(
            dict(
                s=s,
                n=64,
                arrays=dict(
                    phi=phi.copy(),
                    theta=theta.copy(),
                    radius=radius,
                    height=height,
                    et=et,
                    ep=ep,
                    bt=bt,
                    bp=bp,
                    native=native,
                ),
            )
        )
    return rows

def test_archived64_b2_is_fixed_when32_subsample_has_different_field_energy():
    source = archives()
    coarse, fine = [audit.archived_target(source, n) for n in (32, 64)]
    assert coarse["B2_scale"] == fine["B2_scale"]
    assert not np.isclose(coarse["B2_scale"], np.mean(np.sum(coarse["inner_target"] ** 2, axis=1)))
    for key in ("inner_points", "inner_target"):
        np.testing.assert_array_equal(
            coarse[key], fine[key].reshape(3, 64, 64, 3)[:, ::2, ::2].reshape(-1, 3)
        )
    assert coarse["inner_points"].shape == (3 * 32**2, 3)
    assert coarse["radii"] == [0.25, 0.5, 0.75]

@pytest.mark.parametrize(
    "mutation",
    [
        lambda a: a.pop(),
        lambda a: a.reverse(),
        lambda a: a[0].update(n=128),
        lambda a: a[0].update(n=64.0),
        lambda a: a[0].update(s=0.3),
        lambda a: a[0]["arrays"].update(phi=a[0]["arrays"]["phi"] + 1e-8),
        lambda a: a[0]["arrays"].update(theta=a[0]["arrays"]["theta"] + 1e-8),
        lambda a: a[0]["arrays"].update(native=a[0]["arrays"]["native"] + 1e-6),
        lambda a: a[0]["arrays"].update(radius=-a[0]["arrays"]["radius"]),
        lambda a: a[0]["arrays"].update(ep=a[0]["arrays"]["ep"][::2]),
        lambda a: a[0]["arrays"].update(bp=np.full((64, 64), np.nan)),
        lambda a: a[0]["arrays"].update(bp=np.full((64, 64), 1j)),
    ],
)
def test_archive_identity_or_coordinate_mutation_fails(mutation):
    value = archives()
    mutation(value)
    with pytest.raises((ValueError, KeyError)):
        audit.archived_target(value, 32)

@pytest.mark.parametrize("n", [16, 128, True, 32.0])
def test_unqualified_inner_grid_not_substituted(n):
    with pytest.raises(ValueError):
        audit.archived_target(archives(), n)

def test_json_scalar_normalization_does_not_repeat_historical_np_bool_bug():
    normalized = audit.json_value(
        dict(flags=[np.bool_(False), np.bool_(True)], value=np.float64(0.25))
    )
    assert normalized["flags"][0] is False and normalized["flags"][1] is True
    assert json.loads(json.dumps(normalized, allow_nan=False)) == normalized
    for bad in (np.nan, np.inf, np.complex128(1j), object()):
        with pytest.raises(ValueError):
            audit.json_value(bad)
