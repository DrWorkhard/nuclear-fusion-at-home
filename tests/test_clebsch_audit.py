import importlib.util
from pathlib import Path

import numpy as np

from fusion_baselines.clebsch_field import compare_fields


def test_independent_array_replay_and_changed_field():
    path = Path(__file__).resolve().parents[1] / "scripts/audit_qi_clebsch.py"
    spec = importlib.util.spec_from_file_location("clebsch_audit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    ones, zero = np.ones((2, 3)), np.zeros((2, 3))
    data = dict(psi=np.array(-1.), g=-ones, bt=ones * 0.7, bp=ones,
                lt=zero, lp=zero, iota=np.array(0.7),
                et=np.stack((ones, zero, zero), axis=-1),
                ep=np.stack((zero, ones, zero), axis=-1), mod_b=ones * np.sqrt(1.49))
    native, clebsch, errors, _ = compare_fields(**data)
    data.update(native=native, clebsch=clebsch)
    independent, matches = module.recheck(data, 2 * np.pi)
    assert independent == errors and matches
    data["native"][0, 0, 0] += 1
    assert not module.recheck(data, 2 * np.pi)[1]
