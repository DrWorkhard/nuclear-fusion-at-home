"""Source-separated, flux-normalized modular-coil construction for the step4A pilot.

No native SquaredFlux threshold/gradient is used.  Geometry remains a soft
construction penalty; neither this module nor a solver return admits a design.
All loop/surface/coil derivatives use normalized parameters in [0,1].
"""

import json
from pathlib import Path

import netCDF4
import numpy as np
from scipy.spatial import cKDTree

from fusion_baselines.provenance import sha256_file
from fusion_baselines.qi_field_grid import sample
from fusion_baselines.qi_resolution import boundary_errors, mode_map


def local_names(order):
    """Canonical local names, independent of native object numbering."""
    if type(order) is not int or order < 1:
        raise ValueError("positive integer Fourier order required")
    return [name for axis in "xyz" for name in (
        [f"{axis}c(0)"]
        + [f"{axis}{kind}({m})" for m in range(1, order + 1) for kind in "sc"]
    )]


def canonical_names(nbase, order):
    if type(nbase) is not int or nbase < 1:
        raise ValueError("positive integer base count required")
    return [f"coil[{i}]/{name}" for i in range(nbase) for name in local_names(order)]


def physical_rows(nbase, scale, nfp=2):
    """Right-row multiplication matrices: native rotation followed by flip."""
    if nfp != 2 or not np.isfinite(scale) or scale == 0:
        raise ValueError("nfp2 and finite nonzero current scale required")
    canonical_names(nbase, 1)
    rows = []
    for period in range(nfp):
        angle = 2 * np.pi * period / nfp
        c, s = np.cos(angle), np.sin(angle)
        rotation = np.array([[c, s, 0.0], [-s, c, 0.0], [0.0, 0.0, 1.0]])
        for flip in (False, True):
            matrix = rotation @ np.diag([1.0, -1.0, -1.0]) if flip else rotation
            for i in range(nbase):
                rows.append(dict(base_index=i, period=period, flip=flip,
                                 matrix=matrix.tolist(),
                                 current=float(1e5 * scale * (-1 if flip else 1))))
    return rows


def loop_geometry(data, count):
    """Exact Fourier phi=0 section; tangent is d(position)/dt, t=theta/(2pi)."""
    if type(count) is not int or count < 4:
        raise ValueError("at least four loop points required")
    theta = 2 * np.pi * np.arange(count) / count
    r, z, rt, zt = (np.zeros(count) for _ in range(4))
    for (m, _), value in mode_map(data["rbc"]).items():
        r += value * np.cos(m * theta)
        rt -= 2 * np.pi * m * value * np.sin(m * theta)
    for (m, _), value in mode_map(data["zbs"]).items():
        z += value * np.sin(m * theta)
        zt += 2 * np.pi * m * value * np.cos(m * theta)
    points = np.column_stack((r, np.zeros(count), z))
    tangents = np.column_stack((rt, np.zeros(count), zt))
    if not np.isfinite([points, tangents]).all() or np.any(r <= 0):
        raise ValueError("finite positive-R loop required")
    return points, tangents


def target_flux_sign(data, toroidal_components):
    """Stokes orientation: positive R-Z area has Cartesian normal -e_phi."""
    bphi = np.asarray(toroidal_components, dtype=float)
    if (not bphi.size or not np.isfinite(bphi).all() or np.any(bphi == 0)
            or not np.all(np.sign(bphi) == np.sign(bphi.flat[0]))):
        raise ValueError("common finite nonzero inner toroidal-field sign required")
    points, tangent = loop_geometry(data, 1024)
    area = 0.5 * np.mean(points[:, 0] * tangent[:, 2] - points[:, 2] * tangent[:, 0])
    if not np.isfinite(area) or area == 0:
        raise ValueError("nonzero oriented target section required")
    center = points.mean(axis=0)
    normal = np.cross(points - center, tangent)
    # Fan area is a signed parameterized surface, never an absolute Jacobian.
    if np.any(normal[:, 1] == 0) or not np.all(np.sign(normal[:, 1]) == -np.sign(area)):
        raise ValueError("target section fan Jacobian changes sign or degenerates")
    flux = -np.sign(area) * np.sign(bphi.flat[0]) * abs(float(data["phiedge"]))
    if not np.isfinite(flux) or flux == 0:
        raise ValueError("nonzero finite target toroidal flux required")
    return float(flux)


def load_target(wout, input_json, ninner):
    """Read the exact committed input and source-bound401 Wout; no solver work."""
    wout, input_json = Path(wout), Path(input_json)
    data = json.loads(input_json.read_text())
    if (data["nfp"] != 2 or data["mpol"] != 5 or data["ntor"] != 10
            or data["lfreeb"] or data.get("lasym", False)
            or data["pres_scale"] != 0 or data["curtor"] != 0
            or data["ns_array"][-1] != 401
            or not np.isclose(abs(data["phiedge"]), np.pi / 100, rtol=0, atol=1e-15)):
        raise ValueError("registered symmetric nfp2 vacuum401 target required")
    for key in ("rbc", "zbs"):
        modes = mode_map(data[key])
        if any(m < 0 or m >= 5 or abs(n) > 10 for m, n in modes):
            raise ValueError("input boundary mode outside registered truncation")
    with netCDF4.Dataset(wout) as ds:
        if not all(np.isfinite(np.ma.asarray(ds[key][...]).filled(np.nan)).all()
                   for key in ("rmnc", "zmns", "phi")):
            raise ValueError("nonfinite boundary or flux in Wout")
        if (int(ds["ns"][...]) != 401 or int(ds["nfp"][...]) != 2
                or int(ds["lasym__logical__"][...]) != 0
                or max(boundary_errors(ds, data).values()) > 1e-12
                or abs(float(ds["phi"][-1]) - data["phiedge"]) > 1e-14):
            raise ValueError("Wout/input boundary or physical identity mismatch")
    xyz, magnetic, bphi = [], [], []
    for s in (0.25, 0.5, 0.75):
        fields = sample(wout, s, ninner)
        phi, radius, height = (fields[k] for k in ("phi", "radius", "height"))
        points = np.stack((radius * np.cos(phi), radius * np.sin(phi), height), axis=-1)
        field = fields["bt"][..., None] * fields["et"] + fields["bp"][..., None] * fields["ep"]
        xyz.append(points.reshape(-1, 3))
        magnetic.append(field.reshape(-1, 3))
        bphi.append(field[0, :, 1])  # phi=0, same VMEC angular evaluation.
    xyz, magnetic = np.concatenate(xyz), np.concatenate(magnetic)
    if not np.isfinite([xyz, magnetic]).all():
        raise ValueError("nonfinite inner target")
    return dict(input=data, inner_points=xyz, inner_target=magnetic,
                target_flux=target_flux_sign(data, bphi),
                sources={"wout": dict(path=str(wout.resolve()), sha256=sha256_file(wout)),
                         "input": dict(path=str(input_json.resolve()),
                                       sha256=sha256_file(input_json))})


class CoupledCoils:
    """Canonical metre-valued Fourier variables with analytically eliminated current.

    Construction ``evaluate`` always renormalizes at the fixed256-point loop.
    ``diagnostics`` instead freezes the supplied physical scale and B2 denominator.
    Same-state ``arrays``/``snapshot`` reuse cached values and never call evaluate.
    Constructor performs one disclosed seed-loop A call to freeze orientation.
    """

    def __init__(self, wout, input_json, nbase, order, method, ncoil=128,
                 nphi=32, ntheta=32, ninner=16, offset=0):
        from simsopt.field import BiotSavart, Current, coils_via_symmetries
        from simsopt.geo import (
            CurveCurveDistance,
            CurveLength,
            CurveSurfaceDistance,
            LpCurveCurvature,
            create_equally_spaced_curves,
        )
        from simsopt.objectives import QuadraticPenalty

        self.names = canonical_names(nbase, order)
        if method not in ("N", "V"):
            raise ValueError("registered construction method N or V required")
        if (any(type(n) is not int or n < 4 for n in (ncoil, nphi, ntheta, ninner))
                or ncoil <= 2 * order or ninner not in (16, 32, 64, 128)
                or offset not in (0, 0.5)):
            raise ValueError("valid resolved periodic construction grids required")
        self.wout, self.input_json = Path(wout), Path(input_json)
        self.nbase, self.order, self.method = nbase, order, method
        self.ncoil, self.nphi, self.ntheta = ncoil, nphi, ntheta
        self.ninner, self.offset, self.nfp = ninner, offset, 2
        self.target = load_target(wout, input_json, ninner)
        self.input = self.target["input"]
        self.inner_points = np.asarray(self.target["inner_points"], dtype=float)
        self.inner_target = np.asarray(self.target["inner_target"], dtype=float)
        self.target_flux = float(self.target["target_flux"])
        self.B2_scale = float(np.mean(np.sum(self.inner_target**2, axis=1)))
        if not np.isfinite(self.B2_scale) or self.B2_scale <= 0:
            raise ValueError("positive finite target B2 scale required")
        self.surface = self.boundary_surface(nphi, ntheta, offset=offset)
        self.geometry_surface = self.boundary_surface(64, 32, full_torus=True, offset=0)
        self.boundary_points = self.surface.gamma().reshape(-1, 3).copy()
        normal = self.surface.normal().reshape(-1, 3).copy()
        norms = np.linalg.norm(normal, axis=1)
        if not np.isfinite(norms).all() or np.any(norms <= 0):
            raise ValueError("regular target surface required")
        self.boundary_normals, self.boundary_weights = normal / norms[:, None], norms / norms.sum()
        self.base_curves = create_equally_spaced_curves(
            nbase, 2, True, R0=1.0, R1=0.35, order=order, numquadpoints=ncoil)
        self.local_names = local_names(order)
        for curve in self.base_curves:
            if list(curve.local_full_dof_names) != self.local_names:
                raise ValueError("native Fourier local labels differ from explicit schema")
        self.seed_x = np.concatenate([c.local_full_x.copy() for c in self.base_curves])
        self.base_currents = [Current(1e5) for _ in range(nbase)]
        for current in self.base_currents:
            current.fix_all()
        self.coils = coils_via_symmetries(self.base_curves, self.base_currents, 2, True)
        self.curves = [c.curve for c in self.coils]
        self.field = BiotSavart(self.coils)
        self.inner_field = BiotSavart(self.coils)
        self.loop_field = BiotSavart(self.coils)
        self.length_terms = [CurveLength(c) for c in self.base_curves]
        self.curvature_terms = [LpCurveCurvature(c, 2, threshold=10) for c in self.base_curves]
        self.cc = CurveCurveDistance(self.curves, 0.06, num_basecurves=4*nbase)
        self.cs = CurveSurfaceDistance(self.curves, self.geometry_surface, 0.08)
        self.geometry = (sum(QuadraticPenalty(j, 3.5, "max") for j in self.length_terms)
                         + 1000*self.cc + 1000*self.cs + 1e-4*sum(self.curvature_terms))
        self._loop_points, self._loop_tangents = self.loop(256)
        self.loop_field.set_points(self._loop_points)
        initial_a = self.loop_field.A()
        self.seed_unit_flux = float(np.mean(np.sum(initial_a * self._loop_tangents, axis=1)))
        if not np.isfinite(self.seed_unit_flux) or abs(self.seed_unit_flux) <= 1e-12:
            raise ValueError("initial unit-current flux degenerate")
        self.initialization_work = dict(seed_A_calls=1, seed_A_points=256)
        self._cache = None

    @property
    def x(self):
        return np.concatenate([c.local_full_x.copy() for c in self.base_curves])

    @x.setter
    def x(self, value):
        x = np.asarray(value, dtype=float)
        if x.shape != self.seed_x.shape or not np.isfinite(x).all():
            raise ValueError("finite canonical Fourier vector required")
        size = len(self.local_names)
        for i, curve in enumerate(self.base_curves):
            if (list(curve.local_dof_names) != self.local_names
                    or list(curve.local_full_dof_names) != self.local_names):
                raise ValueError("native curve labels/free masks changed")
            curve.local_full_x = x[i*size:(i+1)*size].copy()
        self._cache = None

    def boundary_surface(self, nphi=None, ntheta=None, *, full_torus=False, offset=0):
        """Fresh untruncated fixed target; normalized full-toroidal phi coordinates."""
        from simsopt.geo import SurfaceRZFourier

        nphi, ntheta = nphi or self.nphi, ntheta or self.ntheta
        if (any(type(n) is not int or n < 4 for n in (nphi, ntheta))
                or offset not in (0, 0.5) or type(full_torus) is not bool):
            raise ValueError("valid target surface grid required")
        surface = SurfaceRZFourier(
            nfp=2, stellsym=True, mpol=self.input["mpol"]-1, ntor=self.input["ntor"],
            quadpoints_phi=(np.arange(nphi)+offset)/(nphi*(1 if full_torus else 2)),
            quadpoints_theta=(np.arange(ntheta)+offset)/ntheta)
        surface.local_full_x = np.zeros_like(surface.local_full_x)
        for key, setter in (("rbc", surface.set_rc), ("zbs", surface.set_zs)):
            for (m, n), value in mode_map(self.input[key]).items():
                if value != 0:
                    setter(m, n, value)
        surface.local_full_x = surface.get_dofs()
        surface.fix_all()
        return surface

    def loop(self, count=256):
        return loop_geometry(self.input, count)

    def _canonical_gradient(self, derivative):
        rows = []
        for curve in self.base_curves:
            labels = list(curve.local_dof_names)
            values = np.asarray(derivative(curve), dtype=float)
            if len(set(labels)) != len(self.local_names) or set(labels) != set(self.local_names):
                raise ValueError("nonbijective native gradient names")
            rows.append(values[[labels.index(name) for name in self.local_names]])
        result = np.concatenate(rows)
        if result.shape != self.seed_x.shape or not np.isfinite(result).all():
            raise ValueError("nonfinite or incompatible canonical gradient")
        return result

    def _state(self, x, scale=None, B2_scale=None):
        """Value-only state cache: no derivative requests or objective recursion."""
        x = np.asarray(x, dtype=float)
        b2 = self.B2_scale if B2_scale is None else float(B2_scale)
        if not np.isfinite(b2) or b2 <= 0:
            raise ValueError("positive frozen B2 scale required")
        frozen = None if scale is None else float(scale)
        if frozen is not None and (not np.isfinite(frozen) or frozen == 0):
            raise ValueError("finite nonzero frozen physical scale required")
        key = (x.tobytes(), frozen, b2)
        if (self._cache is not None and self._cache["key"] == key
                and np.array_equal(self.x, x)):
            return self._cache
        self.x = x
        coil_positions = np.array([c.gamma().copy() for c in self.curves])
        coil_tangents = np.array([c.gammadash().copy() for c in self.curves])
        if (not np.isfinite([coil_positions, coil_tangents]).all()
                or np.any(np.linalg.norm(coil_tangents, axis=2) <= 0)):
            raise ValueError("nonfinite or stationary filament")
        for points in coil_positions[:self.nbase]:
            pad = 128 * np.finfo(float).eps * max(1.0, float(np.max(abs(points))))
            if np.any(cKDTree(points).query(points, k=2, workers=1)[0][:, 1] <= pad):
                raise ValueError("detected repeated point/self-intersection on filament")
        self.field.set_points(self.boundary_points)
        self.inner_field.set_points(self.inner_points)
        self.loop_field.set_points(self._loop_points)
        bu, biu, au = self.field.B().copy(), self.inner_field.B().copy(), self.loop_field.A().copy()
        unit_flux = float(np.mean(np.sum(au*self._loop_tangents, axis=1)))
        if (not np.isfinite(unit_flux) or abs(unit_flux) <= 1e-12
                or np.sign(unit_flux) != np.sign(self.seed_unit_flux)):
            raise ValueError("unit-current flux invalid or orientation changed from start")
        a = self.target_flux / unit_flux if frozen is None else frozen
        b, bi = a*bu, a*biu
        bn = np.sum(b*self.boundary_normals, axis=1)
        bnorm = np.linalg.norm(b, axis=1)
        if not np.isfinite([bu, b]).all() or not np.isfinite(bi).all() or np.any(bnorm <= 0):
            raise ValueError("nonfinite or zero field at diagnostic points")
        jn = 0.5*float(np.sum(self.boundary_weights*bn**2))/b2
        jv = 0.5*float(np.mean(np.sum((bi-self.inner_target)**2, axis=1)))/b2
        geometry = float(self.geometry.J())
        kappa = [float(np.max(c.kappa())) for c in self.base_curves]
        lengths = [float(j.J()) for j in self.length_terms]
        metrics = dict(
            JN=jn, JV=jv, scale=float(a), B2_scale=b2, unit_flux=unit_flux,
            target_flux=self.target_flux, flux=float(a*unit_flux), current=float(a*1e5),
            normal_rms=float(np.sqrt(np.sum(self.boundary_weights*(bn/bnorm)**2))),
            normal_max=float(np.max(abs(bn)/bnorm)), vector_rms=float(np.sqrt(2*jv)),
            boundary_B_rms=float(np.sqrt(np.sum(self.boundary_weights*bnorm**2))),
            lengths=lengths, kappa_max=kappa,
            coil_distance=float(self.cc.shortest_distance()),
            surface_distance=float(self.cs.shortest_distance()),
            geometry_penalty=geometry, J=float(jn+(0.05*jv if self.method == "V" else 0)+geometry),
            frozen_scale=frozen is not None,
        )
        numeric = [v for v in metrics.values() if not isinstance(v, (list, bool))]
        if not np.isfinite(numeric+lengths+kappa).all():
            raise ValueError("nonfinite objective or geometry metrics")
        arrays = dict(boundary_points=self.boundary_points.copy(),
                      boundary_normals=self.boundary_normals.copy(),
                      boundary_weights=self.boundary_weights.copy(), boundary_B=b,
                      inner_points=self.inner_points.copy(), inner_target=self.inner_target.copy(),
                      inner_B=bi, loop_points=self._loop_points.copy(),
                      loop_tangents=self._loop_tangents.copy(), loop_A=a*au,
                      coil_positions=coil_positions, coil_tangents=coil_tangents,
                      coil_currents=np.array([c.current.get_value()*a for c in self.coils]))
        self._cache = dict(key=key, x=x.copy(), metrics=metrics, arrays=arrays, bu=bu, biu=biu)
        return self._cache

    def evaluate(self, x):
        """One explicitly requested construction value/gradient bundle."""
        state = self._state(x)
        metrics, arrays = state["metrics"], state["arrays"]
        a, phi, b2 = (metrics[k] for k in ("scale", "unit_flux", "B2_scale"))
        bn = np.sum(arrays["boundary_B"]*self.boundary_normals, axis=1)
        vb = (self.boundary_weights*bn/b2)[:, None]*self.boundary_normals
        vi = (arrays["inner_B"]-self.inner_target)/(len(self.inner_points)*b2)
        if self.method == "N":
            vi = np.zeros_like(vi)
        else:
            vi *= 0.05
        contraction = float(np.sum(vb*state["bu"])+np.sum(vi*state["biu"]))
        gradient = (self.field.B_vjp(a*vb) + self.inner_field.B_vjp(a*vi)
                    - (a*contraction/phi)*self.loop_field.A_vjp(
                        self._loop_tangents/len(self._loop_tangents))
                    + self.geometry.dJ(partials=True))
        return metrics["J"], self._canonical_gradient(gradient), dict(metrics)

    def diagnostics(self, x, scale, B2_scale):
        """Value-only diagnostics at an explicitly frozen physical normalization."""
        return dict(self._state(x, scale, B2_scale)["metrics"])

    def arrays(self, x, scale=None, B2_scale=None):
        """Copied value arrays; cached same-state access has no new native work."""
        return {k: v.copy() for k, v in self._state(x, scale, B2_scale)["arrays"].items()}

    def snapshot(self, x, scale=None, B2_scale=None):
        """Named SI geometry and explicit actual current for every physical copy."""
        state = self._state(x, scale, B2_scale)
        metrics = state["metrics"]
        return dict(schema_version=1, nfp=2, nbase=self.nbase, order=self.order,
                    names=self.names.copy(), base_coefficients=state["x"].reshape(
                        self.nbase, 3, 2*self.order+1).tolist(),
                    physical=physical_rows(self.nbase, metrics["scale"]),
                    scale=metrics["scale"], B2_scale=metrics["B2_scale"],
                    unit_flux=metrics["unit_flux"], target_flux=self.target_flux,
                    seed_unit_flux=self.seed_unit_flux, method=self.method,
                    sources=self.target.get("sources", {}),
                    construction=dict(ncoil=self.ncoil, nphi=self.nphi, ntheta=self.ntheta,
                                      ninner=self.ninner, offset=self.offset, nloop=256),
                    initialization_work=dict(self.initialization_work))
