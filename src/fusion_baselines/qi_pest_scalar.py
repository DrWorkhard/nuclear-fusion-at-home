"""Separate radial interpolation/Fourier loops and scalar-Brent PEST field audit."""

import netCDF4
import numpy as np

from fusion_baselines.pest_root_audit import scalar_root


def sample(wout, surface, u, phi):
    u, phi = np.asarray(u), np.asarray(phi)
    if u.shape != phi.shape or u.size == 0:
        raise ValueError("matched nonempty scalar-audit grids required")
    with netCDF4.Dataset(wout) as ds:
        def read(key):
            value = np.ma.asarray(ds[key][...], dtype=float).filled(np.nan)
            if not np.isfinite(value).all():
                raise ValueError("nonfinite independent Wout data")
            return value

        ns, nfp = int(read("ns").item()), int(read("nfp").item())
        if ns < 3 or nfp < 1 or read("lasym__logical__").item() != 0:
            raise ValueError("valid symmetric scalar-audit input required")
        full = np.arange(ns) / (ns-1)
        half = (np.arange(ns-1) + .5) / (ns-1)

        def radial(key, half_mesh=True):
            radial_grid = half if half_mesh else full
            if not radial_grid[0] <= surface <= radial_grid[-1]:
                raise ValueError("independent radial range exceeded")
            index = min(int(np.searchsorted(radial_grid, surface, side="right")),
                        len(radial_grid)-1)
            weight = (surface-radial_grid[index-1])/(radial_grid[index]-radial_grid[index-1])
            rows = read(key)[1:] if half_mesh else read(key)
            return (1-weight)*rows[index-1] + weight*rows[index]

        m, n, mn, nn = (read(k) for k in ("xm", "xn", "xm_nyq", "xn_nyq"))
        lam, r, z = radial("lmns"), radial("rmnc", False), radial("zmns", False)
        roots = [scalar_root(float(uu), float(pp), m, n, lam)
                 for uu, pp in zip(u.ravel(), phi.ravel(), strict=True)]
        result = {k: np.array([v[k] for v in roots]).reshape(u.shape) for k in roots[0]}
        theta = result["theta"]
        radius, height, rt, rp, zt, zp = (np.zeros(u.shape) for _ in range(6))
        for a, b, rr, zz in zip(m, n, r, z, strict=True):
            phase = a*theta-b*phi
            cosine, sine = np.cos(phase), np.sin(phase)
            radius += rr*cosine
            height += zz*sine
            rt -= a*rr*sine
            rp += b*rr*sine
            zt += a*zz*cosine
            zp -= b*zz*cosine
        et = np.stack((rt*np.cos(phi), rt*np.sin(phi), zt), axis=-1)
        ep = np.stack((rp*np.cos(phi)-radius*np.sin(phi),
                       rp*np.sin(phi)+radius*np.cos(phi), zp), axis=-1)
        bmag = np.zeros(u.shape)
        for a, b, coefficient in zip(mn, nn, radial("bmnc"), strict=True):
            bmag += coefficient*np.cos(a*theta-b*phi)
        if not result["passed"].all():
            return result
        result.update(radius=radius, height=height, mod_b=bmag, et=et, ep=ep,
                      eu=et/result["denominator"][..., None],
                      ep_u=ep-et*(result["lp"]/result["denominator"])[..., None],
                      iota=np.array(radial("iotas")), volume=float(read("volume_p").item()))
        return result
