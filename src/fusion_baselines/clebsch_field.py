"""Bounded comparison of independent symmetric-VMEC field representations."""

from pathlib import Path

import netCDF4
import numpy as np

from fusion_baselines.vmec_trace import _fourier, _interpolate


def compare_fields(psi, g, bt, bp, lt, lp, iota, et, ep, mod_b):
    g, bt, bp, lt, lp, mod_b = [np.asarray(v, dtype=float) for v in (g, bt, bp, lt, lp, mod_b)]
    et, ep = np.asarray(et, dtype=float), np.asarray(ep, dtype=float)
    if (
        not np.isfinite(psi) or psi == 0 or not np.isfinite(iota)
        or g.size == 0 or any(v.shape != g.shape for v in (bt, bp, lt, lp, mod_b))
        or et.shape != ep.shape or et.shape != (*g.shape, 3)
        or any(not np.isfinite(v).all() for v in (g, bt, bp, lt, lp, mod_b, et, ep))
        or np.any(g == 0) or np.any(mod_b <= 0)
    ):
        raise ValueError("finite nonsingular field-coordinate arrays required")
    expected_p, expected_t = psi * (1 + lt), psi * (iota - lp)
    norm_p = float(np.max(abs(expected_p)))
    if norm_p == 0:
        raise ValueError("nonzero toroidal reference required")
    native = bt[..., None] * et + bp[..., None] * ep
    clebsch = (expected_t[..., None] * et + expected_p[..., None] * ep) / g[..., None]
    norm_b = float(np.max(np.linalg.norm(native, axis=-1)))
    if norm_b == 0 or not np.isfinite(clebsch).all():
        raise ValueError("nonzero finite reconstructed field required")
    errors = dict(
        toroidal=float(np.max(abs(g * bp - expected_p)) / norm_p),
        poloidal=float(np.max(abs(g * bt - expected_t)) /
                       max(abs(psi), float(np.max(abs(expected_t))))),
        cartesian=float(np.max(np.linalg.norm(native - clebsch, axis=-1)) / norm_b),
        magnitude=float(np.max(abs(np.linalg.norm(native, axis=-1) - mod_b)) / mod_b.max()),
        wrong_sign=float(np.max(abs(g * bp + expected_p)) / norm_p),
        missing_2pi=float(np.max(abs(g * bp - 2 * np.pi * expected_p)) / norm_p),
    )
    checks = {k: bool(np.isfinite(v) and (v > 0.1 if k in ("wrong_sign", "missing_2pi")
                                         else v <= 1e-3)) for k, v in errors.items()}
    return native, clebsch, errors, checks


def sample_coordinates(wout: Path, surface, resolution):
    if surface not in (0.25, 0.5, 0.75) or resolution not in (16, 32):
        raise ValueError("preregistered radii and grids required")
    with netCDF4.Dataset(wout) as dataset:
        def read(name):
            value = np.ma.asarray(dataset[name][...], dtype=float).filled(np.nan)
            if not np.isfinite(value).all():
                raise ValueError(f"nonfinite VMEC variable: {name}")
            return value

        if read("lasym__logical__").item() != 0:
            raise ValueError("stellarator-symmetric data required")
        ns, nfp = int(read("ns").item()), int(read("nfp").item())
        if ns < 3 or nfp < 1:
            raise ValueError("invalid VMEC dimensions")
        full = np.linspace(0, 1, ns)
        half = (full[1:] + full[:-1]) / 2
        m, n, mn, nn = [read(k) for k in ("xm", "xn", "xm_nyq", "xn_nyq")]
        r = _interpolate(full, read("rmnc"), surface)
        z = _interpolate(full, read("zmns"), surface)
        lam = _interpolate(half, read("lmns")[1:], surface)
        iota = float(_interpolate(half, read("iotas")[1:], surface))
        edge_flux = float(read("phi")[-1])
        coeffs = {k: _interpolate(half, read(k)[1:], surface)
                  for k in ("gmnc", "bsupumnc", "bsupvmnc", "bmnc")}
    phi, theta = np.meshgrid(2 * np.pi * np.arange(resolution) / (resolution * nfp),
                             2 * np.pi * np.arange(resolution) / resolution, indexing="ij")

    def f(coefficients, *, sine=False):
        return _fourier(theta, phi, m, n, coefficients, sine=sine)

    radius, rt, rp = f(r), f(-m * r, sine=True), f(n * r, sine=True)
    zt, zp = f(m * z), f(-n * z)
    et = np.stack((rt * np.cos(phi), rt * np.sin(phi), zt), axis=-1)
    ep = np.stack((rp * np.cos(phi) - radius * np.sin(phi),
                   rp * np.sin(phi) + radius * np.cos(phi), zp), axis=-1)
    nyquist = {k: _fourier(theta, phi, mn, nn, v) for k, v in coeffs.items()}
    arrays = dict(
        theta=theta, phi=phi, g=nyquist["gmnc"], bt=nyquist["bsupumnc"],
        bp=nyquist["bsupvmnc"], mod_b=nyquist["bmnc"], lt=f(m * lam), lp=f(-n * lam),
        et=et, ep=ep, psi=np.array(-edge_flux / (2 * np.pi)), iota=np.array(iota),
    )
    return arrays, dict(ns=ns, nfp=nfp, edge_flux=edge_flux, surface=surface, resolution=resolution)
