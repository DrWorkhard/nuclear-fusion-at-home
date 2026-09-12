"""Additive matrix-Fourier QI field reader; historical fixed-grid reader is untouched."""

import netCDF4
import numpy as np


def sample(wout, surface, resolution):
    if surface not in (0.25, 0.5, 0.75) or resolution not in (16, 32, 64, 128):
        raise ValueError("registered QI surfaces and grids required")
    with netCDF4.Dataset(wout) as ds:
        def read(key):
            value = np.ma.asarray(ds[key][...], dtype=float).filled(np.nan)
            if not np.isfinite(value).all():
                raise ValueError(f"nonfinite field coefficient: {key}")
            return value

        ns, nfp = int(read("ns").item()), int(read("nfp").item())
        if ns < 3 or nfp < 1 or read("lasym__logical__").item() != 0:
            raise ValueError("valid symmetric Wout required")
        full = np.linspace(0, 1, ns)
        half = (full[:-1] + full[1:]) / 2
        if not half[0] <= surface <= half[-1]:
            raise ValueError("interior half-mesh surface required")

        def radial(key, half_mesh=True):
            grid = half if half_mesh else full
            values = read(key)[1:] if half_mesh else read(key)
            if values.ndim == 1:
                return np.array(np.interp(surface, grid, values))
            return np.array([np.interp(surface, grid, v) for v in values.T])

        m, n, mn, nn = [read(k) for k in ("xm", "xn", "xm_nyq", "xn_nyq")]
        phi, theta = np.meshgrid(2 * np.pi * np.arange(resolution) / (resolution * nfp),
                                 2 * np.pi * np.arange(resolution) / resolution, indexing="ij")
        phase = m[:, None] * theta.ravel() - n[:, None] * phi.ravel()
        c, s = np.cos(phase), np.sin(phase)

        def project(coeff, basis=c):
            return (coeff @ basis).reshape(theta.shape)

        r, z, lam = radial("rmnc", False), radial("zmns", False), radial("lmns")
        radius, height = project(r), project(z, s)
        rt, rp, zt, zp = project(-m * r, s), project(n * r, s), project(m * z), project(-n * z)
        nyquist = np.cos(mn[:, None] * theta.ravel() - nn[:, None] * phi.ravel())
        arrays = {out: project(radial(key), nyquist) for out, key in (
            ("g", "gmnc"), ("bt", "bsupumnc"), ("bp", "bsupvmnc"), ("mod_b", "bmnc"))}
        arrays.update(theta=theta, phi=phi, radius=radius, height=height,
                      lt=project(m * lam), lp=project(-n * lam), iota=radial("iotas"),
                      psi=np.array(-float(read("phi")[-1]) / (2 * np.pi)),
                      et=np.stack((rt * np.cos(phi), rt * np.sin(phi), zt), axis=-1),
                      ep=np.stack((rp * np.cos(phi) - radius * np.sin(phi),
                                   rp * np.sin(phi) + radius * np.cos(phi), zp), axis=-1))
    return arrays


def relative_max(new, old):
    a, b = np.asarray(new), np.asarray(old)
    if a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("matched finite arrays required")
    denominator = float(np.max(abs(b)))
    if denominator == 0:
        raise ValueError("nonzero relative reference required")
    return float(np.max(abs(a - b)) / denominator)


def fidelity(new, old):
    # Cartesian components and R/Z/tangents use a single max-component scale.
    result = {key: relative_max(new[key], old[key]) for key in ("mod_b", "et", "ep")}
    result["rz"] = relative_max(np.stack((new["radius"], new["height"])),
                                np.stack((old["radius"], old["height"])))
    result["iota"] = float(abs(new["iota"] - old["iota"]))
    return result


def nested_errors(coarse, fine):
    result = {}
    for key, value in coarse.items():
        other = fine[key][::2, ::2] if value.ndim >= 2 else fine[key]
        if other.shape != value.shape or not np.isfinite(other).all():
            raise ValueError("matching nested grids required")
        result[key] = float(np.max(abs(other - value)) / max(1, float(np.max(abs(value)))))
    return result
