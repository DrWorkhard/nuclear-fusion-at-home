"""Real Fourier projection onto explicitly stored VMEC mode pairs."""

import numpy as np


def mode_mask(size, m, n, nfp):
    m, n = np.asarray(m), np.asarray(n)
    if (
        type(size) is not int
        or size < 2
        or nfp < 1
        or m.shape != n.shape
        or m.ndim != 1
        or not np.isfinite(m).all()
        or not np.isfinite(n).all()
        or not np.array_equal(m, np.rint(m))
        or not np.array_equal(n / nfp, np.rint(n / nfp))
        or m.size == 0
        or np.max(abs(m)) >= size / 2
        or np.max(abs(n / nfp)) >= size / 2
    ):
        raise ValueError("resolved integer Fourier modes required")
    mask = np.zeros((size, size), dtype=bool)
    for poloidal, toroidal in zip(m.astype(int), (n / nfp).astype(int), strict=True):
        mask[-toroidal % size, poloidal % size] = True
        mask[toroidal % size, -poloidal % size] = True
    return mask


def project(values, mask):
    values, mask = np.asarray(values), np.asarray(mask)
    if (
        values.ndim < 2
        or mask.ndim != 2
        or mask.dtype != bool
        or values.shape[-2:] != mask.shape
        or mask.shape[0] != mask.shape[1]
        or not np.isfinite(values).all()
        or np.iscomplexobj(values)
    ):
        raise ValueError("finite real square fields and matching mode mask required")
    size = mask.shape[0]
    if not np.array_equal(mask, mask[np.ix_((-np.arange(size)) % size, (-np.arange(size)) % size)]):
        raise ValueError("conjugate-symmetric mode mask required")
    coefficients = np.fft.fft2(values, axes=(-2, -1)) / (size * size)
    projected = (np.fft.ifft2(coefficients * mask, axes=(-2, -1)) * (size * size)).real
    energy = np.mean(values**2, axis=(-2, -1))
    inside = np.sum(abs(coefficients * mask) ** 2, axis=(-2, -1))
    outside = np.sum(abs(coefficients * (~mask)) ** 2, axis=(-2, -1))
    parseval = abs(inside + outside - energy) / np.maximum(1e-300, energy)
    return (
        projected,
        coefficients,
        dict(energy=energy, inside=inside, outside=outside, parseval_error=parseval),
    )


def explicit_projection(coefficients, mask):
    """Independent trigonometric summation, with no inverse FFT."""
    coefficients = np.asarray(coefficients)
    size = mask.shape[0]
    if coefficients.shape[-2:] != mask.shape or not np.isfinite(coefficients).all():
        raise ValueError("finite matching Fourier coefficients required")
    angles = 2 * np.pi * np.arange(size) / size
    result = np.zeros(coefficients.shape)
    for i, j in np.argwhere(mask):
        ki, kj = (i if i <= size // 2 else i - size), (j if j <= size // 2 else j - size)
        phase = ki * angles[:, None] + kj * angles[None, :]
        c = coefficients[..., i, j, None, None]
        result += c.real * np.cos(phase) - c.imag * np.sin(phase)
    return result
