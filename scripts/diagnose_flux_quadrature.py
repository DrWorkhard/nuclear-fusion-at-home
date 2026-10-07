"""Unchanged analytic controls from the completed #48 interval-estimator study."""

import numpy as np

from fusion_baselines import flux_labels as labels


class UniformY:
    def set_points(self, points):
        self.points = points

    def A(self):
        return np.column_stack((np.zeros((len(self.points), 2)), -self.points[:, 0]))

    def B(self):
        return np.tile([0., 1., 0.], (len(self.points), 1))


def controls(guard):
    theta = np.sort(np.random.default_rng(4810).uniform(0, 2*np.pi, 160))
    rows = []
    for modulation in (0., .2):
        radius = .2*(1+modulation*np.cos(2*theta))
        rz = np.column_stack((1.+radius*np.cos(theta), radius*np.sin(theta)))
        spline, _ = labels.polar_contour(rz, [1., 0.])
        area = 0.
        for coefficients, width in zip(spline.c.T, np.diff(spline.x), strict=True):
            polynomial = np.polynomial.Polynomial(coefficients[::-1])
            area += .5*(polynomial*polynomial).integ()(width)
        area = float(area)
        result = labels.interval_flux_integrals(UniformY(), spline, [1., 0.], guard=guard)
        errors = dict(line=abs(result['line_flux']+area), area=abs(result['area_flux']+area))
        if not modulation:
            errors['circle'] = abs(area-np.pi*.2**2)
        rows.append(dict(modulation=modulation, exact_spline_area=area, errors=errors,
                         passed=bool(max(errors.values()) < 1e-10)))
    return rows

