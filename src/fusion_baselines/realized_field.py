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
    def from_wout(cls, path):
        import netCDF4

        path = Path(path)
        with path.open("rb") as stream:
            sha256 = hashlib.file_digest(stream, "sha256").hexdigest()
        with netCDF4.Dataset(path) as data:
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
    return abs(turned) / (2 * np.pi), float((theta[-1] - theta[0]) / turned)


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
    """Trace lines from target surfaces; stop a line only when it leaves the target boundary."""
    from simsopt.field.tracing import LevelsetStoppingCriterion, compute_fieldlines
    from simsopt.geo import SurfaceClassifier

    need(0 < transits <= 2000 and 0 < tol < 1e-6, "bounded transits and tight tolerance")
    classifier = SurfaceClassifier(surface, h=0.02, p=2)
    starts = [float(target.rz(s, 0.0, 0.0)[0]) for s in s_values]
    tmax = 1.3 * transits * 2 * math.pi * max(starts)
    paths, hits = compute_fieldlines(field, starts, [0.0] * len(starts), tmax=tmax, tol=tol,
                                     phis=[0.0, math.pi / 2],
                                     stopping_criteria=[LevelsetStoppingCriterion(classifier.dist)])
    lines = []
    for s, path, hit in zip(s_values, paths, hits, strict=True):
        turns, iota = winding(path[:, 1:4], target)
        left = bool(len(hit) and hit[-1, 1] < 0)
        lines.append(dict(s=s, R0=float(path[0, 1]), transits=turns, left_target=left,
                          iota_traced=iota, iota_target=target.iota(s)))
    return lines, hits


def summarize(lines, iota_tolerance=0.02):
    confined = [not line["left_target"] for line in lines]
    mismatch = max(abs(abs(line["iota_traced"]) - abs(line["iota_target"])) for line in lines)
    return dict(lines_confined=sum(confined), lines=len(lines), max_abs_iota_mismatch=mismatch,
                nested_and_matching=all(confined) and mismatch <= iota_tolerance,
                iota_tolerance=iota_tolerance, physical_admission=False)
