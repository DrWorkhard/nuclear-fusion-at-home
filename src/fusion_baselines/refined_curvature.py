"""Fine curvature penalties explicitly mapped onto the original curve DOFs."""

import numpy as np


class RefinedCurvePenalty:
    def __init__(self, bases, refined, objectives):
        self.bases, self.refined, self.objectives = map(list, (bases, refined, objectives))
        if not self.bases or not len(self.bases) == len(self.refined) == len(self.objectives):
            raise ValueError("one refined curve and objective required per base")
        self.dof_names = [name for base in self.bases for name in base.dof_names]
        if len(self.dof_names) != len(set(self.dof_names)):
            raise ValueError("duplicate base DOF names")
        for base, fine, objective in zip(self.bases, self.refined, self.objectives, strict=True):
            if (base.dofs is not fine.dofs or objective.curve is not fine
                    or list(base.local_dof_names) != list(fine.local_dof_names)
                    or [name.split(":", 1)[-1] for name in objective.dof_names]
                    != list(fine.local_dof_names)):
                raise ValueError("refined curve identity or derivative order mismatch")
        self._check_state()

    @property
    def x(self):
        return np.concatenate([base.x for base in self.bases])

    def _check_state(self):
        for base, fine, objective in zip(self.bases, self.refined, self.objectives, strict=True):
            if not np.array_equal(base.x, fine.x) or not np.array_equal(fine.x, objective.x):
                raise ValueError("refined/base state mismatch")

    def J(self):
        self._check_state()
        return sum(float(objective.J()) for objective in self.objectives)

    def dJ(self):
        self._check_state()
        gradients = [np.asarray(objective.dJ(), dtype=float) for objective in self.objectives]
        if any(g.shape != base.x.shape for g, base in zip(gradients, self.bases, strict=True)):
            raise ValueError("refined gradient shape mismatch")
        return np.concatenate(gradients)


def make_refined_penalty(bases, threshold, resolution=1600):
    # Optional benchmark dependencies are deliberately absent from core imports.
    from simsopt.geo import CurveXYZFourier, LpCurveCurvature

    refined = [CurveXYZFourier(resolution, (len(base.local_full_x)//3 - 1)//2,
                              dofs=base.dofs) for base in bases]
    objectives = [LpCurveCurvature(curve, 2, threshold) for curve in refined]
    return RefinedCurvePenalty(bases, refined, objectives)
