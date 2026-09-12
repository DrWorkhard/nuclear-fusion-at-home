"""Additive Wout field evaluation at arbitrary VMEC or straight-field coordinates."""

import netCDF4
import numpy as np

from fusion_baselines.pest_coordinates import (
    angles,
    coefficients,
    invert_theta,
    transform_tangents,
)


def read_coefficients(wout, surface):
    if surface not in (.25, .5, .75):
        raise ValueError("registered surface required")
    with netCDF4.Dataset(wout) as ds:
        def read(key):
            value = np.ma.asarray(ds[key][...], dtype=float).filled(np.nan)
            if not np.isfinite(value).all():
                raise ValueError(f"nonfinite coefficient {key}")
            return value

        ns, nfp = read("ns").item(), read("nfp").item()
        if (ns != int(ns) or nfp != int(nfp) or ns < 3 or nfp < 1
                or read("lasym__logical__").item() != 0):
            raise ValueError("symmetric Wout with valid dimensions required")
        full = np.linspace(0, 1, int(ns))
        half = (full[:-1] + full[1:]) / 2
        if not half[0] <= surface <= half[-1]:
            raise ValueError("interior half-grid surface required")
        m, n, mn, nn = (read(k) for k in ("xm", "xn", "xm_nyq", "xn_nyq"))
        for a, b in ((m, n), (mn, nn)):
            coefficients(a, b / nfp, np.zeros_like(a))

        def radial(key, size=None, half_mesh=True):
            grid = half if half_mesh else full
            values = read(key)[1:] if half_mesh else read(key)
            expected = (len(grid),) if size is None else (len(grid), size)
            if values.shape != expected:
                raise ValueError(f"radial/mode shape mismatch for {key}")
            if size is None:
                return np.array(np.interp(surface, grid, values))
            return np.array([np.interp(surface, grid, v) for v in values.T])

        result = dict(m=m, n=n, mn=mn, nn=nn, ns=int(ns), nfp=int(nfp), surface=surface,
                      r=radial("rmnc", len(m), False), z=radial("zmns", len(m), False),
                      lam=radial("lmns", len(m)), iota=radial("iotas"),
                      psi=np.array(-read("phi")[-1] / (2*np.pi)),
                      volume=float(read("volume_p").item()))
        for out, key in (("g", "gmnc"), ("bt", "bsupumnc"), ("bp", "bsupvmnc"),
                         ("mod_b", "bmnc")):
            result[out] = radial(key, len(mn))
        return result


def evaluate(c, theta, phi):
    theta, phi = angles(theta, phi)
    m, n, r, z, lam = (c[k] for k in ("m", "n", "r", "z", "lam"))
    phase = m[:, None]*theta.ravel() - n[:, None]*phi.ravel()
    cosine, sine = np.cos(phase), np.sin(phase)

    def project(coeff, basis=cosine):
        return (coeff @ basis).reshape(theta.shape)

    radius, height = project(r), project(z, sine)
    rt, rp = project(-m*r, sine), project(n*r, sine)
    zt, zp = project(m*z), project(-n*z)
    nyquist = np.cos(c["mn"][:, None]*theta.ravel() - c["nn"][:, None]*phi.ravel())
    result = {k: project(c[k], nyquist) for k in ("g", "bt", "bp", "mod_b")}
    result.update(theta=theta, phi=phi, radius=radius, height=height,
                  lam=project(lam, sine), lt=project(m*lam), lp=project(-n*lam),
                  psi=c["psi"], iota=c["iota"],
                  et=np.stack((rt*np.cos(phi), rt*np.sin(phi), zt), axis=-1),
                  ep=np.stack((rp*np.cos(phi)-radius*np.sin(phi),
                               rp*np.sin(phi)+radius*np.cos(phi), zp), axis=-1))
    if not all(np.isfinite(v).all() for v in result.values()):
        raise ValueError("nonfinite reconstructed field")
    return result


def grid(nfp, resolution):
    if resolution not in (32, 64, 128) or nfp < 1 or int(nfp) != nfp:
        raise ValueError("registered grid and positive NFP required")
    phi, u = np.meshgrid(2*np.pi*np.arange(resolution)/(resolution*nfp),
                         2*np.pi*np.arange(resolution)/resolution, indexing="ij")
    return u, phi


def sample(c, resolution):
    u, phi = grid(c["nfp"], resolution)
    inversion = invert_theta(u, phi, c["m"], c["n"], c["lam"])
    if not inversion["passed"].all():
        return inversion, None
    fields = evaluate(c, inversion["theta"], phi)
    fields["eu"], fields["ep_u"] = transform_tangents(
        fields["et"], fields["ep"], fields["lt"], fields["lp"])
    return inversion, fields
