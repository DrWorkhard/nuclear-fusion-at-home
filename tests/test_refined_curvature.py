import numpy as np
import pytest

from fusion_baselines.budgeted_oracle import NamedVectorBackend
from fusion_baselines.refined_curvature import RefinedCurvePenalty


class Curve:
    def __init__(self, name, dofs):
        self.name, self.dofs = name, dofs
        self.local_dof_names = ["a", "b"]
        self.dof_names = [name+":"+s for s in self.local_dof_names]

    @property
    def x(self):
        return self.dofs.copy()


class Objective:
    def __init__(self, curve):
        self.curve = curve
        self.dof_names = curve.dof_names

    @property
    def x(self):
        return self.curve.x

    def J(self):
        return float(self.x @ self.x)

    def dJ(self):
        return 2*self.x


def test_shared_refinement_preserves_original_gradient_names():
    dofs = np.array([1., 2.])
    base, fine = Curve("base", dofs), Curve("fine", dofs)
    objective = Objective(fine)
    wrapper = RefinedCurvePenalty([base], [fine], [objective])

    class Global:
        dof_names = ["base:b", "base:a"]

        @property
        def x(self):
            return dofs[::-1].copy()

        @x.setter
        def x(self, values):
            dofs[:] = values[::-1]

    backend = NamedVectorBackend(Global(), [wrapper], [1])
    values, jac = backend(np.array([3., 4.]))
    np.testing.assert_array_equal(values, [25])
    np.testing.assert_array_equal(jac, [[6, 8]])
    assert wrapper.dof_names == ["base:a", "base:b"]
    assert objective.dof_names == ["fine:a", "fine:b"]


def test_unshared_or_reordered_refinement_rejected():
    dofs = np.array([1., 2.])
    base, fine = Curve("base", dofs), Curve("fine", dofs.copy())
    with pytest.raises(ValueError, match="identity"):
        RefinedCurvePenalty([base], [fine], [Objective(fine)])
    fine.dofs = dofs
    objective = Objective(fine)
    objective.dof_names = objective.dof_names[::-1]
    with pytest.raises(ValueError, match="order"):
        RefinedCurvePenalty([base], [fine], [objective])
