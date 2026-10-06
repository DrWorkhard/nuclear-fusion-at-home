"""Exploratory toroidal flux of star-shaped Poincare contours, not a surface proof."""

import numpy as np
from scipy.interpolate import CubicSpline


def polar_contour(rz, center):
    """Periodic radius versus geometric angle; expose angular gaps rather than hide them."""
    rz, center = np.asarray(rz, dtype=float), np.asarray(center, dtype=float)
    if rz.ndim != 2 or rz.shape[1] != 2 or len(rz) < 8 or center.shape != (2,):
        raise ValueError("at least eight R,Z points and a two-coordinate center required")
    if not np.isfinite(rz).all() or not np.isfinite(center).all():
        raise ValueError("finite section coordinates required")
    offset = rz-center
    radius = np.linalg.norm(offset, axis=1)
    if np.any(radius <= 1e-10) or np.any(rz[:, 0] <= 0):
        raise ValueError("positive R and nonzero polar radius required")
    angles = np.mod(np.arctan2(offset[:, 1], offset[:, 0]), 2*np.pi)
    order = np.argsort(angles)
    angles, radius = angles[order], radius[order]
    gaps = np.diff(np.r_[angles, angles[0]+2*np.pi])
    if np.min(gaps) < 1e-10:
        raise ValueError("duplicate polar angles cannot define a single-valued contour")
    spline = CubicSpline(np.r_[angles, angles[0]+2*np.pi], np.r_[radius, radius[0]],
                         bc_type="periodic")
    return spline, float(np.max(gaps))


def contour_points(spline, center, count):
    """Counterclockwise R,Z contour at phi=0; tangent is per normalized turn."""
    if type(count) is not int or count < 16:
        raise ValueError("at least sixteen quadrature points required")
    theta = np.arange(count)*2*np.pi/count
    radius, derivative = spline(theta), spline(theta, 1)
    if not np.isfinite([radius, derivative]).all() or np.any(radius <= 0):
        raise ValueError("interpolated contour must have finite positive radius")
    c, s = np.cos(theta), np.sin(theta)
    points = np.column_stack((center[0]+radius*c, np.zeros(count), center[1]+radius*s))
    tangent = 2*np.pi*np.column_stack((derivative*c-radius*s, np.zeros(count),
                                     derivative*s+radius*c))
    if np.any(points[:, 0] <= 0):
        raise ValueError("contour crosses cylindrical axis")
    return points, tangent


def flux_integrals(field, spline, center, count=512, radial_count=12, guard=lambda: None):
    """Compare A line quadrature with B fan quadrature (same field implementation)."""
    points, tangent = contour_points(spline, center, count)
    guard()
    field.set_points(np.ascontiguousarray(points))
    line = float(np.mean(np.einsum("ij,ij->i", field.A(), tangent)))
    guard()
    nodes, weights = np.polynomial.legendre.leggauss(radial_count)
    rho, weights = (nodes+1)/2, weights/2
    origin = np.array([center[0], 0., center[1]])
    radial = points-origin
    jacobian = np.cross(radial, tangent)
    fan = origin+rho[:, None, None]*radial
    normals = weights[:, None, None]*rho[:, None, None]*jacobian/count
    B = []
    for first in range(0, fan.size//3, 128):
        guard()
        field.set_points(np.ascontiguousarray(fan.reshape(-1, 3)[first:first+128]))
        B.append(field.B().copy())
    guard()
    area = float(np.sum(np.concatenate(B)*normals.reshape(-1, 3)))
    return dict(line_flux=line, area_flux=area, stokes_abs_error=abs(line-area))


def interval_contour_points(spline, center, order):
    """Gauss points/weights on every spline interval; tangent is per radian."""
    if type(order) is not int or not 2 <= order <= 16:
        raise ValueError("interval quadrature order must be an integer from 2 to 16")
    center = np.asarray(center, dtype=float)
    if center.shape != (2,) or not np.isfinite(center).all():
        raise ValueError("finite two-coordinate center required")
    nodes, weights = np.polynomial.legendre.leggauss(order)
    widths = np.diff(spline.x)
    theta = (spline.x[:-1, None]+widths[:, None]*(nodes+1)/2).ravel()
    weights = (widths[:, None]*weights/2).ravel()
    radius, derivative = spline(theta), spline(theta, 1)
    if not np.isfinite([radius, derivative]).all() or np.any(radius <= 0):
        raise ValueError("interpolated contour must have finite positive radius")
    c, s = np.cos(theta), np.sin(theta)
    points = np.column_stack((center[0]+radius*c, np.zeros(len(theta)), center[1]+radius*s))
    tangent = np.column_stack((derivative*c-radius*s, np.zeros(len(theta)),
                               derivative*s+radius*c))
    if np.any(points[:, 0] <= 0):
        raise ValueError("contour crosses cylindrical axis")
    return points, tangent, weights


def interval_flux_integrals(field, spline, center, order=8, radial_count=24,
                           guard=lambda: None):
    """A line and B fan flux with angular Gauss integration over each spline piece."""
    points, tangent, angular_weights = interval_contour_points(spline, center, order)
    guard()
    field.set_points(np.ascontiguousarray(points))
    line = float(np.sum(angular_weights*np.sum(field.A()*tangent, axis=1)))
    nodes, weights = np.polynomial.legendre.leggauss(radial_count)
    rho, weights = (nodes+1)/2, weights/2
    origin = np.array([center[0], 0., center[1]])
    radial = points-origin
    fan = origin+rho[:, None, None]*radial
    normals = (weights[:, None, None]*rho[:, None, None]*angular_weights[None, :, None]
               *np.cross(radial, tangent)[None, :, :])
    area = 0.
    for first in range(0, fan.size//3, 128):
        guard()
        field.set_points(np.ascontiguousarray(fan.reshape(-1, 3)[first:first+128]))
        area += float(np.sum(field.B()*normals.reshape(-1, 3)[first:first+128]))
    guard()
    return dict(line_flux=line, area_flux=area, stokes_abs_error=abs(line-area),
                angular_points=len(points))


def contour_diagnostics(field, rz, center, edge_flux, guard=lambda: None,
                        grids=(256, 512), radial_count=12, interval_orders=None):
    """Record both resolution and disjoint crossing-subset sensitivity of a flux estimate."""
    if not np.isfinite(edge_flux) or edge_flux == 0:
        raise ValueError("finite nonzero oriented edge flux required")
    spline, gap = polar_contour(rz, center)
    if interval_orders is None:
        quadrature = [flux_integrals(field, spline, center, n, radial_count, guard) for n in grids]
    else:
        if tuple(interval_orders) != (4, 8):
            raise ValueError("registered interval orders 4 and 8 required")
        quadrature = [interval_flux_integrals(field, spline, center, n, radial_count, guard)
                      for n in interval_orders]
    subsets = []
    for offset in (0, 1):
        section = np.asarray(rz)[offset::2]
        try:
            sub, subgap = polar_contour(section, center)
            if interval_orders is None:
                points, tangent = contour_points(sub, center, grids[-1])
                guard()
                field.set_points(np.ascontiguousarray(points))
                flux = float(np.mean(np.einsum("ij,ij->i", field.A(), tangent)))
                subset_quadrature = {}
            else:
                values = []
                for order in interval_orders:
                    points, tangent, weights = interval_contour_points(sub, center, order)
                    guard()
                    field.set_points(np.ascontiguousarray(points))
                    values.append(float(np.sum(weights*np.sum(field.A()*tangent, axis=1))))
                    guard()
                flux = values[-1]
                subset_quadrature = dict(quadrature_label_change=abs(values[0]-flux)/abs(edge_flux))
            held = np.asarray(rz)[1-offset::2]-center
            angle = np.arctan2(held[:, 1], held[:, 0])
            residual = np.linalg.norm(held, axis=1)-sub(angle)
            subsets.append(dict(label=flux/edge_flux, max_gap_rad=subgap,
                                heldout_radius_max_m=float(np.max(abs(residual))),
                                **subset_quadrature))
        except ValueError as exc:
            subsets.append(dict(error=str(exc)))
    return dict(crossings=len(rz), max_gap_rad=gap, grids=quadrature,
                label=quadrature[-1]["line_flux"]/edge_flux,
                quadrature_label_change=abs(quadrature[0]["line_flux"]-quadrature[1]["line_flux"])
                /abs(edge_flux), subsets=subsets)


def scaled_launch(rz, center, scale):
    """Move a launch along its fixed physical R,Z ray, with a bounded scale factor."""
    rz, center = np.asarray(rz, dtype=float), np.asarray(center, dtype=float)
    if rz.shape != (2,) or center.shape != (2,) or not np.isfinite([rz, center]).all():
        raise ValueError("finite physical R,Z launch and center required")
    if not np.isfinite(scale) or not .95 <= scale <= 1.05:
        raise ValueError("launch scale must remain within [0.95, 1.05]")
    point = center+scale*(rz-center)
    if point[0] <= 0:
        raise ValueError("positive cylindrical R required")
    return point


def secant_scale(old_scale, old_label, new_scale, new_label, desired=.75):
    """One bounded secant proposal; reject ill-conditioned or reversed slopes, never clip."""
    values = np.array([old_scale, old_label, new_scale, new_label, desired])
    if not np.isfinite(values).all() or abs(new_scale-old_scale) < 1e-10:
        raise ValueError("finite distinct scale trials required")
    slope = (new_label-old_label)/(new_scale-old_scale)
    if slope <= 1e-3:
        raise ValueError("positive resolved flux slope required")
    proposal = new_scale+(desired-new_label)/slope
    if not .95 <= proposal <= 1.05:
        raise ValueError("secant proposal outside frozen scale bounds")
    return float(proposal)
