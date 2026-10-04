"""Realized-field magnetic surfaces: traced coil-field lines versus a VMEC target.

A diagnostic separate from fitting and acceptance. Field lines start on target
surfaces at phi=0, theta=0; each line reports whether it stays inside the target
boundary and its rotational transform, measured as the unwrapped poloidal angle
about the target axis per unwrapped toroidal angle. Nested surfaces and a matching
transform are necessary for benefit transfer; they do not demonstrate it.
"""

import hashlib
import math
from pathlib import Path

import numpy as np

from fusion_baselines.reference_wout import validate_reference

S_VALUES = tuple(round(0.05 + 0.1 * k, 2) for k in range(10))


def need(condition, message):
    if not condition:
        raise ValueError(message)


class Target:
    """Fixed-boundary VMEC output: R = sum rmnc cos(m theta - n phi), Z = sum zmns sin(...)."""

    def __init__(self, xm, xn, rmnc, zmns, iotaf, sha256=None):
        self.xm, self.xn = np.asarray(xm, dtype=float), np.asarray(xn, dtype=float)
        self.rmnc, self.zmns = np.asarray(rmnc, dtype=float), np.asarray(zmns, dtype=float)
        self.iotaf, self.sha256 = np.asarray(iotaf, dtype=float), sha256
        self.ns = len(self.iotaf)
        need(self.ns >= 2 and self.rmnc.shape == self.zmns.shape == (self.ns, len(self.xm))
             and np.isfinite([*self.rmnc.ravel(), *self.zmns.ravel(), *self.iotaf]).all(),
             "finite full-mesh target coefficients required")

    @classmethod
    def from_wout(cls, path, target_input=None):
        import netCDF4

        path = Path(path)
        with path.open("rb") as stream:
            sha256 = hashlib.file_digest(stream, "sha256").hexdigest()
        with netCDF4.Dataset(path) as data:
            if target_input is not None:
                validate_reference(data, target_input)
            need(int(data["lasym__logical__"][...]) == 0, "stellarator-symmetric Wout required")
            values = [np.ma.filled(data[k][...], np.nan) for k in
                      ("xm", "xn", "rmnc", "zmns", "iotaf")]
        return cls(*values, sha256=sha256)

    def index(self, s):
        need(0 <= s <= 1, "normalized flux 0..1 required")
        return round(s * (self.ns - 1))

    def rz(self, s, theta, phi):
        angle = np.multiply.outer(np.asarray(theta), self.xm) - np.multiply.outer(
            np.asarray(phi), self.xn)
        j = self.index(s)
        return np.sum(self.rmnc[j] * np.cos(angle), -1), np.sum(self.zmns[j] * np.sin(angle), -1)

    def axis(self, phi):
        return self.rz(0.0, np.zeros_like(np.asarray(phi, dtype=float)), phi)

    def iota(self, s):
        return float(self.iotaf[self.index(s)])


def winding(xyz, target):
    """Toroidal transits and rotational transform of one traced line about the target axis."""
    xyz = np.asarray(xyz, dtype=float)
    need(xyz.ndim == 2 and xyz.shape[1] == 3 and len(xyz) >= 2, "traced positions required")
    phi = np.unwrap(np.arctan2(xyz[:, 1], xyz[:, 0]))
    radius = np.hypot(xyz[:, 0], xyz[:, 1])
    raxis, zaxis = target.axis(np.mod(phi, 2 * np.pi))
    theta = np.unwrap(np.arctan2(xyz[:, 2] - zaxis, radius - raxis))
    turned = phi[-1] - phi[0]
    need(turned != 0, "line must advance toroidally")
    return float(abs(turned) / (2 * np.pi)), float((theta[-1] - theta[0]) / turned)


def coils(candidate, current):
    """24 simsopt coils of a public six-coil candidate at one signed base current."""
    from simsopt.field import Current, coils_via_symmetries
    from simsopt.geo import CurveXYZFourier

    curves = []
    for i, coefficients in enumerate(candidate["base_coefficients"]):
        curve = CurveXYZFourier(512, 5)
        need([f"coil[{i}]/{name}" for name in curve.local_full_dof_names]
             == candidate["parameter_names"][33 * i: 33 * (i + 1)],
             "native named coordinate identity")
        curve.local_full_x = np.asarray(coefficients, dtype=float).ravel()
        curves.append(curve)
    return coils_via_symmetries(curves, [Current(current) for _ in curves], 2, True)


def trace(field, target, surface, transits=200, tol=1e-10, s_values=S_VALUES):
    """Trace until boundary exit, requested transits or the finite integration-time cap."""
    from simsopt.field.tracing import (
        LevelsetStoppingCriterion,
        ToroidalTransitStoppingCriterion,
        compute_fieldlines,
    )
    from simsopt.geo import SurfaceClassifier

    need(0 < transits <= 2000 and 0 < tol < 1e-6, "bounded transits and tight tolerance")
    classifier = SurfaceClassifier(surface, h=0.02, p=2)
    starts = [float(target.rz(s, 0.0, 0.0)[0]) for s in s_values]
    # A finite integration cap, not proof that the requested transits were completed.
    tmax = 1.3 * transits * 2 * math.pi * max(starts)
    paths, hits = compute_fieldlines(field, starts, [0.0] * len(starts), tmax=tmax, tol=tol,
                                     phis=[0.0, math.pi / 2],
                                     stopping_criteria=[LevelsetStoppingCriterion(classifier.dist),
                                                        ToroidalTransitStoppingCriterion(
                                                            transits, False)])
    lines = []
    for s, path, hit in zip(s_values, paths, hits, strict=True):
        # SIMSOPT returns the terminal stopping state in hits, not in the path.
        if len(hit) and hit[-1, 1] < 0 and hit[-1, 0] > path[-1, 0]:
            path = np.vstack((path, hit[-1, [0, 2, 3, 4]]))
        turns, iota = winding(path[:, 1:4], target)
        stopped = bool(len(hit) and np.any(hit[:, 1] == -1))
        # The gridded classifier can stop lines a few mm inside the boundary; only an
        # exact containment test of the stop point confirms an exit.
        left = stopped and not bool(inside_target(target, path[-1:, 1:4])[0])
        termination = ("boundary" if left else "classifier_stop_inside_target" if stopped
                       else "requested_transits" if turns >= transits else "integration_limit")
        lines.append(dict(s=s, R0=float(path[0, 1]), transits=turns, left_target=left,
                          termination=termination,
                          iota_traced=iota, iota_target=target.iota(s)))
    return lines, hits


def inside_target(target, xyz, count=2000):
    """Exact containment of each point in the target boundary section at its own phi."""
    xyz = np.atleast_2d(np.asarray(xyz, dtype=float))
    need(xyz.ndim == 2 and xyz.shape[1] == 3 and count >= 64, "points and section resolution")
    theta = np.linspace(0, 2*np.pi, count, endpoint=False)
    result = []
    for x, y, z in xyz:
        r = math.hypot(x, y)
        br, bz = target.rz(1.0, theta, np.full(count, math.atan2(y, x)))
        nr, nz = np.roll(br, -1), np.roll(bz, -1)
        crosses = (bz > z) != (nz > z)
        with np.errstate(divide="ignore", invalid="ignore"):
            at = br + (z - bz) * (nr - br) / (nz - bz)
        result.append(bool(np.count_nonzero(crosses & (r < at)) % 2))
    return np.asarray(result)


def sample_points(target, rng, count):
    """Seeded 3-D volume locations independent of the structured public sample grid."""
    s = rng.uniform(0.05, 0.95, count)
    theta, phi = rng.uniform(0, 2*math.pi, (2, count))
    rz = [target.rz(a, b, c) for a, b, c in zip(s, theta, phi, strict=True)]
    radius, z = np.asarray(rz).T
    return np.column_stack((radius*np.cos(phi), radius*np.sin(phi), z))


def summarize(lines, requested_transits, iota_tolerance=0.02):
    need(bool(lines) and np.isfinite([requested_transits, iota_tolerance]).all()
         and 0 < requested_transits <= 2000 and iota_tolerance >= 0,
         "nonempty lines, bounded transits and finite tolerance required")
    need(np.isfinite([[line[k] for k in ("transits", "iota_traced", "iota_target")]
                      for line in lines]).all(), "finite trace metrics required")
    confined = [not line["left_target"] for line in lines]
    inconclusive = sum(line.get("termination") == "classifier_stop_inside_target"
                       for line in lines)
    complete = [bool(line["transits"] >= requested_transits) for line in lines]
    mismatch = max(abs(line["iota_traced"] - line["iota_target"]) for line in lines)
    return dict(lines_confined=sum(confined), lines=len(lines), max_abs_iota_mismatch=mismatch,
                lines_completing_transits=sum(complete), requested_transits=requested_transits,
                classifier_stops_inside_target=inconclusive,
                all_confined_and_iota_matching=all(confined) and all(complete)
                and mismatch <= iota_tolerance, nestedness_tested=False,
                iota_tolerance=iota_tolerance, physical_admission=False)
