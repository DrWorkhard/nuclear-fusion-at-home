"""Neutral circular seed geometry (#114 N33): a valid public candidate centred on the plasma."""

import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pytest

from fusion_public.data import validate_candidate

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("seed", ROOT/"scripts/make_circular_seed.py")
seed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seed)
SELECTED = json.loads((ROOT/"evidence/plasma-balanced-v1/selected-input-401.json").read_text(encoding="utf-8"))


def points(coefficients, count=64):
    t = 2*math.pi*np.arange(count)/count
    out = []
    for axis in coefficients:
        c = np.asarray(axis)
        harmonics = range(1, len(c)//2 + 1)
        out.append(c[0] + sum(c[2*k-1]*np.sin(k*t) + c[2*k]*np.cos(k*t) for k in harmonics))
    return np.stack(out, axis=-1)


def test_seed_is_a_valid_candidate_of_planar_circles_around_the_section_centre():
    candidate = seed.circular_seed(SELECTED, 0.4)
    validate_candidate(candidate)
    for i, coil in enumerate(candidate["base_coefficients"]):
        xyz = points(coil)
        phi = (i + 0.5)*(math.pi/2)/6
        normal = np.array([-math.sin(phi), math.cos(phi), 0.0])
        assert np.allclose(xyz @ normal, 0, atol=1e-12)  # in the plane of its toroidal angle
        centre = xyz.mean(axis=0)
        assert np.allclose(np.linalg.norm(xyz - centre, axis=1), 0.4, atol=1e-12)
        r0 = sum(r["value"]*math.cos(r["n"]*2*phi) for r in SELECTED["rbc"] if r["m"] == 0)
        z0 = -sum(r["value"]*math.sin(r["n"]*2*phi) for r in SELECTED["zbs"] if r["m"] == 0)
        assert np.hypot(*centre[:2]) == pytest.approx(r0) and centre[2] == pytest.approx(z0)


@pytest.mark.parametrize("radius", [0.0, -0.1, 1.0])
def test_seed_rejects_unphysical_radius(radius):
    with pytest.raises(ValueError):
        seed.circular_seed(SELECTED, radius)
