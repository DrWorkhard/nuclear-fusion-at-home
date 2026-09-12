"""Independent symmetric-VMEC field-line reconstruction using geometric arc length."""

from pathlib import Path

import netCDF4
import numpy as np


def _interpolate(grid, values, surface):
    if not grid[0] <= surface <= grid[-1]:
        raise ValueError("surface outside interpolation grid")
    upper = min(int(np.searchsorted(grid, surface, side="right")), len(grid) - 1)
    lower = upper - 1
    fraction = (surface - grid[lower]) / (grid[upper] - grid[lower])
    return values[lower] * (1 - fraction) + values[upper] * fraction


def _fourier(theta, phi, modes_m, modes_n, coefficients, *, sine=False):
    result = np.zeros_like(theta)
    for m, n, coefficient in zip(modes_m, modes_n, coefficients, strict=True):
        if coefficient != 0:
            phase = m * theta - n * phi
            result += coefficient * (np.sin(phase) if sine else np.cos(phase))
    return result


def trace_geometry(
    wout: Path, surface: float, nphi: int, nalpha: int, periods: int, *, alpha_offset: float = 0.0
):
    if nphi < 2 or nalpha < 1 or periods < 1:
        raise ValueError("invalid trace resolution")
    if not np.isfinite(alpha_offset):
        raise ValueError("finite alpha offset required")
    with netCDF4.Dataset(wout) as dataset:

        def read(name):
            value = np.ma.asarray(dataset[name][...], dtype=float).filled(np.nan)
            if not np.all(np.isfinite(value)):
                raise ValueError(f"nonfinite VMEC variable: {name}")
            return value

        if read("lasym__logical__").item() != 0:
            raise ValueError("only stellarator-symmetric wouts are supported")
        ns = int(read("ns").item())
        nfp = int(read("nfp").item())
        if ns < 3 or nfp < 1:
            raise ValueError("invalid radial resolution or field periods")
        full = np.linspace(0, 1, ns)
        half = (full[1:] + full[:-1]) / 2
        m, n = read("xm"), read("xn")
        mn, nn = read("xm_nyq"), read("xn_nyq")
        r = _interpolate(full, read("rmnc"), surface)
        z = _interpolate(full, read("zmns"), surface)
        lam = _interpolate(half, read("lmns")[1:], surface)
        b = _interpolate(half, read("bmnc")[1:], surface)
        iota = float(_interpolate(half, read("iotas")[1:], surface))
    phi = np.linspace(0, 2 * np.pi * periods / nfp, nphi)[:, None]
    alpha = np.linspace(0, 2 * np.pi, nalpha, endpoint=False)[None, :]
    if alpha_offset != 0:
        alpha = alpha + alpha_offset
    target = alpha + iota * phi
    theta = target.copy()
    for _ in range(50):
        residual = theta + _fourier(theta, phi, m, n, lam, sine=True) - target
        if np.max(np.abs(residual)) <= 1e-12:
            break
        derivative = 1 + _fourier(theta, phi, m, n, m * lam)
        if np.any(np.abs(derivative) < 1e-8):
            raise ValueError("singular coordinate mapping")
        theta -= np.clip(residual / derivative, -0.5, 0.5)
    residual = theta + _fourier(theta, phi, m, n, lam, sine=True) - target
    residual_max = float(np.max(np.abs(residual)))
    if not np.isfinite(residual_max) or residual_max > 1e-10:
        raise ValueError(f"coordinate inversion failed: {residual_max}")
    derivative_theta = 1 + _fourier(theta, phi, m, n, m * lam)
    if np.any(np.abs(derivative_theta) < 1e-8):
        raise ValueError("singular converged coordinate mapping")
    theta_prime = (iota - _fourier(theta, phi, m, n, -n * lam)) / derivative_theta
    radius = _fourier(theta, phi, m, n, r)
    r_prime = (
        _fourier(theta, phi, m, n, n * r, sine=True)
        + _fourier(theta, phi, m, n, -m * r, sine=True) * theta_prime
    )
    z_prime = _fourier(theta, phi, m, n, -n * z) + _fourier(theta, phi, m, n, m * z) * theta_prime
    speed = np.sqrt(radius**2 + r_prime**2 + z_prime**2)
    field = _fourier(theta, phi, mn, nn, b)
    if np.any(radius <= 0) or np.any(field <= 0) or not np.all(np.isfinite(speed)):
        raise ValueError("invalid reconstructed geometry or field")
    length = np.zeros_like(theta)
    length[1:] = np.cumsum((speed[:-1] + speed[1:]) * np.diff(phi, axis=0) / 2, axis=0)
    return {
        "B": field,
        "length": length,
        "theta": theta,
        "speed": speed,
        "phi": phi[:, 0],
        "alpha": alpha[0],
        "coordinate_residual_max": residual_max,
    }
