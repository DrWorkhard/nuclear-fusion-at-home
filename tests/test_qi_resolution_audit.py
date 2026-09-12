import sys
from pathlib import Path

import numpy as np
from test_clebsch_field import torus

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_qi_resolution import direct_fidelity, loop_errors, saved_errors

from fusion_baselines.clebsch_field import compare_fields


def test_independent_saved_arithmetic_detects_mutated_component():
    data = torus()
    native, clebsch, errors, _ = compare_fields(**data)
    data.update(native=native, clebsch=clebsch, psi=np.array(data["psi"]))
    assert saved_errors(data, 2 * np.pi, errors)[1]
    data["bp"][1] *= 1.01
    assert not saved_errors(data, 2 * np.pi, errors)[1]


def test_independent_nested_and_fidelity_mutation():
    old = dict(mod_b=np.ones((2, 2)), et=np.ones((2, 2, 3)), ep=np.ones((2, 2, 3)),
               radius=np.ones((2, 2)), height=np.zeros((2, 2)), iota=np.array(0.7))
    assert all(v == 0 for v in direct_fidelity(old, old).values())
    fine = {k: np.repeat(np.repeat(v, 2, axis=0), 2, axis=1) if v.ndim >= 2 else v.copy()
            for k, v in old.items()}
    assert max(loop_errors(fine, old, 2).values()) == 0
    fine["radius"][0, 0] = 1.1
    assert loop_errors(fine, old, 2)["radius"] > 0.09
